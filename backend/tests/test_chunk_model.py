import uuid

from app.core.config import settings
from app.models.chunk import DocumentChunk


def test_document_chunk_model():
    doc_id = uuid.uuid4()
    embedding = [0.1] * settings.DEFAULT_VECTOR_DIMENSION
    chunk = DocumentChunk(
        document_id=doc_id,
        content="Test content",
        embedding=embedding,
        chunk_index=0,
        chunk_metadata={"page": 1},
    )

    assert chunk.document_id == doc_id
    assert chunk.content == "Test content"
    assert len(chunk.embedding) == settings.DEFAULT_VECTOR_DIMENSION
    assert chunk.chunk_index == 0
    assert chunk.chunk_metadata == {"page": 1}
