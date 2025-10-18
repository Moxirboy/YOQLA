"""RAG API endpoints - Full implementation"""

import hashlib
import logging
import secrets
import time
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.config import settings
from ...core.db.database import async_get_db
from ...core.utils import queue
from ...crud.crud_api_keys import crud_api_keys
from ...crud.crud_documents import crud_documents
from ...crud.crud_workspaces import crud_workspaces
from ...models.rag.api_key import ApiKey
from ...models.rag.query_event import QueryEvent
from ...models.rag.workspace import Workspace
from ...schemas.rag import (
    ApiKeyCreate,
    ApiKeyRead,
    ApiKeyWithSecret,
    DocumentRead,
    DocumentUploadResponse,
    QueryRequest,
    QueryResponse,
    RetrievedChunk,
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
)
from ...services.storage import storage_service
from ...rag.retrieval import retrieve_chunks
from ...rag.generation import generate_answer

router = APIRouter(tags=["rag"], prefix="/rag")
logger = logging.getLogger(__name__)


def get_workspace_user_id(workspace) -> int:
    """Helper to get user_id from workspace (handles both dict and object)"""
    if isinstance(workspace, dict):
        return workspace["user_id"]
    return workspace.user_id


def get_attr(obj, attr_name):
    """Helper to get attribute from object or dict"""
    if isinstance(obj, dict):
        return obj.get(attr_name)
    return getattr(obj, attr_name, None)


# ========== Workspace Management ==========

