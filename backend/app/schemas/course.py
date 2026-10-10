from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lecture import CourseSummary, LectureOut


class CourseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)


class CourseUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    updated_at: datetime


class CourseListItem(CourseOut):
    lecture_count: int
    missed_count: int


class CourseDetail(CourseOut):
    lectures: list[LectureOut]
    summary: CourseSummary
