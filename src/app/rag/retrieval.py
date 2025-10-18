"""Vector similarity retrieval"""
import logging
from typing import List, Tuple

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.rag.chunk import Chunk
from ..models.rag.document import Document
from ..models.rag.embedding import Embedding
from .embeddings import generate_embedding

logger = logging.getLogger(__name__)


async def retrieve_chunks(
    query: str,
    workspace_id: int,
    db: AsyncSession,
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> List[Tuple[Chunk, Document, float]]:
    """
    Retrieve most relevant chunks using cosine similarity

    Args:
        query: User's question
        workspace_id: Workspace ID for isolation
        db: Database session
        top_k: Number of chunks to retrieve
        score_threshold: Minimum similarity score

    Returns:
        List of (chunk, document, score) tuples
    """
    top_k = top_k or settings.RAG_TOP_K
    score_threshold = score_threshold or settings.RAG_SCORE_THRESHOLD

    # Generate query embedding
    logger.info(f"Generating embedding for query: {query[:50]}...")
    query_embedding = generate_embedding(query)

    # Calculate cosine similarity using PostgreSQL array operations
    # Cosine similarity = dot product / (magnitude1 * magnitude2)
    query_stmt = text(
        """
        WITH query_vec AS (
            SELECT CAST(:query_embedding AS FLOAT[]) AS vec
        )
        SELECT
            e.chunk_id,
            (
                (SELECT SUM(a * b) FROM UNNEST(e.embedding, q.vec) AS t(a, b)) /
                (
                    SQRT((SELECT SUM(a * a) FROM UNNEST(e.embedding) AS t(a))) *
                    SQRT((SELECT SUM(b * b) FROM UNNEST(q.vec) AS t(b)))
                )
            ) AS score
        FROM embeddings e, query_vec q
        WHERE e.workspace_id = :workspace_id
        ORDER BY score DESC
        LIMIT :top_k
        """
    )

    result = await db.execute(
        query_stmt,
        {
            "query_embedding": query_embedding,
            "workspace_id": workspace_id,
            "top_k": top_k,
        },
    )

    chunk_scores = result.fetchall()

    if not chunk_scores:
        logger.warning(f"No chunks found for workspace {workspace_id}")
        return []

    # Fetch chunks and documents
    chunk_ids = [row[0] for row in chunk_scores]
    score_map = {row[0]: row[1] for row in chunk_scores}

    stmt = (
        select(Chunk, Document)
        .join(Document, Chunk.document_id == Document.id)
        .where(Chunk.id.in_(chunk_ids))
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Combine chunks with scores and filter by threshold
    results = []
    for chunk, document in rows:
        score = score_map[chunk.id]
        if score >= score_threshold:
            results.append((chunk, document, score))

    # Sort by score descending
    results.sort(key=lambda x: x[2], reverse=True)

    logger.info(
        f"Retrieved {len(results)} chunks with scores >= {score_threshold} (from {len(chunk_scores)} total)"
    )

    return results