@router.post("/workspaces", response_model=WorkspaceRead, status_code=201)
async def create_workspace(
    workspace: WorkspaceCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> WorkspaceRead:
    """Create a new RAG workspace"""
    workspace_data = workspace.model_dump()
    workspace_data["user_id"] = current_user["id"]

    db_workspace = Workspace(**workspace_data)
    db.add(db_workspace)
    await db.commit()
    await db.refresh(db_workspace)

    logger.info(f"Created workspace {db_workspace.id} for user {current_user['id']}")
    return db_workspace


@router.get("/workspaces", response_model=List[WorkspaceRead])
async def list_workspaces(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> List[WorkspaceRead]:
    """List all workspaces for current user"""
    stmt = select(Workspace).where(Workspace.user_id == current_user["id"])
    result = await db.execute(stmt)
    workspaces = result.scalars().all()
    return workspaces


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> WorkspaceRead:
    """Get a specific workspace"""
    workspace = await crud_workspaces.get(db, id=workspace_id)
    if not workspace or get_workspace_user_id(workspace) != current_user["id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: int,
    workspace_update: WorkspaceUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> WorkspaceRead:
    """Update workspace"""
    workspace = await crud_workspaces.get(db, id=workspace_id)
    if not workspace or get_workspace_user_id(workspace) != current_user["id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")

    update_data = workspace_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workspace, key, value)

    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.delete("/workspaces/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> None:
    """Delete workspace (cascades to documents, chunks, embeddings)"""
    workspace = await crud_workspaces.get(db, id=workspace_id)
    if not workspace or get_workspace_user_id(workspace) != current_user["id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")

    await db.delete(workspace)
    await db.commit()


# ========== API Key Management ==========

@router.post("/workspaces/{workspace_id}/keys", response_model=ApiKeyWithSecret, status_code=201)
async def create_api_key(
    workspace_id: int,
    api_key_data: ApiKeyCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> ApiKeyWithSecret:
    """Create API key for workspace"""
    # Verify workspace ownership
    workspace = await crud_workspaces.get(db, id=workspace_id)
    if not workspace or get_workspace_user_id(workspace) != current_user["id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Generate API key
    key = f"rag_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_prefix = key[:12]

    # Create API key record with full key stored
    db_api_key = ApiKey(
        workspace_id=workspace_id,
        name=api_key_data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        key=key,  # Store full key in database
        rate_limit_quota=api_key_data.rate_limit_quota,
    )
    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)

    logger.info(f"Created API key {db_api_key.id} for workspace {workspace_id}")

    return db_api_key


@router.get("/workspaces/{workspace_id}/keys", response_model=List[ApiKeyRead])
async def list_api_keys(
    workspace_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> List[ApiKeyRead]:
    """List API keys for workspace"""
    workspace = await crud_workspaces.get(db, id=workspace_id)
    if not workspace or get_workspace_user_id(workspace) != current_user["id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")

    stmt = select(ApiKey).where(ApiKey.workspace_id == workspace_id)
    result = await db.execute(stmt)
    api_keys = result.scalars().all()
    return api_keys


@router.delete("/workspaces/{workspace_id}/keys/{key_id}", status_code=204)
async def delete_api_key(
    workspace_id: int,
    key_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> None:
    """Delete API key"""
    workspace = await crud_workspaces.get(db, id=workspace_id)
    if not workspace or get_workspace_user_id(workspace) != current_user["id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")

    api_key = await crud_api_keys.get(db, id=key_id)
    if not api_key or api_key.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.delete(api_key)
    await db.commit()


# ========== Document Management ==========

async def get_workspace_by_api_key(
    x_api_key: Annotated[str, Header()], db: Annotated[AsyncSession, Depends(async_get_db)]
) -> Workspace:
    """Dependency to get workspace from API key header"""
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()

    stmt = (
        select(ApiKey, Workspace)
        .join(Workspace, ApiKey.workspace_id == Workspace.id)
        .where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    )

    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")

    api_key, workspace = row

    # Update last_used_at
    from datetime import datetime
    api_key.last_used_at = datetime.now()
    await db.commit()

    return workspace


@router.post("/workspaces/{workspace_id}/documents", response_model=DocumentUploadResponse)
async def upload_documents(
    workspace_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    files: List[UploadFile] = File(...),
) -> DocumentUploadResponse:
    """Upload documents to workspace for processing"""
    # Verify workspace ownership
    workspace = await crud_workspaces.get(db, id=workspace_id)
    if not workspace or get_workspace_user_id(workspace) != current_user["id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Validate files
    allowed_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
        "text/markdown",
        "text/csv",
    }

    uploaded_docs = []

    for file in files:
        # Validate size
        content = await file.read()
        file_size = len(content)

        if file_size > settings.MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds maximum size of {settings.MAX_UPLOAD_BYTES} bytes",
            )

        # Validate type
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, detail=f"Unsupported file type: {file.content_type}"
            )

        # Upload to storage
        storage_key = f"workspaces/{workspace_id}/{secrets.token_urlsafe(16)}_{file.filename}"

        from io import BytesIO

        storage_uri = await storage_service.put_object(
            storage_key, BytesIO(content), file.content_type
        )

        # Create document record
        from ...models.rag.document import Document

        document = Document(
            workspace_id=workspace_id,
            filename=file.filename,
            file_size=file_size,
            mime_type=file.content_type,
            storage_uri=storage_uri,
            status="pending",
            uploaded_by=current_user["id"],
        )
        db.add(document)
        await db.flush()

        # Queue processing task
        if queue.pool is None:
            logger.error("Queue pool is not available")
            raise HTTPException(status_code=503, detail="Background job queue is not available")

        await queue.pool.enqueue_job("process_document_task", document.id)
        logger.info(f"Queued processing for document {document.id}")
        uploaded_docs.append(document)

    await db.commit()

    return DocumentUploadResponse(
        documents=[DocumentRead.model_validate(doc) for doc in uploaded_docs],
        message=f"Uploaded {len(uploaded_docs)} document(s). Processing started.",
    )


@router.get("/workspaces/{workspace_id}/documents", response_model=List[DocumentRead])
async def list_documents(
    workspace_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> List[DocumentRead]:
    """List documents in workspace"""
    workspace = await crud_workspaces.get(db, id=workspace_id)
    if not workspace or get_workspace_user_id(workspace) != current_user["id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")

    from ...models.rag.document import Document

    stmt = select(Document).where(Document.workspace_id == workspace_id).order_by(Document.created_at.desc())
    result = await db.execute(stmt)
    documents = result.scalars().all()
    return documents


@router.delete("/workspaces/{workspace_id}/documents/{document_id}", status_code=204)
async def delete_document(
    workspace_id: int,
    document_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> None:
    """Delete document (cascades to chunks and embeddings)"""
    workspace = await crud_workspaces.get(db, id=workspace_id)
    if not workspace or get_workspace_user_id(workspace) != current_user["id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Fetch document as model object, not dict
    from ...models.rag.document import Document

    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document or document.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from storage
    try:
        key = storage_service.parse_uri(document.storage_uri)
        await storage_service.delete_object(key)
    except Exception as e:
        logger.warning(f"Failed to delete file from storage: {e}")

    # Delete document (cascades to chunks and embeddings via ON DELETE CASCADE)
    await db.delete(document)
    await db.commit()


# ========== Query Endpoint ==========

@router.post("/query", response_model=QueryResponse)
async def query_rag(
    query: QueryRequest,
    workspace: Annotated[Workspace, Depends(get_workspace_by_api_key)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> QueryResponse:
    """Query RAG system using API key authentication"""
    start_time = time.time()

    # Retrieve relevant chunks
    chunks_with_docs = await retrieve_chunks(
        query.query, workspace.id, db, query.top_k, query.score_threshold
    )

    if not chunks_with_docs:
        return QueryResponse(
            answer="I don't have any relevant information to answer that question.",
            chunks=[],
            query=query.query,
            latency_ms=int((time.time() - start_time) * 1000),
            model=settings.LLM_MODEL,
        )

    # Generate answer
    answer = generate_answer(query.query, chunks_with_docs)

    # Build response
    retrieved_chunks = [
        RetrievedChunk(
            content=chunk.content,
            score=score,
            document_id=document.id,
            document_filename=document.filename,
            chunk_index=chunk.chunk_index,
        )
        for chunk, document, score in chunks_with_docs
    ]

    latency_ms = int((time.time() - start_time) * 1000)

    # Log query event
    query_event = QueryEvent(
        workspace_id=workspace.id,
        api_key_id=None,  # Could be extracted from workspace dependency
        query=query.query,
        response=answer,
        top_k=query.top_k,
        retrieved_chunks=len(chunks_with_docs),
        latency_ms=latency_ms,
    )
    db.add(query_event)
    await db.commit()

    return QueryResponse(
        answer=answer,
        chunks=retrieved_chunks,
        query=query.query,
        latency_ms=latency_ms,
        model=settings.LLM_MODEL,
    )


# ========== Health & Config Endpoints ==========

@router.get("/health")
async def rag_health_check() -> dict:
    """RAG module health check"""
    return {
        "status": "healthy",
        "rag_enabled": True,
        "llm_configured": bool(settings.LLM_API_KEY),
        "storage_configured": bool(settings.STORAGE_BUCKET),
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "model": settings.LLM_MODEL,
    }


@router.get("/test-llm")
async def test_llm_api() -> dict:
    """Test LLM API connection"""
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.LLM_API_KEY)
        model = genai.GenerativeModel(settings.LLM_MODEL)
        response = model.generate_content("Say 'API is working!' in 5 words")

        return {
            "status": "success",
            "response": response.text,
            "model": settings.LLM_MODEL,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/config")
async def get_rag_config(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get RAG configuration (requires authentication)"""
    return {
        "chunk_size": settings.RAG_CHUNK_SIZE,
        "chunk_overlap": settings.RAG_CHUNK_OVERLAP,
        "top_k": settings.RAG_TOP_K,
        "score_threshold": settings.RAG_SCORE_THRESHOLD,
        "max_upload_bytes": settings.MAX_UPLOAD_BYTES,
        "embedding_dim": settings.EMBEDDING_DIM,
        "model": settings.LLM_MODEL,
    }
