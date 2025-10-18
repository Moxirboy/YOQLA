"""Answer generation using LLM provider"""
import logging
from typing import List, Tuple

import google.generativeai as genai

from ..core.config import settings
from ..models.rag.chunk import Chunk
from ..models.rag.document import Document

logger = logging.getLogger(__name__)

# Configure LLM API
genai.configure(api_key=settings.LLM_API_KEY)


def generate_answer(
    query: str,
    chunks: List[Tuple[Chunk, Document, float]],
    model: str | None = None,
) -> str:
    """
    Generate answer using retrieved chunks

    Args:
        query: User's question
        chunks: Retrieved (chunk, document, score) tuples
        model: LLM model to use

    Returns:
        Generated answer text
    """
    model = model or settings.LLM_MODEL

    if not chunks:
        return "I don't have enough information to answer that question based on the available documents."

    # Build context from chunks
    context_parts = []
    for i, (chunk, document, score) in enumerate(chunks, 1):
        context_parts.append(
            f"[Document: {document.filename}, Chunk {chunk.chunk_index}, Relevance: {score:.2f}]\n{chunk.content}"
        )

    context = "\n\n---\n\n".join(context_parts)

    # Build prompt
    prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided context from documents.

Context:
{context}

Question: {query}

Instructions:
- Answer the question based solely on the provided context
- If the context doesn't contain enough information, say so
- Cite the document names when referencing information
- Be concise but comprehensive

Answer:"""

    try:
        # Generate response
        logger.info(f"Generating answer with model {model}")
        llm_model = genai.GenerativeModel(model)

        response = llm_model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
            ),
        )

        answer = response.text
        logger.info(f"Generated answer with {len(answer)} characters")
        return answer

    except Exception as e:
        logger.error(f"Failed to generate answer: {e}")
        return f"Sorry, I encountered an error while generating the answer: {str(e)}"
