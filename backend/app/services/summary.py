from collections.abc import Sequence

from app.models import Lecture, LectureStatus
from app.schemas import CourseSummary, LectureRef


def compute_summary(lectures: Sequence[Lecture]) -> CourseSummary:
    """Derive the student's position in a course from lecture statuses.

    Pure function: no database, no ordering assumptions about the input.
    """
    ordered = sorted(lectures, key=lambda lecture: lecture.order_index)

    understood = [lecture for lecture in ordered if lecture.status == LectureStatus.UNDERSTOOD]
    last_understood = understood[-1] if understood else None

    upcoming = next(
        (lecture for lecture in ordered if lecture.status == LectureStatus.UPCOMING), None
    )

    missed = [lecture for lecture in ordered if lecture.status == LectureStatus.MISSED]
    unmarked = [lecture for lecture in ordered if lecture.status == LectureStatus.UNMARKED]

    if upcoming is not None:
        missed = [lecture for lecture in missed if lecture.order_index < upcoming.order_index]
        unmarked = [
            lecture for lecture in unmarked if lecture.order_index < upcoming.order_index
        ]
    else:
        # The "before upcoming" framing does not apply; avoid nagging about
        # unmarked lectures when the student has not picked an upcoming lecture yet.
        unmarked = []

    def to_ref(lecture: Lecture) -> LectureRef:
        return LectureRef.model_validate(lecture)

    return CourseSummary(
        last_understood_lecture=to_ref(last_understood) if last_understood else None,
        upcoming_lecture=to_ref(upcoming) if upcoming else None,
        missed_lectures=[to_ref(lecture) for lecture in missed],
        unmarked_before_upcoming=[to_ref(lecture) for lecture in unmarked],
    )
