from app.schemas.course import (
    CourseCreate,
    CourseDetail,
    CourseListItem,
    CourseOut,
    CourseUpdate,
)
from app.schemas.lecture import (
    CourseSummary,
    LectureCreate,
    LectureOut,
    LectureRef,
    LectureUpdate,
)
from app.schemas.material import (
    MaterialOut,
    MaterialSegmentOut,
    NotesMaterialCreate,
)

__all__ = [
    "CourseCreate",
    "CourseDetail",
    "CourseListItem",
    "CourseOut",
    "CourseSummary",
    "CourseUpdate",
    "LectureCreate",
    "LectureOut",
    "LectureRef",
    "LectureUpdate",
    "MaterialOut",
    "MaterialSegmentOut",
    "NotesMaterialCreate",
]
