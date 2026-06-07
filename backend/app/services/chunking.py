import logging

from langchain_core.embeddings import Embeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.embedding import embedding_service
from app.services.embedding.base import BaseEmbeddingService

logger = logging.getLogger(__name__)


class LangChainEmbeddingAdapter(Embeddings):
    """Adapter to make BaseEmbeddingService compatible with LangChain."""

    def __init__(self, service: BaseEmbeddingService):
        self.service = service

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import asyncio

        return asyncio.run(self.service.embed_documents(texts))

    def embed_query(self, text: str) -> list[float]:
        import asyncio

        return asyncio.run(self.service.embed_query(text))


class ChunkingService:
    """Service for splitting text into smaller chunks for embedding."""

    def __init__(
        self,
        strategy: str = "recursive",  # "recursive" or "semantic"
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_provider: BaseEmbeddingService | None = None,
    ):
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Recursive Splitter
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

        # Semantic Splitter (Lazy initialized)
        self._semantic_splitter = None
        self._embedding_provider = embedding_provider or embedding_service

    @property
    def semantic_splitter(self):
        if self._semantic_splitter is None:
            try:
                adapter = LangChainEmbeddingAdapter(self._embedding_provider)
                self._semantic_splitter = SemanticChunker(
                    adapter, breakpoint_threshold_type="percentile"
                )
            except Exception as e:
                logger.error(f"Failed to initialize SemanticChunker: {e}")
                # We return None and split_text will handle the fallback
                return None
        return self._semantic_splitter

    def split_text(self, text: str, strategy: str | None = None) -> list[str]:
        """Splits a single string into a list of chunks based on selected strategy."""
        strategy = strategy or self.strategy
        try:
            if strategy == "semantic":
                splitter = self.semantic_splitter
                if splitter:
                    return splitter.split_text(text)
                else:
                    logger.warning(
                        "Semantic splitter not available, falling back to recursive."
                    )
                    return self.recursive_splitter.split_text(text)
            else:
                return self.recursive_splitter.split_text(text)
        except Exception as e:
            logger.error(f"Error splitting text with {strategy} strategy: {e}")
            # Fallback to recursive if semantic fails
            if strategy == "semantic":
                logger.warning("Semantic splitting failed, falling back to recursive.")
                return self.recursive_splitter.split_text(text)
            raise

    def create_chunks_with_metadata(
        self, text: str, metadata: dict | None = None, strategy: str | None = None
    ) -> list[dict]:
        """
        Splits text and returns a list of dictionaries containing
        the chunk text and associated metadata.
        """
        chunks = self.split_text(text, strategy=strategy)
        result = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = (metadata or {}).copy()
            chunk_metadata["chunk_index"] = i
            result.append({"content": chunk, "metadata": chunk_metadata})
        return result


chunking_service = ChunkingService()
