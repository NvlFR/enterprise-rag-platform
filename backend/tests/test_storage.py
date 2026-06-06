import io
import os

import pytest
from app.core.config import settings
from app.services.storage import storage_service


@pytest.mark.asyncio
async def test_storage_lifecycle():
    # Ensure we are using the test settings/bucket if needed,
    # but for now, we'll use what's in settings.

    # 1. Initialize bucket
    await storage_service.initialize_bucket()

    # 2. Upload file
    test_content = b"Hello, EKA storage!"
    test_file = io.BytesIO(test_content)
    test_key = "test/test-file.txt"

    s3_url = await storage_service.upload_file(
        test_file, test_key, content_type="text/plain"
    )
    assert s3_url == f"s3://{settings.S3_BUCKET}/{test_key}"

    # 3. Get pre-signed URL
    url = await storage_service.get_presigned_url(test_key)
    # In some environments, S3_ENDPOINT might be localhost or minio
    assert settings.S3_BUCKET in url
    assert "test-file.txt" in url

    # 4. Download file
    dest_path = "test_downloaded.txt"
    if os.path.exists(dest_path):
        os.remove(dest_path)

    await storage_service.download_file(test_key, dest_path)

    assert os.path.exists(dest_path)
    with open(dest_path, "rb") as f:
        content = f.read()
        assert content == test_content

    os.remove(dest_path)

    # 5. Delete file
    await storage_service.delete_file(test_key)


@pytest.mark.asyncio
async def test_storage_error_handling():
    # Try to download a non-existent file
    with pytest.raises(Exception):  # noqa: B017
        await storage_service.download_file(
            "non-existent-key.txt", "wont-be-created.txt"
        )
