"""Query Event model for analytics"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ...core.db.database import Base

if TYPE_CHECKING:
    from .workspace import Workspace
    from .api_key import ApiKey


class QueryEvent(Base):
    __tablename__ = "query_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False)
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True, init=False
    )
    api_key_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True, default=None
    )
    response: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    retrieved_chunks: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True, default=None)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="query_events", init=False)
    api_key: Mapped["ApiKey | None"] = relationship("ApiKey", back_populates="query_events", init=False, default=None)
