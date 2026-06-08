import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk


class VectorRepository:
    """Repository for managing document chunks and their vector embeddings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chunk(
        self,
        document_id: uuid.UUID,
        content: str,
        embedding: list[float],
        chunk_index: int,
        metadata: dict | None = None,
    ) -> DocumentChunk:
        """Create a new document chunk."""
        db_chunk = DocumentChunk(
            document_id=document_id,
            content=content,
            embedding=embedding,
            chunk_index=chunk_index,
            chunk_metadata=metadata,
        )
        self.db.add(db_chunk)
        return db_chunk

    async def create_chunks_batch(self, chunks: list[DocumentChunk]) -> None:
        """Create multiple document chunks in a single batch."""
        self.db.add_all(chunks)

    async def get_chunks_by_document(
        self, document_id: uuid.UUID
    ) -> list[DocumentChunk]:
        """Retrieve all chunks for a specific document."""
        result = await self.db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def delete_chunks_by_document(self, document_id: uuid.UUID) -> None:
        """Delete all chunks associated with a document."""
        await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )

    async def search_similar_chunks(
        self,
        query_embedding: list[float],
        limit: int = 5,
        filters: dict | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search for chunks similar to the query embedding, with optional filtering.
        Returns a list of (chunk, score) tuples.
        Score is calculated as 1 - cosine_distance.
        """
        distance_col = DocumentChunk.embedding.cosine_distance(query_embedding).label(
            "distance"
        )
        stmt = select(DocumentChunk, distance_col).order_by(distance_col).limit(limit)

        if filters:
            for key, value in filters.items():
                if key == "document_id":
                    stmt = stmt.where(DocumentChunk.document_id == value)
                else:
                    stmt = stmt.where(
                        DocumentChunk.chunk_metadata[key].astext == str(value)
                    )

        result = await self.db.execute(stmt)
        # Convert distance to similarity score (1 - distance)
        return [(row[0], 1.0 - float(row[1])) for row in result.all()]

    async def search_by_keywords(
        self,
        query: str,
        limit: int = 5,
        filters: dict | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for chunks using keyword-based full text search."""
        ts_query = func.websearch_to_tsquery("english", query)
        rank_col = func.ts_rank(DocumentChunk.tsv_content, ts_query).label("rank")
        stmt = (
            select(DocumentChunk, rank_col)
            .where(DocumentChunk.tsv_content.op("@@")(ts_query))
            .order_by(rank_col.desc())
            .limit(limit)
        )

        if filters:
            for key, value in filters.items():
                if key == "document_id":
                    stmt = stmt.where(DocumentChunk.document_id == value)
                else:
                    stmt = stmt.where(
                        DocumentChunk.chunk_metadata[key].astext == str(value)
                    )

        result = await self.db.execute(stmt)
        return [(row[0], float(row[1])) for row in result.all()]

    async def get_context_window(
        self, document_id: uuid.UUID, chunk_index: int, window_size: int = 1
    ) -> list[DocumentChunk]:
        """
        Fetch a window of chunks surrounding a specific chunk index.
        """
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .where(DocumentChunk.chunk_index >= chunk_index - window_size)
            .where(DocumentChunk.chunk_index <= chunk_index + window_size)
            .order_by(DocumentChunk.chunk_index)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_chunk(self, chunk_id: uuid.UUID) -> DocumentChunk | None:
        """Retrieve a specific chunk by ID."""
        result = await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.id == chunk_id)
        )
        return result.scalar_one_or_none()
