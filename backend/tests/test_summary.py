from app.models import Lecture, LectureStatus
from app.services.summary import compute_summary


def lecture(order_index: int, status: LectureStatus, title: str | None = None) -> Lecture:
    """Transient Lecture (never persisted): the summary is a pure function."""
    return Lecture(
        id=order_index,
        course_id=1,
        order_index=order_index,
        title=title or f"Lecture {order_index}",
        status=status,
    )


def test_empty_course_has_no_position():
    summary = compute_summary([])
    assert summary.last_understood_lecture is None
    assert summary.upcoming_lecture is None
    assert summary.missed_lectures == []
    assert summary.unmarked_before_upcoming == []


def test_all_unmarked_course_has_no_position():
    lectures = [lecture(index, LectureStatus.UNMARKED) for index in (1, 2, 3)]
    summary = compute_summary(lectures)
    assert summary.last_understood_lecture is None
    assert summary.upcoming_lecture is None
    assert summary.missed_lectures == []
    assert summary.unmarked_before_upcoming == []


def test_single_gap_scenario():
    """L1 understood, L2 missed, L3 upcoming -- the core Stage 1 scenario.

    Concepts and dependencies are not modelled yet (Stages 3-5); at the
    lecture level the position is: knowledge complete up to L1, gap at L2,
    preparing for L3.
    """
    lectures = [
        lecture(1, LectureStatus.UNDERSTOOD, "Introduction"),
        lecture(2, LectureStatus.MISSED, "Congestion Control"),
        lecture(3, LectureStatus.UPCOMING, "Quality of Service"),
    ]
    summary = compute_summary(lectures)

    assert summary.last_understood_lecture.order_index == 1
    assert summary.upcoming_lecture.order_index == 3
    assert [missed.order_index for missed in summary.missed_lectures] == [2]
    assert summary.unmarked_before_upcoming == []


def test_multiple_missed_lectures_are_all_in_the_gap():
    lectures = [
        lecture(1, LectureStatus.UNDERSTOOD),
        lecture(2, LectureStatus.MISSED),
        lecture(3, LectureStatus.MISSED),
        lecture(4, LectureStatus.UPCOMING),
    ]
    summary = compute_summary(lectures)
    assert [missed.order_index for missed in summary.missed_lectures] == [2, 3]


def test_missed_after_upcoming_is_not_part_of_the_gap():
    """A MISSED lecture after the upcoming one is out of scope for this bridge."""
    lectures = [
        lecture(1, LectureStatus.UNDERSTOOD),
        lecture(2, LectureStatus.MISSED),
        lecture(3, LectureStatus.UPCOMING),
        lecture(4, LectureStatus.MISSED),
    ]
    summary = compute_summary(lectures)
    assert [missed.order_index for missed in summary.missed_lectures] == [2]


def test_without_upcoming_all_missed_lectures_are_reported():
    lectures = [
        lecture(1, LectureStatus.UNDERSTOOD),
        lecture(2, LectureStatus.MISSED),
        lecture(3, LectureStatus.MISSED),
    ]
    summary = compute_summary(lectures)
    assert summary.upcoming_lecture is None
    assert [missed.order_index for missed in summary.missed_lectures] == [2, 3]


def test_without_upcoming_unmarked_lectures_are_not_nagged_about():
    lectures = [
        lecture(1, LectureStatus.UNDERSTOOD),
        lecture(2, LectureStatus.UNMARKED),
    ]
    summary = compute_summary(lectures)
    assert summary.unmarked_before_upcoming == []


def test_unmarked_before_upcoming_is_surfaced():
    """An unmarked lecture must never be silently treated as known."""
    lectures = [
        lecture(1, LectureStatus.UNDERSTOOD),
        lecture(2, LectureStatus.UNMARKED),
        lecture(3, LectureStatus.UPCOMING),
    ]
    summary = compute_summary(lectures)
    assert [item.order_index for item in summary.unmarked_before_upcoming] == [2]
    assert summary.missed_lectures == []


def test_unmarked_after_upcoming_is_ignored():
    lectures = [
        lecture(1, LectureStatus.UNDERSTOOD),
        lecture(2, LectureStatus.UPCOMING),
        lecture(3, LectureStatus.UNMARKED),
    ]
    summary = compute_summary(lectures)
    assert summary.unmarked_before_upcoming == []


def test_last_understood_is_the_highest_ordered_understood_lecture():
    lectures = [
        lecture(1, LectureStatus.UNDERSTOOD),
        lecture(2, LectureStatus.UNDERSTOOD),
        lecture(3, LectureStatus.MISSED),
        lecture(4, LectureStatus.UPCOMING),
    ]
    summary = compute_summary(lectures)
    assert summary.last_understood_lecture.order_index == 2


def test_input_order_does_not_matter():
    lectures = [
        lecture(3, LectureStatus.UPCOMING),
        lecture(1, LectureStatus.UNDERSTOOD),
        lecture(2, LectureStatus.MISSED),
    ]
    summary = compute_summary(lectures)
    assert summary.last_understood_lecture.order_index == 1
    assert [missed.order_index for missed in summary.missed_lectures] == [2]
    assert summary.upcoming_lecture.order_index == 3


def test_only_the_first_upcoming_is_used_when_data_is_inconsistent():
    """The API enforces a single upcoming lecture; the pure function stays total."""
    lectures = [
        lecture(1, LectureStatus.UPCOMING),
        lecture(2, LectureStatus.UPCOMING),
    ]
    summary = compute_summary(lectures)
    assert summary.upcoming_lecture.order_index == 1


def test_marking_a_later_lecture_upcoming_shifts_the_gap():
    """Changing which lecture is upcoming changes what counts as the gap."""
    before = [
        lecture(1, LectureStatus.UNDERSTOOD),
        lecture(2, LectureStatus.MISSED),
        lecture(3, LectureStatus.UPCOMING),
    ]
    after = [
        lecture(1, LectureStatus.UNDERSTOOD),
        lecture(2, LectureStatus.MISSED),
        lecture(3, LectureStatus.MISSED),
        lecture(4, LectureStatus.UPCOMING),
    ]
    assert [item.order_index for item in compute_summary(before).missed_lectures] == [2]
    assert [item.order_index for item in compute_summary(after).missed_lectures] == [2, 3]
