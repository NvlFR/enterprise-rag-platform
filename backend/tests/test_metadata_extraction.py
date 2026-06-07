from app.services.metadata import metadata_service


def test_extract_metadata_basic():
    text = """EKA - Enterprise Knowledge Assistant
    This is an enterprise knowledge assistant document.
    It is useful for knowledge management in the enterprise.
    """
    metadata = metadata_service.extract(text)

    assert metadata["title"] == "EKA - Enterprise Knowledge Assistant"
    assert metadata["language"] == "en"
    assert "enterprise" in metadata["keywords"]
    assert "knowledge" in metadata["keywords"]
    assert "assistant" in metadata["keywords"]


def test_extract_metadata_empty():
    text = ""
    metadata = metadata_service.extract(text)

    assert metadata["title"] == "Untitled Document"
    assert metadata["language"] == "en"
    assert metadata["keywords"] == []


def test_extract_metadata_other_language():
    text_non_ascii = "Désolé, ceci est en français."
    metadata_non_ascii = metadata_service.extract(text_non_ascii)
    assert metadata_non_ascii["language"] == "other"
