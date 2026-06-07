from abc import ABC, abstractmethod


class BaseEmbeddingService(ABC):
    """Abstract base class for all embedding services."""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of document strings.

        Args:
            texts: A list of strings to embed.

        Returns:
            A list of embedding vectors (list of floats).
        """
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query string.

        Args:
            text: A string to embed.

        Returns:
            An embedding vector (list of floats).
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """The dimensionality of the embeddings produced by this service."""
        pass
