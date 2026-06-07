import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentStatus


class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    doc_metadata: dict[str, Any] | None = None


class DocumentCreate(DocumentBase):
    """Schema untuk membuat document baru (internal use)."""

    file_path: str
    s3_key: str | None = None
    owner_id: uuid.UUID
    status: DocumentStatus = DocumentStatus.UPLOADED


class DocumentUpdate(BaseModel):
    """Schema untuk mengupdate status atau metadata document."""

    title: str | None = Field(None, min_length=1, max_length=255)
    status: DocumentStatus | None = None
    doc_metadata: dict[str, Any] | None = None


class DocumentRead(DocumentBase):
    """Schema untuk response document ke client."""

    id: uuid.UUID
    file_path: str
    s3_key: str | None
    status: DocumentStatus
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentListItem(BaseModel):
    """Schema ringkas untuk list documents."""

    id: uuid.UUID
    title: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
