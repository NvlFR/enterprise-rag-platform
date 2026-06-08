# ruff: noqa: E501
import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

from app.services.chat_service import ChatService
from app.services.citation import citation_service
from app.services.hallucination import hallucination_service
from app.services.llm import llm_service
from app.services.prompt import prompt_service
from app.services.retrieval import RetrievalService

logger = logging.getLogger(__name__)


class RAGService:
    """Orchestrator for the RAG pipeline."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        chat_service: ChatService | None = None,
    ):
        self.retrieval_service = retrieval_service
        self.chat_service = chat_service

    async def generate_answer(
        self,
        question: str,
        top_k: int = 5,
        filters: dict | None = None,
        rephrase: bool = False,
        rerank: bool = True,
        context_window: int = 0,
        check_hallucination: bool = False,
        conversation_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Execute the full RAG flow to answer a question.
        """
        try:
            search_query = question
            history = []

            # 0. Load History and Save User Message
            if conversation_id and self.chat_service:
                history = await self.chat_service.format_history_for_prompt(
                    conversation_id
                )
                await self.chat_service.save_message(conversation_id, "user", question)

            # 1. Query Rephrasing (Optional)
            if rephrase:
                rephrase_prompt = prompt_service.format_prompt(
                    "query_rephraser", {"question": question, "history": history}
                )
                search_query = await llm_service.chat_completion(rephrase_prompt)
                logger.info(f"Rephrased query: {search_query}")

            # 2. Retrieval
            chunks_with_scores = await self.retrieval_service.hybrid_search(
                query=search_query,
                top_k=top_k,
                filters=filters,
                rerank=rerank,
                context_window=context_window,
            )

            if not chunks_with_scores:
                answer = "I don't have enough information to answer this question."
                if conversation_id and self.chat_service:
                    await self.chat_service.save_message(
                        conversation_id, "assistant", answer
                    )
                return {
                    "answer": answer,
                    "sources": [],
                    "verified_citations": [],
                    "is_hallucination": False,
                }

            # 3. Format Prompt
            chunks = [c for c, _ in chunks_with_scores]
            rag_prompt = prompt_service.format_prompt(
                "rag_answer",
                {"chunks": chunks, "question": question, "history": history},
            )

            # 4. Generate Answer
            raw_answer = await llm_service.chat_completion(rag_prompt)

            # 5. Verify Citations
            verified_answer, verified_citations = citation_service.verify_and_clean(
                raw_answer, chunks
            )

            # 6. Hallucination Check (Optional)
            is_hallucination = False
            if check_hallucination:
                is_hallucination = await hallucination_service.check_hallucination(
                    verified_answer, chunks
                )

            # 7. Save Assistant Message
            if conversation_id and self.chat_service:
                await self.chat_service.save_message(
                    conversation_id,
                    "assistant",
                    verified_answer,
                    metadata={"citations": verified_citations},
                )

            # 8. Prepare Response
            sources = []
            for chunk, score in chunks_with_scores:
                sources.append(
                    {
                        "id": str(chunk.id),
                        "content": chunk.content,
                        "metadata": chunk.chunk_metadata,
                        "score": score,
                    }
                )

            return {
                "answer": verified_answer,
                "sources": sources,
                "verified_citations": verified_citations,
                "is_hallucination": is_hallucination,
                "search_query": search_query,
            }

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            raise

    async def stream_generate_answer(
        self,
        question: str,
        top_k: int = 5,
        filters: dict | None = None,
        rephrase: bool = False,
        rerank: bool = True,
        context_window: int = 0,
        check_hallucination: bool = False,
        conversation_id: uuid.UUID | None = None,
    ) -> AsyncIterator[str]:
        """
        Execute the full RAG flow and stream the answer.
        Yields JSON strings for each chunk of the response.
        """
        try:
            search_query = question
            history = []

            # 0. Load History and Save User Message
            if conversation_id and self.chat_service:
                history = await self.chat_service.format_history_for_prompt(
                    conversation_id
                )
                await self.chat_service.save_message(conversation_id, "user", question)

            # 1. Query Rephrasing
            if rephrase:
                rephrase_prompt = prompt_service.format_prompt(
                    "query_rephraser", {"question": question, "history": history}
                )
                search_query = await llm_service.chat_completion(rephrase_prompt)

            yield json.dumps({"type": "search_query", "query": search_query}) + "\n"

            # 2. Retrieval
            chunks_with_scores = await self.retrieval_service.hybrid_search(
                query=search_query,
                top_k=top_k,
                filters=filters,
                rerank=rerank,
                context_window=context_window,
            )

            if not chunks_with_scores:
                answer = "I don't have enough information to answer this question."
                if conversation_id and self.chat_service:
                    await self.chat_service.save_message(
                        conversation_id, "assistant", answer
                    )
                yield (
                    json.dumps(
                        {
                            "type": "answer",
                            "content": answer,
                        }
                    )
                    + "\n"
                )
                yield json.dumps({"type": "done"}) + "\n"
                return

            # Yield sources early so the UI can show them
            sources = []
            for chunk, score in chunks_with_scores:
                sources.append(
                    {
                        "id": str(chunk.id),
                        "content": chunk.content,
                        "metadata": chunk.chunk_metadata,
                        "score": score,
                    }
                )
            yield json.dumps({"type": "sources", "sources": sources}) + "\n"

            # 3. Format Prompt
            chunks = [c for c, _ in chunks_with_scores]
            rag_prompt = prompt_service.format_prompt(
                "rag_answer",
                {"chunks": chunks, "question": question, "history": history},
            )

            # 4. Stream Answer
            full_raw_answer = ""
            async for text_chunk in llm_service.stream_chat_completion(rag_prompt):
                full_raw_answer += text_chunk
                yield json.dumps({"type": "answer_chunk", "content": text_chunk}) + "\n"

            # 5. Post-processing: Citation Verification & Hallucination Check
            verified_answer, verified_citations = citation_service.verify_and_clean(
                full_raw_answer, chunks
            )

            is_hallucination = False
            if check_hallucination:
                is_hallucination = await hallucination_service.check_hallucination(
                    verified_answer, chunks
                )

            # 6. Save Assistant Message
            if conversation_id and self.chat_service:
                await self.chat_service.save_message(
                    conversation_id,
                    "assistant",
                    verified_answer,
                    metadata={"citations": verified_citations},
                )

            yield (
                json.dumps(
                    {
                        "type": "final_verification",
                        "verified_answer": verified_answer,
                        "verified_citations": verified_citations,
                        "is_hallucination": is_hallucination,
                    }
                )
                + "\n"
            )

            yield json.dumps({"type": "done"}) + "\n"

        except Exception as e:
            logger.error(f"Error in RAG streaming pipeline: {e}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
