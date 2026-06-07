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


# We can add more tests for PDF/DOCX if we have sample files.
