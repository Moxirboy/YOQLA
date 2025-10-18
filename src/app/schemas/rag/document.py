"""Document schemas"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    filename: str
    file_size: int
    mime_type: str


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    workspace_id: int
    storage_uri: str
    status: str
    error_message: str | None
    total_chunks: int | None
    meta: dict | None = None  # Changed from metadata to match model
    uploaded_by: int
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    """Response after uploading documents"""

    documents: list[DocumentRead]
    message: str
