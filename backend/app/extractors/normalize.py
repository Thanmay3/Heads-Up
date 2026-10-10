"""Conservative normalization of extracted segments.

Goal: remove artifacts that would pollute later concept extraction
(repeated headers/footers, page-number lines, whitespace damage, repeated
junk lines) while never rewriting or reordering real content.
"""

import math
import re
from collections import Counter

from app.extractors.base import RawSegment

# A standalone page number: "12", "3/41", "Page 7", "Page 7 of 41".
_PAGE_NUMBER_RE = re.compile(r"^(?:page\s+\d+(?:\s+of\s+\d+)?|\d{1,4})$", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")

_MARGIN_LINES = 2
_MIN_SEGMENTS_FOR_MARGIN_DETECTION = 3
_MIN_LINE_RUN_TO_COLLAPSE = 3
_MARGIN_REPEAT_THRESHOLD = 0.6


def _clean_line(line: str) -> str:
    return _WHITESPACE_RE.sub(" ", line).strip()


def _collapse_repeated_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        j = i
        while j < len(lines) and lines[j] == lines[i]:
            j += 1
        if j - i >= _MIN_LINE_RUN_TO_COLLAPSE:
            out.append(lines[i])
        else:
            out.extend(lines[i:j])
        i = j
    return out


def _clean_segment(segment: RawSegment) -> RawSegment:
    lines = [_clean_line(line) for line in segment.text.splitlines()]
    lines = [line for line in lines if line and not _PAGE_NUMBER_RE.match(line)]
    lines = _collapse_repeated_lines(lines)
    return RawSegment(page_number=segment.page_number, text="\n".join(lines))


def _repeated_margin_strings(segments: list[RawSegment]) -> set[str]:
    """Strings that appear in the top/bottom margin of most segments.

    Detected on casefolded, stripped lines and only within the first/last
    _MARGIN_LINES positions, so mid-content lines are never candidates.
    """
    counts: Counter[str] = Counter()
    for segment in segments:
        lines = segment.text.splitlines()
        tail = lines[-_MARGIN_LINES:] if len(lines) > _MARGIN_LINES else []
        margin = lines[:_MARGIN_LINES] + tail
        for key in {line.casefold() for line in margin if line.strip()}:
            counts[key] += 1

    threshold = math.ceil(_MARGIN_REPEAT_THRESHOLD * len(segments))
    return {key for key, count in counts.items() if count >= threshold}


def _strip_repeated_margins(segments: list[RawSegment]) -> list[RawSegment]:
    if len(segments) < _MIN_SEGMENTS_FOR_MARGIN_DETECTION:
        return segments
    repeated = _repeated_margin_strings(segments)
    if not repeated:
        return segments

    out: list[RawSegment] = []
    for segment in segments:
        lines = segment.text.splitlines()
        kept = [
            line
            for index, line in enumerate(lines)
            if (index >= _MARGIN_LINES and index < len(lines) - _MARGIN_LINES)
            or line.casefold() not in repeated
        ]
        out.append(RawSegment(page_number=segment.page_number, text="\n".join(kept)))
    return out


def _has_content(text: str) -> bool:
    return any(char.isalnum() for char in text)


def normalize_segments(segments: list[RawSegment]) -> list[RawSegment]:
    cleaned = [_clean_segment(segment) for segment in segments]
    stripped = _strip_repeated_margins([seg for seg in cleaned if seg.text])
    return [seg for seg in stripped if _has_content(seg.text)]
