"""Plain text extraction with encoding fallbacks."""

from app.extractors.base import ExtractionError, RawSegment


def extract_txt(payload: bytes) -> list[RawSegment]:
    if b"\x00" in payload:
        raise ExtractionError(
            "This file looks binary, not plain text - upload PDF/PPTX for "
            "documents like that"
        )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        text = payload.decode("latin-1")

    text = text.strip()
    if not text:
        raise ExtractionError("This text file is empty")
    return [RawSegment(page_number=None, text=text)]
