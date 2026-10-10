"""PDF text extraction via pypdf."""

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.extractors.base import ExtractionError, RawSegment


def extract_pdf(payload: bytes) -> list[RawSegment]:
    try:
        reader = PdfReader(io.BytesIO(payload))
    except (PdfReadError, ValueError, OSError) as exc:
        raise ExtractionError(f"This file is not a readable PDF ({exc})") from exc

    segments: list[RawSegment] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except (PdfReadError, ValueError) as exc:
            raise ExtractionError(f"Could not read page {index} of this PDF ({exc})") from exc
        if text.strip():
            segments.append(RawSegment(page_number=index, text=text))

    if not segments:
        raise ExtractionError(
            "No text could be extracted from this PDF - it is probably scanned "
            "images rather than text"
        )
    return segments
