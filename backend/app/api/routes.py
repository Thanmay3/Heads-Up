from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    CourseCreate,
    CourseDetail,
    CourseListItem,
    CourseOut,
    CourseUpdate,
    LectureCreate,
    LectureOut,
    LectureUpdate,
    MaterialOut,
    MaterialSegmentOut,
    NotesMaterialCreate,
)
from app.services import courses as course_service
from app.services import lectures as lecture_service
from app.services import materials as material_service


def register(app_router: APIRouter) -> None:
    @app_router.get("/health", tags=["health"])
    def health(db: Session = Depends(get_db)) -> dict[str, str]:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}

    courses = APIRouter(prefix="/courses", tags=["courses"])

    @courses.get("", response_model=list[CourseListItem])
    def list_courses(db: Session = Depends(get_db)) -> list[CourseListItem]:
        return course_service.list_courses(db)

    @courses.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
    def create_course(payload: CourseCreate, db: Session = Depends(get_db)) -> CourseOut:
        return CourseOut.model_validate(course_service.create_course(db, payload.name))

    @courses.get("/{course_id}", response_model=CourseDetail)
    def get_course(course_id: int, db: Session = Depends(get_db)) -> CourseDetail:
        return course_service.get_course_detail(db, course_id)

    @courses.patch("/{course_id}", response_model=CourseOut)
    def update_course(
        course_id: int, payload: CourseUpdate, db: Session = Depends(get_db)
    ) -> CourseOut:
        return CourseOut.model_validate(course_service.update_course(db, course_id, payload.name))

    @courses.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_course(course_id: int, db: Session = Depends(get_db)) -> None:
        course_service.delete_course(db, course_id)

    @courses.post(
        "/{course_id}/lectures",
        response_model=LectureOut,
        status_code=status.HTTP_201_CREATED,
    )
    def add_lecture(
        course_id: int, payload: LectureCreate, db: Session = Depends(get_db)
    ) -> LectureOut:
        lecture = lecture_service.add_lecture(db, course_id, payload.title)
        return LectureOut.model_validate(lecture)

    app_router.include_router(courses)

    lectures = APIRouter(prefix="/lectures", tags=["lectures"])

    @lectures.patch("/{lecture_id}", response_model=LectureOut)
    def update_lecture(
        lecture_id: int, payload: LectureUpdate, db: Session = Depends(get_db)
    ) -> LectureOut:
        if payload.title is None and payload.status is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Provide at least one of: title, status",
            )
        lecture = lecture_service.update_lecture(
            db, lecture_id, title=payload.title, status=payload.status
        )
        return LectureOut.model_validate(lecture)

    @lectures.delete("/{lecture_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_lecture(lecture_id: int, db: Session = Depends(get_db)) -> None:
        lecture_service.delete_lecture(db, lecture_id)

    @lectures.post(
        "/{lecture_id}/materials",
        response_model=MaterialOut,
        status_code=status.HTTP_201_CREATED,
    )
    def upload_material(
        lecture_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
    ) -> MaterialOut:
        material = material_service.add_file_material(db, lecture_id, file)
        return MaterialOut.model_validate(material)

    @lectures.get("/{lecture_id}/materials", response_model=list[MaterialOut])
    def list_materials(lecture_id: int, db: Session = Depends(get_db)) -> list[MaterialOut]:
        return [
            MaterialOut.model_validate(material)
            for material in material_service.list_materials(db, lecture_id)
        ]

    @lectures.post(
        "/{lecture_id}/notes",
        response_model=MaterialOut,
        status_code=status.HTTP_201_CREATED,
    )
    def add_notes(
        lecture_id: int, payload: NotesMaterialCreate, db: Session = Depends(get_db)
    ) -> MaterialOut:
        material = material_service.add_notes_material(
            db, lecture_id, title=payload.title, content=payload.content
        )
        return MaterialOut.model_validate(material)

    app_router.include_router(lectures)

    materials = APIRouter(tags=["materials"])

    @materials.get("/materials/{material_id}", response_model=MaterialOut)
    def get_material(material_id: int, db: Session = Depends(get_db)) -> MaterialOut:
        return MaterialOut.model_validate(material_service.get_material(db, material_id))

    @materials.get("/materials/{material_id}/segments", response_model=list[MaterialSegmentOut])
    def get_material_segments(
        material_id: int, db: Session = Depends(get_db)
    ) -> list[MaterialSegmentOut]:
        return [
            MaterialSegmentOut.model_validate(segment)
            for segment in material_service.get_material_segments(db, material_id)
        ]

    @materials.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_material(material_id: int, db: Session = Depends(get_db)) -> None:
        material_service.delete_material(db, material_id)

    app_router.include_router(materials)
