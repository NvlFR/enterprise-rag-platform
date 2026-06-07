from unittest.mock import patch

import pytest
from app.services.embedding import get_embedding_service
from app.services.embedding.mock import MockEmbeddingService


@pytest.mark.asyncio
async def test_mock_embedding_service():
    dimension = 128
    service = MockEmbeddingService(dimension=dimension)

    assert service.dimension == dimension

    texts = ["text1", "text2", "longer text three"]
    embeddings = await service.embed_documents(texts)

    assert len(embeddings) == 3
    assert all(len(emb) == dimension for emb in embeddings)
    assert isinstance(embeddings[0][0], float)

    query_emb = await service.embed_query("query")
    assert len(query_emb) == dimension


def test_embedding_factory():
    with patch("app.core.config.settings.EMBEDDING_PROVIDER", "mock"):
        with patch("app.core.config.settings.DEFAULT_VECTOR_DIMENSION", 1536):
            service = get_embedding_service()
            assert isinstance(service, MockEmbeddingService)
            assert service.dimension == 1536


def test_embedding_factory_unsupported():
    with patch("app.core.config.settings.EMBEDDING_PROVIDER", "unsupported_provider"):
        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            get_embedding_service()
