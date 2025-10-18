"""Embedding generation using LLM provider"""
import logging
from typing import List

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import settings

logger = logging.getLogger(__name__)

# Configure LLM API
genai.configure(api_key=settings.LLM_API_KEY)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_embedding(text: str, model: str | None = None) -> List[float]:
    """
    Generate embedding for a single text

    Args:
        text: Text to embed
        model: Embedding model to use (defaults to settings.EMBEDDING_PROVIDER)

    Returns:
        Embedding vector as list of floats
    """
    model = model or settings.EMBEDDING_PROVIDER

    try:
        result = genai.embed_content(
            model=f"models/{model}",
            content=text,
            task_type="retrieval_document",
        )

        embedding = result["embedding"]
        logger.debug(f"Generated embedding with {len(embedding)} dimensions")
        return embedding

    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


def generate_embeddings_batch(
    texts: List[str], model: str | None = None, batch_size: int | None = None
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batches

    Args:
        texts: List of texts to embed
        model: Embedding model to use
        batch_size: Number of texts per batch

    Returns:
        List of embedding vectors
    """
    model = model or settings.EMBEDDING_PROVIDER
    batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE

    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        logger.info(f"Generating embeddings for batch {i // batch_size + 1}")

        for text in batch:
            emb = generate_embedding(text, model=model)
            embeddings.append(emb)

    logger.info(f"Generated {len(embeddings)} embeddings")
    return embeddings
