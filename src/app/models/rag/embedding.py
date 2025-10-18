"""Embedding model for vector storage"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, ARRAY, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ...core.db.database import Base

if TYPE_CHECKING:
    from .chunk import Chunk
    from .workspace import Workspace


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False)
    chunk_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, init=False
    )

    # Relationships
    chunk: Mapped["Chunk"] = relationship("Chunk", back_populates="embedding", init=False)
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="embeddings", init=False)
