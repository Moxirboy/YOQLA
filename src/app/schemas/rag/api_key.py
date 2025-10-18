"""API Key schemas"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ApiKeyBase(BaseModel):
    name: str
    rate_limit_quota: int = 100


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyRead(ApiKeyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    key_prefix: str
    key: str  # Include full key
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApiKeyWithSecret(ApiKeyRead):
    """Response when creating a new API key - includes the full key once"""

    key: str
