"""Seed a demo course matching the HeadsUp core scenario.

Run from backend/:  .venv/Scripts/python.exe scripts/seed_demo.py

Idempotent: if a course named "Computer Networks" already has lectures, nothing
is created. The shape mirrors the product's core example -- the student
understood lectures 1-8, missed the two congestion-control lectures, and is
preparing for "Quality of Service".
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal  # noqa: E402
from app.models import Course, Lecture, LectureStatus  # noqa: E402
from app.services.courses import create_course  # noqa: E402
from app.services.lectures import add_lecture, update_lecture  # noqa: E402

COURSE_NAME = "Computer Networks"

LECTURES: list[tuple[str, LectureStatus]] = [
    ("Introduction", LectureStatus.UNDERSTOOD),
    ("The Network Edge", LectureStatus.UNDERSTOOD),
    ("HTTP", LectureStatus.UNDERSTOOD),
    ("DNS", LectureStatus.UNDERSTOOD),
    ("The Transport Layer", LectureStatus.UNDERSTOOD),
    ("UDP", LectureStatus.UNDERSTOOD),
    ("Reliable Data Transfer", LectureStatus.UNDERSTOOD),
    ("TCP", LectureStatus.UNDERSTOOD),
    ("Congestion Control", LectureStatus.MISSED),
    ("Congestion Control, continued", LectureStatus.MISSED),
    ("Quality of Service", LectureStatus.UPCOMING),
]


def main() -> None:
    with SessionLocal() as db:
        present = db.query(Course).filter(Course.name == COURSE_NAME).first()
        if present is not None and db.query(Lecture).filter_by(course_id=present.id).count() > 0:
            print(f'Course "{COURSE_NAME}" already seeded; nothing to do.')
            return
        if present is not None:
            db.delete(present)
            db.commit()

    course = create_course(SessionLocal(), COURSE_NAME)
    for title, lecture_status in LECTURES:
        lecture = add_lecture(SessionLocal(), course.id, title)
        if lecture_status is not LectureStatus.UNMARKED:
            update_lecture(SessionLocal(), lecture.id, status=lecture_status)
    print(f'Seeded "{COURSE_NAME}" with {len(LECTURES)} lectures (course id {course.id}).')


if __name__ == "__main__":
    main()
