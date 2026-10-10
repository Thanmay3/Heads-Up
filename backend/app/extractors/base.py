"""Shared extraction primitives: the raw segment unit and the failure type."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RawSegment:
    """One page/slide/chunk of extracted text before normalization.

    page_number is the 1-based page or slide the text came from; None for
    formats without pagination (plain text, typed notes).
    """

    page_number: int | None
    text: str


class ExtractionError(Exception):
    """A material payload could not be turned into text.

    The message must be actionable for the student (shown in the UI), e.g.
    "This PDF has no extractable text - it is probably scanned images".
    """
