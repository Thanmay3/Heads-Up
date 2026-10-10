from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import MaterialFileType, MaterialKind, MaterialStatus


class MaterialOut(BaseModel):
    """API view of a lecture material.

    storage_path and content_hash are internal (dedup/traceability) and are
    deliberately not exposed; segment_count tells the UI how much text a
    material produced.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    lecture_id: int
    kind: MaterialKind
    file_type: MaterialFileType
    title: str
    original_filename: str | None
    file_size: int | None
    status: MaterialStatus
    error_message: str | None
    segment_count: int
    created_at: datetime


class NotesMaterialCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=100_000)


class MaterialSegmentOut(BaseModel):
    """One extracted text chunk with its source position (page/slide)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    page_number: int | None
    text: str
