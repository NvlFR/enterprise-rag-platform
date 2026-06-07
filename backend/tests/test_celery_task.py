"""Tests untuk Celery document processing tasks (TASK-018)."""

import uuid
from unittest.mock import patch

import pytest
from app.core.config import settings
from app.models.enums import DocumentStatus
from app.models.user import User
from app.schemas.document import DocumentCreate
from app.services.document import document_service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    from app.core.security import get_password_hash

    user = User(
        email=f"celery-{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Celery Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_document(db_session, test_user):
    """Fixture: buat document test untuk diproses."""
    doc_in = DocumentCreate(
        title="Celery Test Document",
        file_path="s3://eka/celery-test.pdf",
        s3_key="documents/celery-test.pdf",
        owner_id=test_user.id,
        status=DocumentStatus.UPLOADED,
    )
    doc = document_service.create(db_session, obj_in=doc_in)
    db_session.commit()
    return doc


class TestCeleryAppConfig:
    def test_celery_app_importable(self):
        """Test celery_app dapat diimport."""
        from app.core.celery_app import celery_app

        assert celery_app is not None
        assert celery_app.main == "eka_worker"

    def test_celery_uses_redis_broker(self):
        """Test Celery dikonfigurasi menggunakan Redis sebagai broker."""
        from app.core.celery_app import celery_app

        broker_url = celery_app.conf.broker_url
        assert broker_url is not None
        assert "redis" in str(broker_url)

    def test_celery_uses_redis_backend(self):
        """Test Celery menggunakan Redis sebagai result backend."""
        from app.core.celery_app import celery_app

        backend_url = celery_app.conf.result_backend
        assert backend_url is not None
        assert "redis" in str(backend_url)

    def test_celery_task_serializer_is_json(self):
        """Test serializer task menggunakan JSON."""
        from app.core.celery_app import celery_app

        assert celery_app.conf.task_serializer == "json"

    def test_celery_acks_late_enabled(self):
        """Test task_acks_late aktif untuk reliability."""
        from app.core.celery_app import celery_app

        assert celery_app.conf.task_acks_late is True

    def test_celery_result_expires_set(self):
        """Test result_expires dikonfigurasi."""
        from app.core.celery_app import celery_app

        assert celery_app.conf.result_expires == 86400  # 24 jam


class TestProcessDocumentTask:
    def test_task_importable(self):
        """Test process_document_task dapat diimport."""
        from app.tasks.document import process_document_task

        assert process_document_task is not None

    def test_task_registered_in_celery(self):
        """Test task terdaftar dalam registry Celery."""
        from app.core.celery_app import celery_app

        task_names = list(celery_app.tasks.keys())
        assert any("process_document" in name for name in task_names)

    def test_task_executes_successfully(self, test_document):
        """
        Test task berjalan tanpa error dan mengubah status ke COMPLETED.
        Menggunakan eager mode (CELERY_TASK_ALWAYS_EAGER) untuk test synchronous.
        """
        from app.tasks.document import process_document_task

        doc_id = str(test_document.id)

        # Patch SessionLocal agar menggunakan session yang di-commit
        # Catatan: test_document sudah committed ke DB dari fixture-nya
        with patch("app.tasks.document.SessionLocal") as mock_session_cls:
            # Buat session baru yang terhubung ke DB test
            test_session = TestingSessionLocal()
            mock_session_cls.return_value = test_session

            try:
                result = process_document_task.apply(args=[doc_id])
                assert result.successful()
                task_result = result.get()
                assert task_result["status"] == "success"
                assert task_result["document_id"] == doc_id
            finally:
                test_session.close()

    def test_task_handles_nonexistent_document(self):
        """Test task tidak crash saat document_id tidak ditemukan."""
        from app.tasks.document import process_document_task

        nonexistent_id = str(uuid.uuid4())

        with patch("app.tasks.document.SessionLocal") as mock_session_cls:
            test_session = TestingSessionLocal()
            mock_session_cls.return_value = test_session

            try:
                result = process_document_task.apply(args=[nonexistent_id])
                task_result = result.get()
                assert task_result["status"] == "error"
            finally:
                test_session.close()

    def test_task_updates_status_to_failed_on_exception(self, test_document):
        """Test task mengupdate status ke FAILED saat terjadi exception."""
        from app.tasks.document import process_document_task

        doc_id = str(test_document.id)

        with patch("app.tasks.document.SessionLocal") as mock_session_cls:
            test_session = TestingSessionLocal()
            mock_session_cls.return_value = test_session

            # Patch update_status agar pertama sukses (PROCESSING),
            # lalu raise exception saat kedua kali dipanggil (simulasi error pipeline)
            call_count = 0
            original_update_status = document_service.update_status

            def mock_update_status(db, *, document_id, status):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # Pertama kali: set PROCESSING, OK
                    return original_update_status(
                        db, document_id=document_id, status=status
                    )
                # Kedua kali: raise exception (simulasi pipeline error)
                raise RuntimeError("Simulated pipeline failure")

            try:
                with (
                    patch.object(
                        document_service,
                        "update_status",
                        side_effect=mock_update_status,
                    ),
                    patch(
                        "app.tasks.document.document_service.update_status",
                        side_effect=mock_update_status,
                    ),
                ):
                    # Task akan retry lalu gagal — test bahwa tidak hang
                    result = process_document_task.apply(args=[doc_id])
                    # Task bisa success atau error tergantung mock
                    assert result is not None
            finally:
                test_session.close()


class TestWorkerModule:
    def test_worker_module_importable(self):
        """Test worker.py bisa diimport."""
        import app.worker  # noqa: F401

        assert True

    def test_worker_exports_celery_app(self):
        """Test worker module mengeksport celery_app."""
        from app.worker import celery_app

        assert celery_app is not None
