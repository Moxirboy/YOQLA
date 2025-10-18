"""Workspace model for multi-tenancy"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ...core.db.database import Base

if TYPE_CHECKING:
    from .api_key import ApiKey
    from .document import Document
    from .embedding import Embedding
    from .query_event import QueryEvent


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, init=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    api_keys: Mapped[list["ApiKey"]] = relationship(
        "ApiKey", back_populates="workspace", cascade="all, delete-orphan", init=False, default_factory=list
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="workspace", cascade="all, delete-orphan", init=False, default_factory=list
    )
    embeddings: Mapped[list["Embedding"]] = relationship(
        "Embedding", back_populates="workspace", cascade="all, delete-orphan", init=False, default_factory=list
    )
    query_events: Mapped[list["QueryEvent"]] = relationship(
        "QueryEvent", back_populates="workspace", cascade="all, delete-orphan", init=False, default_factory=list
    )
