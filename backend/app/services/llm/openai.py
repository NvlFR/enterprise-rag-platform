import logging
from collections.abc import AsyncIterator
from typing import Any

from openai import APITimeoutError, AsyncOpenAI, InternalServerError, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.services.llm.base import BaseLLMService

logger = logging.getLogger(__name__)


class OpenAILLMService(BaseLLMService):
    """OpenAI LLM implementation."""

    def __init__(self, model: str = None):
        self.model = model or settings.LLM_MODEL
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @retry(
        retry=retry_if_exception_type(
            (RateLimitError, APITimeoutError, InternalServerError)
        ),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        before_sleep=lambda retry_state: logger.warning(
            f"OpenAI LLM API error, retrying attempt {retry_state.attempt_number}..."
        ),
    )
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
                if temperature is not None
                else settings.LLM_TEMPERATURE,
                max_tokens=max_tokens
                if max_tokens is not None
                else settings.LLM_MAX_TOKENS,
                **kwargs,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in OpenAI chat completion: {e}")
            raise

    async def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
                if temperature is not None
                else settings.LLM_TEMPERATURE,
                max_tokens=max_tokens
                if max_tokens is not None
                else settings.LLM_MAX_TOKENS,
                stream=True,
                **kwargs,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error in OpenAI streaming chat completion: {e}")
            raise
