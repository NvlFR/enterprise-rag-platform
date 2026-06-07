import uuid
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base_class import Base

if TYPE_CHECKING:
    from .document import Document


class DocumentChunk(Base):
    """Model for storing document chunks and their vector embeddings."""

    __tablename__ = "document_chunk"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Dimension is configurable via settings, but we default to 1536 (OpenAI)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.DEFAULT_VECTOR_DIMENSION), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    # Full Text Search vector
    tsv_content: Mapped[Any] = mapped_column(TSVECTOR, nullable=True)

    document: Mapped["Document"] = relationship("Document")

    __table_args__ = (
        Index(
            "ix_document_chunk_embedding",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "ix_document_chunk_metadata",
            chunk_metadata,
            postgresql_using="gin",
        ),
        Index(
            "ix_document_chunk_tsv",
            tsv_content,
            postgresql_using="gin",
        ),
    )
