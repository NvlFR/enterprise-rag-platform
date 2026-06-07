# ruff: noqa: E501
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.services.citation import citation_service
from app.services.hallucination import hallucination_service
from app.services.llm import llm_service
from app.services.prompt import prompt_service
from app.services.retrieval import RetrievalService

logger = logging.getLogger(__name__)


class RAGService:
    """Orchestrator for the RAG pipeline."""

    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval_service = retrieval_service

    async def generate_answer(
        self,
        question: str,
        top_k: int = 5,
        filters: dict | None = None,
        rephrase: bool = False,
        rerank: bool = True,
        context_window: int = 0,
        check_hallucination: bool = False,
    ) -> dict[str, Any]:
        """
        Execute the full RAG flow to answer a question.
        """
        try:
            search_query = question

            # 1. Query Rephrasing (Optional)
            if rephrase:
                rephrase_prompt = prompt_service.format_prompt(
                    "query_rephraser", {"question": question}
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
                return {
                    "answer": "I don.t have enough information to answer this question.",  # noqa: E501
                    "sources": [],
                    "verified_citations": [],
                    "is_hallucination": False,
                }

            # 3. Format Prompt
            chunks = [c for c, _ in chunks_with_scores]
            rag_prompt = prompt_service.format_prompt(
                "rag_answer", {"chunks": chunks, "question": question}
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

            # 7. Prepare Response
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
    ) -> AsyncIterator[str]:
        """
        Execute the full RAG flow and stream the answer.
        Yields JSON strings for each chunk of the response.
        """
        try:
            search_query = question

            # 1. Query Rephrasing
            if rephrase:
                rephrase_prompt = prompt_service.format_prompt(
                    "query_rephraser", {"question": question}
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
                yield (
                    json.dumps(
                        {
                            "type": "answer",
                            "content": "I don.t have enough information to answer this question.",  # noqa: E501
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
                "rag_answer", {"chunks": chunks, "question": question}
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
