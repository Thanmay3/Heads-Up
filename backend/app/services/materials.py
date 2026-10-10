"""Material ingestion: validation, dedup, storage, extraction, traceability.

Synchronous by design for Stage 2: the upload request settles the material
into READY or FAILED before responding. FAILED rows are kept (with
error_message) so the student sees exactly which file failed and why.
"""

import hashlib
import re
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.extractors import (
    ExtractionError,
    RawSegment,
    extract_notes,
    extract_raw,
    normalize_segments,
)
from app.models import (
    LectureMaterial,
    MaterialFileType,
    MaterialKind,
    MaterialSegment,
    MaterialStatus,
)
from app.services.errors import (
    ConflictError,
    MaterialTooLargeError,
    MaterialValidationError,
    NotFoundError,
)
from app.services.lectures import get_lecture

_EXTENSION_TO_TYPE: dict[str, MaterialFileType] = {
    ".pdf": MaterialFileType.PDF,
    ".pptx": MaterialFileType.PPTX,
    ".ppt": MaterialFileType.PPT,
    ".txt": MaterialFileType.TXT,
}

_FILENAME_ALLOWED_RE = re.compile(r"[^A-Za-z0-9._ -]")
_MAX_FILENAME_LENGTH = 255


def _sanitize_filename(name: str) -> str:
    """Reduce an uploaded filename to a safe basename."""
    base = name.replace("\\", "/").split("/")[-1]
    base = _FILENAME_ALLOWED_RE.sub("_", base).strip(". ")
    if not base:
        base = "material"
    return base[:_MAX_FILENAME_LENGTH]


def _detect_file_type(filename: str) -> MaterialFileType:
    suffix = Path(filename).suffix.lower()
    file_type = _EXTENSION_TO_TYPE.get(suffix)
    if file_type is None:
        allowed = ", ".join(sorted(_EXTENSION_TO_TYPE))
        raise MaterialValidationError(
            f"Unsupported file type '{suffix or filename}'. Allowed: {allowed}"
        )
    return file_type


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_material(db: Session, material_id: int) -> LectureMaterial:
    material = db.get(LectureMaterial, material_id)
    if material is None:
        raise NotFoundError(f"Material {material_id} not found")
    return material


def _ensure_no_duplicate(db: Session, lecture_id: int, content_hash: str) -> None:
    existing = db.scalar(
        select(LectureMaterial.id).where(
            LectureMaterial.lecture_id == lecture_id,
            LectureMaterial.content_hash == content_hash,
        )
    )
    if existing is not None:
        raise ConflictError(
            "This material is already attached to this lecture (identical "
            "content was uploaded before)"
        )


def _store_segments(db: Session, material: LectureMaterial, raw: list[RawSegment]) -> None:
    normalized = normalize_segments(raw)
    for position, segment in enumerate(normalized):
        db.add(
            MaterialSegment(
                material_id=material.id,
                position=position,
                page_number=segment.page_number,
                text=segment.text,
            )
        )
    material.status = MaterialStatus.READY


def _fail_material(material: LectureMaterial, message: str) -> None:
    material.status = MaterialStatus.FAILED
    material.error_message = message


def add_file_material(db: Session, lecture_id: int, upload: UploadFile) -> LectureMaterial:
    get_lecture(db, lecture_id)
    settings = get_settings()

    original_name = upload.filename or "upload"
    # Sync route: read the underlying SpooledTemporaryFile directly (capped at
    # limit+1 so oversized uploads never buffer fully).
    payload = upload.file.read(settings.max_material_bytes + 1)

    if len(payload) == 0:
        raise MaterialValidationError("The uploaded file is empty")
    if len(payload) > settings.max_material_bytes:
        limit_mb = settings.max_material_bytes // (1024 * 1024)
        raise MaterialTooLargeError(
            f"File exceeds the {limit_mb} MB upload limit"
        )

    file_type = _detect_file_type(original_name)
    sanitized = _sanitize_filename(original_name)
    content_hash = _sha256(payload)
    _ensure_no_duplicate(db, lecture_id, content_hash)

    material = LectureMaterial(
        lecture_id=lecture_id,
        kind=MaterialKind.FILE,
        file_type=file_type,
        title=Path(sanitized).stem[:200] or sanitized[:200],
        original_filename=sanitized,
        content_hash=content_hash,
        file_size=len(payload),
        status=MaterialStatus.PROCESSING,
    )
    db.add(material)
    db.flush()

    # One storage folder per material, keyed by id: storage_path is stored as
    # a relative key ("<id>/<filename>") so the row survives restarts from a
    # different working directory.
    material_dir = Path(settings.materials_dir) / str(material.id)
    try:
        material_dir.mkdir(parents=True, exist_ok=True)
        (material_dir / sanitized).write_bytes(payload)
        material.storage_path = f"{material.id}/{sanitized}"
    except OSError as exc:
        _fail_material(material, f"Could not store the uploaded file ({exc})")
        db.commit()
        db.refresh(material)
        return material

    try:
        _store_segments(db, material, extract_raw(file_type, payload))
    except ExtractionError as exc:
        _fail_material(material, str(exc))

    try:
        db.commit()
    except IntegrityError as exc:
        # Backstop for the concurrent-upload race; the pre-check already
        # catches the common case.
        db.rollback()
        raise ConflictError(
            "This material is already attached to this lecture (identical "
            "content was uploaded before)"
        ) from exc
    db.refresh(material)
    return material


def add_notes_material(db: Session, lecture_id: int, title: str, content: str) -> LectureMaterial:
    get_lecture(db, lecture_id)

    payload = content.strip().encode("utf-8")
    if not payload:
        raise MaterialValidationError("Notes are empty - type some content first")
    content_hash = _sha256(payload)
    _ensure_no_duplicate(db, lecture_id, content_hash)

    material = LectureMaterial(
        lecture_id=lecture_id,
        kind=MaterialKind.NOTES,
        file_type=MaterialFileType.NOTES,
        title=title,
        content_hash=content_hash,
        file_size=len(payload),
        status=MaterialStatus.PROCESSING,
    )
    db.add(material)
    db.flush()

    try:
        _store_segments(db, material, extract_notes(content))
    except ExtractionError as exc:
        _fail_material(material, str(exc))

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "These notes are already attached to this lecture (identical "
            "content was saved before)"
        ) from exc
    db.refresh(material)
    return material


def list_materials(db: Session, lecture_id: int) -> list[LectureMaterial]:
    get_lecture(db, lecture_id)
    return list(
        db.scalars(
            select(LectureMaterial)
            .where(LectureMaterial.lecture_id == lecture_id)
            .options(selectinload(LectureMaterial.segments))
            .order_by(LectureMaterial.id.asc())
        )
    )


def get_material_segments(db: Session, material_id: int) -> list[MaterialSegment]:
    get_material(db, material_id)
    return list(
        db.scalars(
            select(MaterialSegment)
            .where(MaterialSegment.material_id == material_id)
            .order_by(MaterialSegment.position.asc())
        )
    )


def delete_material(db: Session, material_id: int) -> None:
    material = get_material(db, material_id)
    storage_key = material.storage_path

    db.delete(material)
    db.commit()

    # File cleanup only after the commit succeeded, so a rollback can never
    # leave a row pointing at a deleted file.
    if storage_key:
        path = Path(get_settings().materials_dir) / storage_key
        try:
            path.unlink(missing_ok=True)
            path.parent.rmdir()
        except OSError:
            # Orphan files are harmless; ingestion must not fail over cleanup.
            pass
