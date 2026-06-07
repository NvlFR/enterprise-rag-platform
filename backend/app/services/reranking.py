import logging
from abc import ABC, abstractmethod

from app.core.config import settings
from app.models.chunk import DocumentChunk

logger = logging.getLogger(__name__)


class BaseRerankingService(ABC):
    """Abstract base class for all reranking services."""

    @abstractmethod
    async def rerank(
        self, query: str, chunks: list[DocumentChunk]
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Rerank a list of chunks based on relevance to the query.

        Returns:
            A list of (chunk, score) tuples, sorted by score descending.
        """
        pass


class MockRerankingService(BaseRerankingService):
    """A mock reranker that returns slightly modified scores."""

    async def rerank(
        self, query: str, chunks: list[DocumentChunk]
    ) -> list[tuple[DocumentChunk, float]]:
        # For mock, we just return the chunks with pseudo-random scores
        # in their original order, or maybe slightly shuffled.
        results = []
        for i, chunk in enumerate(chunks):
            # Simulate a score between 0 and 1
            score = 1.0 / (i + 1)
            results.append((chunk, score))
        return results


class CohereRerankingService(BaseRerankingService):
    """Reranker using Cohere's Rerank API."""

    def __init__(self):
        try:
            import cohere

            self.client = cohere.ClientV2(api_key=settings.COHERE_API_KEY)
            self.model = settings.RERANKER_MODEL
        except ImportError:
            logger.error("cohere package not installed")
            raise

    async def rerank(
        self, query: str, chunks: list[DocumentChunk]
    ) -> list[tuple[DocumentChunk, float]]:
        if not chunks:
            return []

        try:
            import asyncio
            # Cohere Python SDK v5+ might be sync or have async methods.
            # Usually, we wrap sync API calls in to_thread.

            # Prepare documents for Cohere
            docs = [c.content for c in chunks]

            response = await asyncio.to_thread(
                self.client.rerank,
                model=self.model,
                query=query,
                documents=docs,
                top_n=len(chunks),
            )

            # Map response results back to chunks
            reranked_results = []
            for result in response.results:
                chunk = chunks[result.index]
                reranked_results.append((chunk, float(result.relevance_score)))

            return reranked_results
        except Exception as e:
            logger.error(f"Error calling Cohere Rerank: {e}")
            raise


def get_reranking_service() -> BaseRerankingService:
    """Factory to get the configured reranking service."""
    provider = settings.RERANKER_PROVIDER.lower()

    if provider == "mock":
        return MockRerankingService()
    elif provider == "cohere":
        return CohereRerankingService()
    else:
        logger.warning(
            f"Unsupported reranker provider: {provider}. Falling back to Mock."
        )
        return MockRerankingService()


# Singleton proxy
class RerankingServiceProxy:
    _instance = None

    def __getattr__(self, name):
        if self._instance is None:
            self._instance = get_reranking_service()
        return getattr(self._instance, name)


reranking_service = RerankingServiceProxy()
