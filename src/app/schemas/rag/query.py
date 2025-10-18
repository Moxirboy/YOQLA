"""Query schemas"""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000, description="The user's question")
    top_k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve")
    score_threshold: float | None = Field(
        None, ge=0.0, le=1.0, description="Minimum similarity score (0-1)"
    )


class RetrievedChunk(BaseModel):
    """A single retrieved chunk with its metadata"""

    content: str
    score: float
    document_id: int
    document_filename: str
    chunk_index: int


class QueryResponse(BaseModel):
    """Response from a RAG query"""

    answer: str
    chunks: list[RetrievedChunk]
    query: str
    latency_ms: int
    model: str
