"""Background tasks for RAG document processing"""
import logging
from typing import Dict

import tiktoken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db.database import async_get_db
from ..models.rag.chunk import Chunk
from ..models.rag.document import Document
from ..models.rag.embedding import Embedding
from ..services.parse import document_parser
from ..services.storage import storage_service
from .chunking import chunk_text
from .embeddings import generate_embedding

logger = logging.getLogger(__name__)


async def process_document_task(ctx: Dict, document_id: int) -> Dict:
    """
    Background task to process a document:
    1. Download from storage
    2. Parse to text
    3. Chunk into segments
    4. Generate embeddings
    5. Store in database

    Args:
        ctx: ARQ context
        document_id: ID of document to process

    Returns:
        Dict with processing results
    """
    logger.info(f"Starting document processing for document_id={document_id}")

    # Get database session
    async for db in async_get_db():
        try:
            # Fetch document
            stmt = select(Document).where(Document.id == document_id)
            result = await db.execute(stmt)
            document = result.scalar_one_or_none()

            if not document:
                logger.error(f"Document {document_id} not found")
                return {"status": "error", "message": "Document not found"}

            # Update status to processing
            document.status = "processing"
            await db.commit()

            # Download file from storage
            logger.info(f"Downloading file from {document.storage_uri}")
            key = storage_service.parse_uri(document.storage_uri)
            file_bytes = await storage_service.get_object(key)

            # Parse document
            logger.info(f"Parsing {document.mime_type} file")
            text = document_parser.parse(file_bytes, document.mime_type, document.filename)

            if not text.strip():
                raise ValueError("No text extracted from document")

            # Chunk text
            logger.info("Chunking text")
            chunks = chunk_text(text)

            # Create encoding for token counting
            encoding = tiktoken.get_encoding("cl100k_base")

            # Save chunks and generate embeddings
            logger.info(f"Saving {len(chunks)} chunks and generating embeddings")
            embedding_model = "text-embedding-004"

            for i, chunk_content in enumerate(chunks):
                # Count tokens
                token_count = len(encoding.encode(chunk_content))

                # Create chunk
                chunk = Chunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk_content,
                    token_count=token_count,
                    meta={"source": document.filename, "page": None},
                )
                db.add(chunk)
                await db.flush()  # Get chunk.id

                # Generate embedding
                logger.info(f"Generating embedding for chunk {i + 1}/{len(chunks)}")
                embedding_vector = generate_embedding(chunk_content, model=embedding_model)

                # Create embedding
                embedding = Embedding(
                    chunk_id=chunk.id,
                    workspace_id=document.workspace_id,
                    embedding=embedding_vector,
                    model=embedding_model,
                )
                db.add(embedding)

            # Update document status
            document.status = "completed"
            document.total_chunks = len(chunks)
            document.error_message = None
            await db.commit()

            logger.info(f"Successfully processed document {document_id} with {len(chunks)} chunks")

            return {
                "status": "success",
                "document_id": document_id,
                "total_chunks": len(chunks),
            }

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}", exc_info=True)

            # Update document status to failed
            try:
                document.status = "failed"
                document.error_message = str(e)
                await db.commit()
            except Exception as commit_error:
                logger.error(f"Failed to update document status: {commit_error}")

            return {
                "status": "error",
                "document_id": document_id,
                "message": str(e),
            }

        finally:
            await db.close()

    return {"status": "error", "message": "Failed to get database session"}
