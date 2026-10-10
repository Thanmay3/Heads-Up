from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import LectureStatus


class LectureRef(BaseModel):
    """Lightweight lecture reference used in course summaries."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_index: int
    title: str
    status: LectureStatus


class LectureOut(LectureRef):
    created_at: datetime
    updated_at: datetime


class LectureCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)


class LectureUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: LectureStatus | None = None


class CourseSummary(BaseModel):
    """The student's position in a course, derived from lecture statuses.

    - last_understood_lecture: highest-order UNDERSTOOD lecture (the point the
      student's knowledge is assumed to be complete up to).
    - upcoming_lecture: the single lecture marked UPCOMING, if any.
    - missed_lectures: MISSED lectures that create the gap before the upcoming
      lecture; if no upcoming lecture is marked, all MISSED lectures.
    - unmarked_before_upcoming: lectures before the upcoming one that are not
      marked at all -- the app nudges the student to resolve these because an
      unmarked lecture is treated as "not known", never as "known".
    """

    last_understood_lecture: LectureRef | None
    upcoming_lecture: LectureRef | None
    missed_lectures: list[LectureRef]
    unmarked_before_upcoming: list[LectureRef]
