import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.lecture import Lecture


class MaterialStatus(enum.StrEnum):
    """Processing lifecycle of an uploaded material.

    UPLOADED/PROCESSING are transient (Stage 2 extracts synchronously); a
    material settles in READY or FAILED. FAILED keeps the row so the student
    can see exactly which file failed and why.
    """

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class MaterialKind(enum.StrEnum):
    FILE = "file"
    NOTES = "notes"


class MaterialFileType(enum.StrEnum):
    PDF = "pdf"
    PPTX = "pptx"
    PPT = "ppt"
    TXT = "txt"
    NOTES = "notes"


class LectureMaterial(TimestampMixin, Base):
    """A piece of material attached to one lecture (file upload or typed notes).

    content_hash (SHA-256 of the raw payload) powers duplicate detection within
    a lecture; it is unique per lecture, not globally -- the same deck can
    legitimately belong to two different lectures of different courses.
    """

    __tablename__ = "lecture_materials"
    __table_args__ = (
        UniqueConstraint("lecture_id", "content_hash", name="uq_materials_lecture_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lecture_id: Mapped[int] = mapped_column(
        ForeignKey("lectures.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[MaterialKind] = mapped_column(
        SAEnum(MaterialKind, name="material_kind", native_enum=False, length=8), nullable=False
    )
    file_type: Mapped[MaterialFileType] = mapped_column(
        SAEnum(MaterialFileType, name="material_file_type", native_enum=False, length=8),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[MaterialStatus] = mapped_column(
        SAEnum(MaterialStatus, name="material_status", native_enum=False, length=16),
        default=MaterialStatus.UPLOADED,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    lecture: Mapped["Lecture"] = relationship(back_populates="materials")
    segments: Mapped[list["MaterialSegment"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
        order_by="MaterialSegment.position",
    )

    @property
    def segment_count(self) -> int:
        return len(self.segments)


class MaterialSegment(Base):
    """One source-aware chunk of extracted text.

    This is the traceability unit for later stages: when the bridge engine
    claims a concept is required, it can cite the material and page/slide the
    claim rests on. Segments are fully derived from the material payload and
    rebuildable, so they carry no timestamps of their own.
    """

    __tablename__ = "material_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(
        ForeignKey("lecture_materials.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(nullable=False)
    page_number: Mapped[int | None] = mapped_column(nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    material: Mapped[LectureMaterial] = relationship(back_populates="segments")
