import asyncio
import logging

from openai import APITimeoutError, AsyncOpenAI, InternalServerError, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.services.embedding.base import BaseEmbeddingService

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService(BaseEmbeddingService):
    """OpenAI embedding implementation with retry logic and batch processing."""

    def __init__(
        self, model: str = None, dimension: int = None, max_concurrency: int = 5
    ):
        self.model = model or settings.EMBEDDING_MODEL
        self._dimension = dimension or settings.DEFAULT_VECTOR_DIMENSION
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.semaphore = asyncio.Semaphore(max_concurrency)

    @retry(
        retry=retry_if_exception_type(
            (RateLimitError, APITimeoutError, InternalServerError)
        ),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        before_sleep=lambda retry_state: logger.warning(
            f"OpenAI API error, retrying attempt {retry_state.attempt_number}..."
        ),
    )
    async def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        """Embed a single batch with retry logic and concurrency control."""
        async with self.semaphore:
            response = await self.client.embeddings.create(
                input=batch,
                model=self.model,
                dimensions=self._dimension
                if "text-embedding-3" in self.model
                else None,
            )
            return [data.embedding for data in response.data]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of document strings using OpenAI's API.
        Handles batching and parallel execution.
        """
        if not texts:
            return []

        # OpenAI limit is 2048 inputs per request.
        # We use a smaller batch size to avoid long request times and timeout issues.
        batch_size = 100
        tasks = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            tasks.append(self._embed_batch(batch))

        # Execute batches in parallel (limited by semaphore)
        results = await asyncio.gather(*tasks)

        # Flatten the list of lists
        all_embeddings = [emb for batch_result in results for emb in batch_result]
        return all_embeddings

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string with retry logic."""
        result = await self._embed_batch([text])
        return result[0]

    @property
    def dimension(self) -> int:
        return self._dimension
