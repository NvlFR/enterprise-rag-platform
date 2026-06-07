import logging

from app.models.chunk import DocumentChunk
from app.services.llm import llm_service
from app.services.prompt import prompt_service

logger = logging.getLogger(__name__)


class HallucinationService:
    """Service for detecting hallucinations in LLM responses."""

    async def check_hallucination(
        self, answer: str, chunks: list[DocumentChunk]
    ) -> bool:
        """
        Check if the answer is grounded in the provided chunks.
        Returns True if it's a hallucination, False if it's grounded.
        """
        try:
            # 1. Format the check prompt
            check_prompt = prompt_service.format_prompt(
                "hallucination_check", {"chunks": chunks, "answer": answer}
            )

            # 2. Call LLM for verification
            # We use a lower temperature for consistency in verification
            response = await llm_service.chat_completion(
                check_prompt, temperature=0.0, max_tokens=10
            )

            # 3. Parse response
            result = response.strip().lower()
            if "hallucination" in result:
                logger.warning("Potential hallucination detected!")
                return True

            return False

        except Exception as e:
            logger.error(f"Error during hallucination check: {e}")
            # In case of error, we default to False to avoid blocking the response
            # but log the failure.
            return False


hallucination_service = HallucinationService()
