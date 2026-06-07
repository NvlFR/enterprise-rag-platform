import logging

from app.core.config import settings
from app.services.embedding.base import BaseEmbeddingService
from app.services.embedding.mock import MockEmbeddingService

logger = logging.getLogger(__name__)

_embedding_service: BaseEmbeddingService | None = None


def get_embedding_service() -> BaseEmbeddingService:
    """
    Factory function to get the configured embedding service.
    """
    global _embedding_service
    if _embedding_service is not None:
        return _embedding_service

    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "mock":
        logger.info("Using MockEmbeddingService")
        _embedding_service = MockEmbeddingService(
            dimension=settings.DEFAULT_VECTOR_DIMENSION
        )
        return _embedding_service

    elif provider == "openai":
        # Placeholder for OpenAI service (TASK-025)
        try:
            from app.services.embedding.openai import OpenAIEmbeddingService

            _embedding_service = OpenAIEmbeddingService()
            return _embedding_service
        except ImportError:
            logger.warning(
                "OpenAIEmbeddingService not implemented yet. Falling back to Mock."
            )
            return MockEmbeddingService()

    elif provider == "gemini":
        # Placeholder for Gemini service (TASK-026)
        try:
            from app.services.embedding.gemini import GeminiEmbeddingService

            _embedding_service = GeminiEmbeddingService()
            return _embedding_service
        except ImportError:
            logger.warning(
                "GeminiEmbeddingService not implemented yet. Falling back to Mock."
            )
            return MockEmbeddingService()

    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


class EmbeddingServiceProxy:
    """Lazy proxy for the embedding service singleton."""

    def __getattr__(self, name):
        return getattr(get_embedding_service(), name)

    def __repr__(self):
        return repr(get_embedding_service())


# Global singleton instance (lazy)
embedding_service = EmbeddingServiceProxy()
