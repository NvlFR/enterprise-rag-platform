from unittest.mock import MagicMock, patch

import pytest
from app.services.parser import parser_service


def test_parse_txt():
    content = b"Hello, world!"
    text = parser_service.parse(content, "txt")
    assert text == "Hello, world!"


def test_parse_unsupported():
    content = b"content"
    with pytest.raises(ValueError):
        parser_service.parse(content, "unknown")


def test_parse_pdf_structured(monkeypatch):
    # Mock elements returned by partition_pdf
    mock_title = MagicMock()
    mock_title.category = "Title"
    mock_title.text = "Doc Title"

    mock_table = MagicMock()
    mock_table.category = "Table"
    mock_table.text = "table text"
    mock_table.metadata.text_as_html = "<table></table>"

    mock_elements = [mock_title, mock_table]

    # Mock partition_pdf where it is used
    with patch("app.services.parser.partition_pdf", return_value=mock_elements):
        result = parser_service.parse_pdf(b"fake pdf")
        assert "# Doc Title" in result
        assert "[Table]" in result
        assert "<table></table>" in result
