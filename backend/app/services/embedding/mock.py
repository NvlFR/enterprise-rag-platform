from app.services.embedding.base import BaseEmbeddingService


class MockEmbeddingService(BaseEmbeddingService):
    """A mock embedding service for testing that returns random or fixed vectors."""

    def __init__(self, dimension: int = 1536):
        self._dimension = dimension

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Return a list of pseudo-random vectors based on text length
        return [
            [float(len(text) + i) / 1000.0 for i in range(self._dimension)]
            for text in texts
        ]

    async def embed_query(self, text: str) -> list[float]:
        return [float(len(text) + i) / 1000.0 for i in range(self._dimension)]

    @property
    def dimension(self) -> int:
        return self._dimension
