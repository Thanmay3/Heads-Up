from app.extractors import RawSegment, normalize_segments


def segs(*texts: str) -> list[RawSegment]:
    return [RawSegment(page_number=i, text=t) for i, t in enumerate(texts, start=1)]


def test_collapses_whitespace_runs():
    result = normalize_segments(segs("Spaced   out\ttext  here"))
    assert result[0].text == "Spaced out text here"


def test_removes_page_number_lines():
    result = normalize_segments(segs("Real content\n12\nPage 3 of 41\nStill real"))
    lines = result[0].text.splitlines()
    assert lines == ["Real content", "Still real"]


def test_keeps_non_pagenumber_numeric_lines():
    result = normalize_segments(segs("Chapter 3\n1984 was a book"))
    lines = result[0].text.splitlines()
    assert lines == ["Chapter 3", "1984 was a book"]


def test_collapses_repeated_junk_lines():
    result = normalize_segments(segs("Title\n- - -\n- - -\n- - -\nBody"))
    assert result[0].text == "Title\n- - -\nBody"


def test_keeps_two_identical_lines():
    result = normalize_segments(segs("Echo\nEcho\nDifferent"))
    assert result[0].text == "Echo\nEcho\nDifferent"


def test_strips_repeated_headers_and_footers():
    pages = [
        f"Computer Networks\n{body}\nProf. Smith"
        for body in ("Intro to DNS", "DNS records", "Resolution", "Caching", "Recap")
    ]
    result = normalize_segments(segs(*pages))
    assert all("Computer Networks" not in s.text for s in result)
    assert all("Prof. Smith" not in s.text for s in result)
    assert result[0].text == "Intro to DNS"


def test_header_on_too_few_pages_is_kept():
    pages = ["Running header\nBody one", "Running header\nBody two"]
    result = normalize_segments(segs(*pages))
    assert all("Running header" in s.text for s in result)


def test_header_matching_only_some_pages_is_kept():
    pages = ["Running header\nOne", "Running header\nTwo", "Three", "Four", "Five"]
    result = normalize_segments(segs(*pages))
    assert "Running header" in result[0].text


def test_header_detection_is_case_insensitive():
    pages = [
        f"CHAPTER 2\n{body}\nchapter 2" for body in ("Alpha", "Beta", "Gamma", "Delta")
    ]
    result = normalize_segments(segs(*pages))
    assert all("hapter" not in s.text for s in result)


def test_drops_segments_without_alphanumeric_content():
    result = normalize_segments(segs("--- *** ---", "Real text"))
    assert [s.text for s in result] == ["Real text"]


def test_preserves_page_numbers():
    result = normalize_segments(segs("One", "Two\n2"))
    assert [s.page_number for s in result] == [1, 2]
