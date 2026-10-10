from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Lecture, LectureStatus
from app.services.courses import get_course
from app.services.errors import NotFoundError


def get_lecture(db: Session, lecture_id: int) -> Lecture:
    lecture = db.get(Lecture, lecture_id)
    if lecture is None:
        raise NotFoundError(f"Lecture {lecture_id} not found")
    return lecture


def add_lecture(db: Session, course_id: int, title: str) -> Lecture:
    get_course(db, course_id)
    next_index = (
        db.scalar(
            select(func.max(Lecture.order_index)).where(Lecture.course_id == course_id)
        )
        or 0
    ) + 1
    lecture = Lecture(course_id=course_id, order_index=next_index, title=title)
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    return lecture


def update_lecture(
    db: Session,
    lecture_id: int,
    title: str | None = None,
    status: LectureStatus | None = None,
) -> Lecture:
    lecture = get_lecture(db, lecture_id)

    if title is not None:
        lecture.title = title

    if status is not None:
        if status == LectureStatus.UPCOMING:
            # A course has at most one upcoming lecture: the one the student is
            # preparing for. The previous upcoming lecture becomes unmarked --
            # the student still has to mark it understood or missed after class.
            others = db.scalars(
                select(Lecture).where(
                    Lecture.course_id == lecture.course_id,
                    Lecture.id != lecture.id,
                    Lecture.status == LectureStatus.UPCOMING,
                )
            ).all()
            for other in others:
                other.status = LectureStatus.UNMARKED
        lecture.status = status

    db.commit()
    db.refresh(lecture)
    return lecture


def delete_lecture(db: Session, lecture_id: int) -> None:
    lecture = get_lecture(db, lecture_id)
    course_id = lecture.course_id
    removed_index = lecture.order_index
    db.delete(lecture)
    db.flush()

    # Close the gap so lecture order stays contiguous (L1..Ln). Renumber one
    # lecture at a time in ascending order: with a unique (course_id,
    # order_index) constraint, each lecture moves into the slot the previous
    # one just vacated, so no transient duplicate ever exists.
    followers = db.scalars(
        select(Lecture)
        .where(Lecture.course_id == course_id, Lecture.order_index > removed_index)
        .order_by(Lecture.order_index.asc())
    ).all()
    for follower in followers:
        follower.order_index -= 1
        db.flush()

    db.commit()
