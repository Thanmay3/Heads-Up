from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.models import Course, Lecture, LectureStatus
from app.schemas import CourseDetail, CourseListItem, CourseOut, LectureOut
from app.services.errors import NotFoundError
from app.services.summary import compute_summary


def create_course(db: Session, name: str) -> Course:
    course = Course(name=name)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def list_courses(db: Session) -> list[CourseListItem]:
    statement: Select = (
        select(
            Course,
            func.count(Lecture.id).label("lecture_count"),
            func.coalesce(
                func.sum(case((Lecture.status == LectureStatus.MISSED, 1), else_=0)), 0
            ).label("missed_count"),
        )
        .outerjoin(Lecture, Lecture.course_id == Course.id)
        .group_by(Course.id)
        .order_by(Course.created_at.desc(), Course.id.desc())
    )
    items: list[CourseListItem] = []
    for course, lecture_count, missed_count in db.execute(statement).all():
        items.append(
            CourseListItem(
                **CourseOut.model_validate(course).model_dump(),
                lecture_count=lecture_count,
                missed_count=int(missed_count),
            )
        )
    return items


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise NotFoundError(f"Course {course_id} not found")
    return course


def get_course_detail(db: Session, course_id: int) -> CourseDetail:
    course = get_course(db, course_id)
    lectures = list(course.lectures)
    return CourseDetail(
        **CourseOut.model_validate(course).model_dump(),
        lectures=[LectureOut.model_validate(lecture) for lecture in lectures],
        summary=compute_summary(lectures),
    )


def update_course(db: Session, course_id: int, name: str) -> Course:
    course = get_course(db, course_id)
    course.name = name
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course_id: int) -> None:
    course = get_course(db, course_id)
    db.delete(course)
    db.commit()
