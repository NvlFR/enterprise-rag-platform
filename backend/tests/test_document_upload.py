"""Integration tests untuk Document Upload API (TASK-017)."""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core import security
from app.core.config import settings
from app.models.enums import DocumentStatus
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def test_user(db: Session) -> User:
    """Fixture: buat user test dengan password."""
    email = f"docupload-{uuid.uuid4()}@example.com"
    password = "testpassword123"  # noqa: S105
    user = User(
        email=email,
        hashed_password=security.get_password_hash(password),
        full_name="Upload Test User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user.plain_password = password
    return user


@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict:
    """Fixture: dapatkan auth headers untuk test_user."""
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": test_user.email, "password": test_user.plain_password},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ========== Tests untuk file upload endpoint ==========


class TestDocumentUpload:
    """Tests untuk POST /api/v1/documents."""

    def test_upload_pdf_success(self, client: TestClient, auth_headers: dict):
        """Test upload PDF berhasil mengembalikan 201 dengan document record."""
        pdf_content = b"%PDF-1.4 test content"
        with (
            patch(
                "app.api.v1.endpoints.documents.storage_service.upload_file",
                new_callable=AsyncMock,
            ) as mock_upload,
            patch(
                "app.api.v1.endpoints.documents.process_document_task.delay"
            ) as mock_task,
        ):
            mock_upload.return_value = "s3://eka-documents/test.pdf"
            mock_task.return_value = MagicMock(id="task-123")

            r = client.post(
                f"{settings.API_V1_STR}/documents",
                headers=auth_headers,
                files={
                    "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")
                },
            )

        assert r.status_code == 201
        data = r.json()
        assert "id" in data
        assert data["title"] == "test.pdf"
        assert data["status"] == DocumentStatus.UPLOADED.value
        assert mock_task.called

    def test_upload_docx_success(self, client: TestClient, auth_headers: dict):
        """Test upload DOCX berhasil."""
        docx_content = b"PK docx content"
        docx_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        with (
            patch(
                "app.api.v1.endpoints.documents.storage_service.upload_file",
                new_callable=AsyncMock,
            ),
            patch("app.api.v1.endpoints.documents.process_document_task.delay"),
        ):
            r = client.post(
                f"{settings.API_V1_STR}/documents",
                headers=auth_headers,
                files={"file": ("document.docx", io.BytesIO(docx_content), docx_type)},
            )

        assert r.status_code == 201

    def test_upload_txt_success(self, client: TestClient, auth_headers: dict):
        """Test upload TXT berhasil."""
        txt_content = b"Plain text document content."

        with (
            patch(
                "app.api.v1.endpoints.documents.storage_service.upload_file",
                new_callable=AsyncMock,
            ),
            patch("app.api.v1.endpoints.documents.process_document_task.delay"),
        ):
            r = client.post(
                f"{settings.API_V1_STR}/documents",
                headers=auth_headers,
                files={"file": ("readme.txt", io.BytesIO(txt_content), "text/plain")},
            )

        assert r.status_code == 201

    def test_upload_invalid_filetype_rejected(
        self, client: TestClient, auth_headers: dict
    ):
        """Test upload file dengan tipe tidak valid direjek dengan 400."""
        r = client.post(
            f"{settings.API_V1_STR}/documents",
            headers=auth_headers,
            files={
                "file": (
                    "malicious.exe",
                    io.BytesIO(b"MZ exe content"),
                    "application/octet-stream",
                )
            },
        )
        assert r.status_code == 400
        assert (
            "tidak diizinkan" in r.json()["detail"].lower()
            or "allowed" in r.json()["detail"].lower()
        )

    def test_upload_image_rejected(self, client: TestClient, auth_headers: dict):
        """Test upload gambar direjek."""
        r = client.post(
            f"{settings.API_V1_STR}/documents",
            headers=auth_headers,
            files={
                "file": ("photo.jpg", io.BytesIO(b"\xff\xd8\xff image"), "image/jpeg")
            },
        )
        assert r.status_code == 400

    def test_upload_requires_authentication(self, client: TestClient):
        """Test upload tanpa auth token mengembalikan 401/403."""
        r = client.post(
            f"{settings.API_V1_STR}/documents",
            files={"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")},
        )
        assert r.status_code in [401, 403]

    def test_upload_creates_db_record_with_metadata(
        self, client: TestClient, auth_headers: dict
    ):
        """Test upload menyimpan metadata file di JSONB field."""
        pdf_content = b"%PDF-1.4 test"

        with (
            patch(
                "app.api.v1.endpoints.documents.storage_service.upload_file",
                new_callable=AsyncMock,
            ),
            patch("app.api.v1.endpoints.documents.process_document_task.delay"),
        ):
            r = client.post(
                f"{settings.API_V1_STR}/documents",
                headers=auth_headers,
                files={
                    "file": (
                        "my_policy.pdf",
                        io.BytesIO(pdf_content),
                        "application/pdf",
                    )
                },
            )

        assert r.status_code == 201
        data = r.json()
        # metadata harus berisi info file
        assert data.get("doc_metadata") is not None
        assert data["doc_metadata"]["original_filename"] == "my_policy.pdf"
        assert data["doc_metadata"]["content_type"] == "application/pdf"


class TestDocumentList:
    """Tests untuk GET /api/v1/documents."""

    def test_list_documents_empty(self, client: TestClient, auth_headers: dict):
        """Test list dokumen saat belum ada dokumen."""
        r = client.get(f"{settings.API_V1_STR}/documents", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_documents_after_upload(self, client: TestClient, auth_headers: dict):
        """Test list menampilkan dokumen yang sudah diupload."""
        pdf_content = b"%PDF-1.4"

        with (
            patch(
                "app.api.v1.endpoints.documents.storage_service.upload_file",
                new_callable=AsyncMock,
            ),
            patch("app.api.v1.endpoints.documents.process_document_task.delay"),
        ):
            upload_r = client.post(
                f"{settings.API_V1_STR}/documents",
                headers=auth_headers,
                files={
                    "file": ("listed.pdf", io.BytesIO(pdf_content), "application/pdf")
                },
            )

        assert upload_r.status_code == 201
        doc_id = upload_r.json()["id"]

        # List dokumen
        list_r = client.get(f"{settings.API_V1_STR}/documents", headers=auth_headers)
        assert list_r.status_code == 200
        ids = [d["id"] for d in list_r.json()]
        assert doc_id in ids


class TestDocumentGet:
    """Tests untuk GET /api/v1/documents/{id}."""

    def test_get_own_document(self, client: TestClient, auth_headers: dict):
        """Test mendapatkan dokumen milik sendiri."""
        pdf_content = b"%PDF-1.4"

        with (
            patch(
                "app.api.v1.endpoints.documents.storage_service.upload_file",
                new_callable=AsyncMock,
            ),
            patch("app.api.v1.endpoints.documents.process_document_task.delay"),
        ):
            upload_r = client.post(
                f"{settings.API_V1_STR}/documents",
                headers=auth_headers,
                files={
                    "file": ("getme.pdf", io.BytesIO(pdf_content), "application/pdf")
                },
            )

        doc_id = upload_r.json()["id"]
        r = client.get(
            f"{settings.API_V1_STR}/documents/{doc_id}", headers=auth_headers
        )
        assert r.status_code == 200
        assert r.json()["id"] == doc_id

    def test_get_nonexistent_document_returns_404(
        self, client: TestClient, auth_headers: dict
    ):
        """Test akses dokumen yang tidak ada mengembalikan 404."""
        r = client.get(
            f"{settings.API_V1_STR}/documents/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert r.status_code == 404
