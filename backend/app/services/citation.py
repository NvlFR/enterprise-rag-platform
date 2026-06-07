import logging
import re
from typing import Any

from app.models.chunk import DocumentChunk

logger = logging.getLogger(__name__)


class CitationService:
    """Service for parsing and verifying citations in LLM responses."""

    def __init__(self, citation_regex: str = r"\[(\d+)\]"):
        self.citation_pattern = re.compile(citation_regex)

    def extract_citations(self, text: str) -> set[int]:
        """Extract all numerical indices from citations like [1], [2]."""
        matches = self.citation_pattern.findall(text)
        return {int(m) for m in matches}

    def verify_and_clean(
        self, text: str, chunks: list[DocumentChunk]
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Verify citations against provided chunks and return cleaned text
        and source attribution list.
        """
        cited_indices = self.extract_citations(text)
        valid_indices = set(range(1, len(chunks) + 1))

        # 1. Identify hallucinated citations
        hallucinated = cited_indices - valid_indices
        if hallucinated:
            logger.warning(f"Removing hallucinated citations: {hallucinated}")
            # Remove hallucinated citations from text
            for idx in hallucinated:
                text = text.replace(f"[{idx}]", "")

        # 2. Get unique valid cited chunks
        final_cited_indices = cited_indices & valid_indices

        # 3. Build source attribution list (preserving order of appearance)
        # We also want to map document_id to unique documents to avoid repeating sources
        unique_sources = {}
        for idx in sorted(final_cited_indices):
            chunk = chunks[idx - 1]
            doc_id = str(chunk.document_id)
            if doc_id not in unique_sources:
                unique_sources[doc_id] = {
                    "document_id": doc_id,
                    "title": chunk.chunk_metadata.get("title", "Unknown Document"),
                    "citations": [],
                }
            unique_sources[doc_id]["citations"].append(idx)

        return text, list(unique_sources.values())


citation_service = CitationService()
