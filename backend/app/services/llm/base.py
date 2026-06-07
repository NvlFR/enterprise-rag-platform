from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class BaseLLMService(ABC):
    """Abstract base class for all LLM services."""

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Send a chat completion request to the LLM.

        Args:
            messages: A list of message objects (role, content).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            The generated response string.
        """
        pass

    @abstractmethod
    async def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Send a streaming chat completion request to the LLM.
        """
        pass
