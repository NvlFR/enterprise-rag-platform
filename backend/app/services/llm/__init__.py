import logging

from app.core.config import settings
from app.services.llm.base import BaseLLMService
from app.services.llm.mock import MockLLMService

logger = logging.getLogger(__name__)

_llm_service: BaseLLMService | None = None


def get_llm_service() -> BaseLLMService:
    """
    Factory function to get the configured LLM service.
    """
    global _llm_service
    if _llm_service is not None:
        return _llm_service

    provider = settings.LLM_PROVIDER.lower()

    if provider == "mock":
        logger.info("Using MockLLMService")
        _llm_service = MockLLMService()
        return _llm_service

    elif provider == "openai":
        try:
            from app.services.llm.openai import OpenAILLMService

            _llm_service = OpenAILLMService()
            return _llm_service
        except ImportError:
            logger.warning(
                "OpenAILLMService dependencies not found. Falling back to Mock."
            )
            return MockLLMService()

    elif provider == "gemini":
        try:
            from app.services.llm.gemini import GeminiLLMService

            _llm_service = GeminiLLMService()
            return _llm_service
        except ImportError:
            logger.warning(
                "GeminiLLMService dependencies not found. Falling back to Mock."
            )
            return MockLLMService()

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


class LLMServiceProxy:
    """Lazy proxy for the LLM service singleton."""

    def __getattr__(self, name):
        return getattr(get_llm_service(), name)

    def __repr__(self):
        return repr(get_llm_service())


# Global singleton instance (lazy)
llm_service = LLMServiceProxy()
