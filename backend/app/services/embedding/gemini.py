import asyncio
import logging

import google.generativeai as genai
from google.api_core import exceptions
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.services.embedding.base import BaseEmbeddingService

logger = logging.getLogger(__name__)


class GeminiEmbeddingService(BaseEmbeddingService):
    """Google Gemini embedding implementation with retry logic and batch processing."""

    def __init__(self, model: str = "models/embedding-001", max_concurrency: int = 5):
        self.model = model
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Default dimension for embedding-001 is 768
        self._dimension = 768
        self.semaphore = asyncio.Semaphore(max_concurrency)

    @retry(
        retry=retry_if_exception_type(
            (
                exceptions.ResourceExhausted,
                exceptions.ServiceUnavailable,
                exceptions.InternalServerError,
            )
        ),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        before_sleep=lambda retry_state: logger.warning(
            f"Gemini API error, retrying attempt {retry_state.attempt_number}..."
        ),
    )
    async def _embed_batch(
        self, batch: list[str], task_type: str = "retrieval_document"
    ) -> list[list[float]]:
        """Embed a single batch with retry logic and concurrency control."""
        async with self.semaphore:
            # Wrap synchronous genai call in a thread
            result = await asyncio.to_thread(
                genai.embed_content,
                model=self.model,
                content=batch,
                task_type=task_type,
            )
            # result["embedding"] is a list of lists if batch, or a single list if string.  # noqa: E501
            # But we passed a list, so it should be a list of lists.
            return result["embedding"]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of document strings using Gemini's API.
        Handles batching and parallel execution.
        """
        if not texts:
            return []

        # Gemini supports up to 100 texts per request or 1000 tokens (approx)
        batch_size = 50
        tasks = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            tasks.append(self._embed_batch(batch, task_type="retrieval_document"))

        results = await asyncio.gather(*tasks)

        # Flatten the list of lists
        all_embeddings = [emb for batch_result in results for emb in batch_result]
        return all_embeddings

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string with retry logic."""
        # Note: for a single string, embed_content returns a single list in result["embedding"]  # noqa: E501
        # But our _embed_batch returns a list of lists if we pass [text]
        result = await self._embed_batch([text], task_type="retrieval_query")
        return result[0]

    @property
    def dimension(self) -> int:
        return self._dimension
