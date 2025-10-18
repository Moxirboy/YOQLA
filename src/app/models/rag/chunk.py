"""Chunk model for document text segments"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ...core.db.database import Base

if TYPE_CHECKING:
    from .document import Document
    from .embedding import Embedding


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, init=False
    )
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True, default=None)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks", init=False)
    embedding: Mapped["Embedding | None"] = relationship(
        "Embedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan", init=False, default=None
    )
