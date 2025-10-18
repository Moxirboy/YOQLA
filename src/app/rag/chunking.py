"""Text chunking with tiktoken"""
import logging
from typing import List

import tiktoken

from ..core.config import settings

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    encoding_name: str = "cl100k_base",
) -> List[str]:
    """
    Split text into chunks based on token count

    Args:
        text: Text to chunk
        chunk_size: Target size of each chunk in tokens
        chunk_overlap: Number of overlapping tokens between chunks
        encoding_name: Tiktoken encoding to use

    Returns:
        List of text chunks
    """
    chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

    try:
        encoding = tiktoken.get_encoding(encoding_name)
    except Exception as e:
        logger.warning(f"Failed to get encoding {encoding_name}, using cl100k_base: {e}")
        encoding = tiktoken.get_encoding("cl100k_base")

    # Encode the entire text
    tokens = encoding.encode(text)
    total_tokens = len(tokens)

    logger.info(f"Chunking {total_tokens} tokens with size={chunk_size}, overlap={chunk_overlap}")

    if total_tokens <= chunk_size:
        # Text fits in a single chunk
        return [text]

    chunks = []
    start = 0

    while start < total_tokens:
        # Get chunk of tokens
        end = min(start + chunk_size, total_tokens)
        chunk_tokens = tokens[start:end]

        # Decode back to text
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)

        # Move to next chunk with overlap
        if end >= total_tokens:
            break
        start += chunk_size - chunk_overlap

    logger.info(f"Created {len(chunks)} chunks")
    return chunks
