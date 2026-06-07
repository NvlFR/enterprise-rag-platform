# ruff: noqa: E501
import io
import logging

from docx import Document as DocxDocument
from unstructured.partition.pdf import partition_pdf

logger = logging.getLogger(__name__)


class ParserService:
    """Service untuk ekstraksi teks dari berbagai format dokumen."""

    def parse_pdf(self, file_content: bytes) -> str:
        """Ekstraksi teks dari PDF menggunakan unstructured untuk layout dan table handling."""  # noqa: E501
        text = ""
        try:
            # Create a file-like object for unstructured
            file_obj = io.BytesIO(file_content)

            # Use high-res strategy for table and layout inference
            elements = partition_pdf(
                file=file_obj,
                strategy="hi_res",
                infer_table_structure=True,
                chunking_strategy=None,  # We handle chunking later
            )

            # Combine elements with better layout awareness
            for element in elements:
                category = element.category

                if category == "Title":
                    text += f"\n# {element.text}\n"
                elif category == "Header":
                    text += f"\n## {element.text}\n"
                elif category == "Subheadline":
                    text += f"\n### {element.text}\n"
                elif category == "Table":
                    # Extract HTML representation if available for better structure
                    html_table = getattr(element.metadata, "text_as_html", None)
                    if html_table:
                        text += f"\n[Table]\n{html_table}\n[/Table]\n"
                    else:
                        # Fallback to plain text if HTML structure is missing
                        text += f"\n[Table]\n{element.text}\n[/Table]\n"
                elif category in ["Footer", "PageNumber"]:
                    # Skip footers and page numbers to avoid noise in RAG
                    continue
                else:
                    # Default handling for NarrativeText, ListItem, etc.
                    text += f"\n{element.text}"

        except Exception as e:
            logger.error(f"Error parsing PDF with unstructured: {e}")
            raise
        return text.strip()

    def parse_docx(self, file_content: bytes) -> str:
        """Ekstraksi teks dari DOCX."""
        text = ""
        try:
            doc = DocxDocument(io.BytesIO(file_content))
            text = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error parsing DOCX: {e}")
            raise
        return text

    def parse_txt(self, file_content: bytes) -> str:
        """Ekstraksi teks dari TXT."""
        try:
            return file_content.decode("utf-8")
        except Exception as e:
            logger.error(f"Error parsing TXT: {e}")
            raise

    def parse(self, file_content: bytes, file_type: str) -> str:
        """Entry point untuk parsing berdasarkan file type."""
        if file_type == "pdf":
            return self.parse_pdf(file_content)
        elif file_type == "docx":
            return self.parse_docx(file_content)
        elif file_type == "txt":
            return self.parse_txt(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")


parser_service = ParserService()
