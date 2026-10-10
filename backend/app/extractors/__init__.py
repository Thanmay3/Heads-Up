"""Format-specific text extraction for lecture materials.

Stage 2 boundary: raw payload -> normalized, source-aware segments. No
concept extraction happens here (that is Stage 3).
"""

from app.extractors.base import ExtractionError, RawSegment
from app.extractors.normalize import normalize_segments
from app.extractors.notes import extract_notes
from app.extractors.pdf import extract_pdf
from app.extractors.pptx import extract_pptx
from app.extractors.txt import extract_txt
from app.models.material import MaterialFileType

_EXTRACTORS = {
    MaterialFileType.PDF: extract_pdf,
    MaterialFileType.PPTX: extract_pptx,
    MaterialFileType.PPT: extract_pptx,
    MaterialFileType.TXT: extract_txt,
}


def extract_raw(file_type: MaterialFileType, payload: bytes) -> list[RawSegment]:
    """Extract raw, per-page segments from a file payload.

    Raises ExtractionError when the format is not supported or the payload is
    unreadable/empty. Returns a non-empty list otherwise.
    """
    extractor = _EXTRACTORS.get(file_type)
    if extractor is None:
        raise ExtractionError(f"No extractor available for {file_type.value} files")
    return extractor(payload)


__all__ = [
    "ExtractionError",
    "RawSegment",
    "extract_notes",
    "extract_raw",
    "normalize_segments",
]
