import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.material import LectureMaterial


class LectureStatus(enum.StrEnum):
    """Where the student stands on a lecture.

    Only UNDERSTOOD lectures contribute to the known-knowledge base used later
    by the bridge engine; UNMARKED is treated as not known, never as known.
    """

    UNMARKED = "unmarked"
    UNDERSTOOD = "understood"
    MISSED = "missed"
    UPCOMING = "upcoming"


class Lecture(TimestampMixin, Base):
    __tablename__ = "lectures"
    __table_args__ = (
        UniqueConstraint("course_id", "order_index", name="uq_lectures_course_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    order_index: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[LectureStatus] = mapped_column(
        SAEnum(
            LectureStatus,
            name="lecture_status",
            native_enum=False,
            length=16,
            validate_strings=True,
        ),
        default=LectureStatus.UNMARKED,
        nullable=False,
    )

    course: Mapped["Course"] = relationship(back_populates="lectures")
    materials: Mapped[list["LectureMaterial"]] = relationship(
        back_populates="lecture",
        cascade="all, delete-orphan",
        order_by="LectureMaterial.id",
    )
