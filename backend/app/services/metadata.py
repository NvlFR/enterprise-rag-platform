import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)


class MetadataService:
    """Service untuk ekstraksi metadata dokumen."""

    def extract(self, text: str) -> dict:
        """Ekstrak title, language (basic), dan keywords dari teks."""
        metadata = {
            "title": "Untitled Document",
            "language": "en",
            "keywords": [],
        }

        if not text:
            return metadata

        # 1. Extract Title (First non-empty line, max 100 chars)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if lines:
            metadata["title"] = lines[0][:100]

        # 2. Basic language detection (Simple check for non-ASCII)
        # Note: For production, consider 'langdetect' or 'nltk'
        if any(ord(c) > 127 for c in text[:1000]):
            metadata["language"] = "other"
        else:
            metadata["language"] = "en"

        # 3. Extract Keywords (Simple frequency-based, ignoring short words)
        words = re.findall(r"\b\w{5,}\b", text.lower())
        stop_words = {"the", "and", "that", "this", "with", "from", "their"}
        filtered_words = [word for word in words if word not in stop_words]

        counts = Counter(filtered_words)
        metadata["keywords"] = [word for word, count in counts.most_common(10)]

        return metadata


metadata_service = MetadataService()
