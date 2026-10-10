"""Typed notes passthrough - no file bytes, text comes straight from the form."""

from app.extractors.base import ExtractionError, RawSegment


def extract_notes(text: str) -> list[RawSegment]:
    stripped = text.strip()
    if not stripped:
        raise ExtractionError("Notes are empty - type some content first")
    return [RawSegment(page_number=None, text=stripped)]
