"""CRUD operations for API Keys"""
from fastcrud import FastCRUD

from ..models.rag.api_key import ApiKey
from ..schemas.rag.api_key import ApiKeyCreate, ApiKeyRead

CRUDApiKey = FastCRUD[ApiKey, ApiKeyCreate, ApiKeyRead, ApiKeyRead, ApiKeyRead, ApiKeyRead]
crud_api_keys = CRUDApiKey(ApiKey)
