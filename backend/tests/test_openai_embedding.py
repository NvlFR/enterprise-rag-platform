from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.embedding.openai import OpenAIEmbeddingService


@pytest.mark.asyncio
async def test_openai_embedding_service():
    mock_client = MagicMock()
    mock_embeddings = MagicMock()
    mock_client.embeddings = mock_embeddings

    # Mock response for create
    mock_response = MagicMock()
    mock_data1 = MagicMock()
    mock_data1.embedding = [0.1, 0.2]
    mock_data2 = MagicMock()
    mock_data2.embedding = [0.3, 0.4]
    mock_response.data = [mock_data1, mock_data2]

    mock_embeddings.create = AsyncMock(return_value=mock_response)

    with patch("app.services.embedding.openai.AsyncOpenAI", return_value=mock_client):
        service = OpenAIEmbeddingService(model="text-embedding-3-small", dimension=2)

        texts = ["hello", "world"]
        embeddings = await service.embed_documents(texts)

        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2]
        assert embeddings[1] == [0.3, 0.4]

        # Verify call arguments
        mock_embeddings.create.assert_called_with(
            input=["hello", "world"], model="text-embedding-3-small", dimensions=2
        )


@pytest.mark.asyncio
async def test_openai_embed_query():
    mock_client = MagicMock()
    mock_embeddings = MagicMock()
    mock_client.embeddings = mock_embeddings

    mock_response = MagicMock()
    mock_data = MagicMock()
    mock_data.embedding = [0.5, 0.6]
    mock_response.data = [mock_data]

    mock_embeddings.create = AsyncMock(return_value=mock_response)

    with patch("app.services.embedding.openai.AsyncOpenAI", return_value=mock_client):
        service = OpenAIEmbeddingService(model="text-embedding-3-small", dimension=2)

        embedding = await service.embed_query("test query")

        assert embedding == [0.5, 0.6]
        mock_embeddings.create.assert_called_with(
            input=["test query"], model="text-embedding-3-small", dimensions=2
        )
