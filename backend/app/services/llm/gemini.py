# ruff: noqa: E501
import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import google.generativeai as genai
from google.api_core import exceptions
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.services.llm.base import BaseLLMService

logger = logging.getLogger(__name__)


class GeminiLLMService(BaseLLMService):
    """Google Gemini LLM implementation."""

    def __init__(self, model: str = "gemini-1.5-pro"):
        self.model_name = model
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def _format_messages(self, messages: list[dict[str, str]]) -> list[dict[str, Any]]:
        """Convert OpenAI format messages to Gemini format."""
        formatted = []
        for msg in messages:
            role = msg["role"]
            if role == "system":
                # Gemini handles system instructions differently in GenerativeModel init
                # For simplicity here, we'll map system to user or just skip it if needed
                # Real implementation should use system_instruction in GenerativeModel
                role = "user"
            elif role == "assistant":
                role = "model"

            formatted.append({"role": role, "parts": [msg["content"]]})
        return formatted

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
            f"Gemini LLM API error, retrying attempt {retry_state.attempt_number}..."
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
            # Handle system message separately if present
            system_instruction = None
            if messages and messages[0]["role"] == "system":
                system_instruction = messages[0]["content"]
                messages = messages[1:]

            model = genai.GenerativeModel(
                model_name=self.model_name, system_instruction=system_instruction
            )

            formatted_messages = self._format_messages(messages)

            config = genai.types.GenerationConfig(
                temperature=temperature
                if temperature is not None
                else settings.LLM_TEMPERATURE,
                max_output_tokens=max_tokens
                if max_tokens is not None
                else settings.LLM_MAX_TOKENS,
                **kwargs,
            )

            response = await asyncio.to_thread(
                model.generate_content,
                contents=formatted_messages,
                generation_config=config,
            )

            return response.text
        except Exception as e:
            logger.error(f"Error in Gemini chat completion: {e}")
            raise

    async def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        # Basic implementation using to_thread for the blocking iterator
        try:
            system_instruction = None
            if messages and messages[0]["role"] == "system":
                system_instruction = messages[0]["content"]
                messages = messages[1:]

            model = genai.GenerativeModel(
                model_name=self.model_name, system_instruction=system_instruction
            )

            formatted_messages = self._format_messages(messages)
            config = genai.types.GenerationConfig(
                temperature=temperature
                if temperature is not None
                else settings.LLM_TEMPERATURE,
                max_output_tokens=max_tokens
                if max_tokens is not None
                else settings.LLM_MAX_TOKENS,
                **kwargs,
            )

            # Gemini's stream is a blocking iterator, we need to handle it carefully in async
            def get_stream():
                return model.generate_content(
                    contents=formatted_messages,
                    generation_config=config,
                    stream=True,
                )

            stream = await asyncio.to_thread(get_stream)
            for chunk in stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Error in Gemini streaming chat completion: {e}")
            raise
