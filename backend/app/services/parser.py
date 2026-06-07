import io
import logging

import fitz  # PyMuPDF
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)


class ParserService:
    """Service untuk ekstraksi teks dari berbagai format dokumen."""

    def parse_pdf(self, file_content: bytes) -> str:
        """Ekstraksi teks dari PDF menggunakan PyMuPDF."""
        text = ""
        try:
            with fitz.open(stream=file_content, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text()
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise
        return text

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
