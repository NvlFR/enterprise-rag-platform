import asyncio
import logging

from app.models.chunk import DocumentChunk
from app.repositories.vector_repository import VectorRepository
from app.services.embedding import embedding_service
from app.services.reranking import reranking_service

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for performing semantic and hybrid retrieval."""

    def __init__(self, vector_repository: VectorRepository):
        self.repository = vector_repository

    async def search_vectors(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
        filters: dict | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Perform a semantic similarity search.
        Returns a list of (chunk, score) tuples.
        """
        try:
            # 1. Vectorize query
            query_embedding = await embedding_service.embed_query(query)

            # 2. Search repository
            results = await self.repository.search_similar_chunks(
                query_embedding=query_embedding, limit=top_k, filters=filters
            )

            # 3. Filter by threshold
            if threshold > 0:
                results = [res for res in results if res[1] >= threshold]

            return results
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            raise

    async def search_keywords(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Perform a keyword-based search."""
        try:
            return await self.repository.search_by_keywords(
                query=query, limit=top_k, filters=filters
            )
        except Exception as e:
            logger.error(f"Error during keyword search: {e}")
            raise

    async def expand_context(
        self,
        chunks_with_scores: list[tuple[DocumentChunk, float]],
        window_size: int = 1,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        For each chunk, retrieve surrounding chunks and merge them.
        Returns unique chunks, with original scores maintained where possible.
        """
        if not chunks_with_scores or window_size == 0:
            return chunks_with_scores

        expanded_results = {}  # Map chunk_id to {chunk, score}

        # To avoid fetching same window multiple times
        fetched_windows = set()

        for original_chunk, score in chunks_with_scores:
            window_key = (original_chunk.document_id, original_chunk.chunk_index)
            if window_key in fetched_windows:
                continue

            # Fetch surrounding chunks
            window_chunks = await self.repository.get_context_window(
                document_id=original_chunk.document_id,
                chunk_index=original_chunk.chunk_index,
                window_size=window_size,
            )

            for chunk in window_chunks:
                chunk_id = str(chunk.id)
                # If chunk is already in results, keep the highest score
                if chunk_id in expanded_results:
                    expanded_results[chunk_id]["score"] = max(
                        expanded_results[chunk_id]["score"], score
                    )
                else:
                    # Chunks that are just "context" get a slightly lower score
                    # than the matching chunk if they weren't in the original result set
                    is_original = any(
                        str(c[0].id) == chunk_id for c in chunks_with_scores
                    )
                    expanded_results[chunk_id] = {
                        "chunk": chunk,
                        "score": score if is_original else score * 0.9,
                    }

            fetched_windows.add(window_key)

        # Return sorted by score
        sorted_expanded = sorted(
            expanded_results.values(), key=lambda x: x["score"], reverse=True
        )
        return [(res["chunk"], res["score"]) for res in sorted_expanded]

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
        rrf_k: int = 60,
        rerank: bool = True,
        context_window: int = 0,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Combine vector and keyword search using Reciprocal Rank Fusion (RRF),
        optionally rerank, and optionally expand context window.
        """
        try:
            # 1. Initial retrieval
            fetch_k = top_k * 5 if rerank else top_k * 2

            vector_task = self.search_vectors(query, top_k=fetch_k, filters=filters)
            keyword_task = self.search_keywords(query, top_k=fetch_k, filters=filters)

            vector_results, keyword_results = await asyncio.gather(
                vector_task, keyword_task
            )

            # 2. Reciprocal Rank Fusion
            rrf_scores = {}
            for rank, (chunk, _) in enumerate(vector_results, start=1):
                cid = str(chunk.id)
                if cid not in rrf_scores:
                    rrf_scores[cid] = {"chunk": chunk, "score": 0.0}
                rrf_scores[cid]["score"] += 1.0 / (rrf_k + rank)

            for rank, (chunk, _) in enumerate(keyword_results, start=1):
                cid = str(chunk.id)
                if cid not in rrf_scores:
                    rrf_scores[cid] = {"chunk": chunk, "score": 0.0}
                rrf_scores[cid]["score"] += 1.0 / (rrf_k + rank)

            sorted_candidates = sorted(
                rrf_scores.values(), key=lambda x: x["score"], reverse=True
            )

            num_candidates = top_k * 2 if rerank else top_k
            candidate_dicts = sorted_candidates[:num_candidates]

            if not candidate_dicts:
                return []

            # 3. Reranking
            final_results = []
            if rerank:
                candidates = [res["chunk"] for res in candidate_dicts]
                final_results = await reranking_service.rerank(query, candidates)
                final_results = final_results[:top_k]
            else:
                final_results = [
                    (res["chunk"], res["score"]) for res in candidate_dicts[:top_k]
                ]

            # 4. Context Window Expansion
            if context_window > 0:
                final_results = await self.expand_context(
                    final_results, window_size=context_window
                )

            return final_results

        except Exception as e:
            logger.error(f"Error during hybrid search: {e}")
            raise
