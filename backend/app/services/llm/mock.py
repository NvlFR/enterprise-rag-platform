from collections.abc import AsyncIterator
from typing import Any

from app.services.llm.base import BaseLLMService


class MockLLMService(BaseLLMService):
    """A mock LLM service for testing."""

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        last_user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        return f"Mock response to: {last_user_msg}"

    async def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        response = await self.chat_completion(messages)
        for word in response.split():
            yield word + " "
