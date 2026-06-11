"""Unit tests untuk DocumentService (TASK-016)."""

import uuid

import pytest
from app.core.config import settings
from app.models.enums import DocumentStatus
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services.document import DocumentService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Gunakan database yang sama dengan tests lain
SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Fixture database session dengan rollback otomatis."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    """Fixture: buat user test di database."""
    from app.core.security import get_password_hash

    user = User(
        email=f"doctest-{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Doc Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def doc_service() -> DocumentService:
    return DocumentService()


# ========== Tests TASK-016 ==========


class TestDocumentServiceCreate:
    def test_create_document_basic(self, db_session, test_user, doc_service):
        """Test membuat document baru dengan field dasar."""
        doc_in = DocumentCreate(
            title="Test Policy.pdf",
            file_path="s3://eka-documents/documents/test.pdf",
            s3_key="documents/test.pdf",
            owner_id=test_user.id,
            status=DocumentStatus.UPLOADED,
        )
        doc = doc_service.create(db_session, obj_in=doc_in)

        assert doc.id is not None
        assert doc.title == "Test Policy.pdf"
        assert doc.file_path == "s3://eka-documents/documents/test.pdf"
        assert doc.s3_key == "documents/test.pdf"
        assert doc.status == DocumentStatus.UPLOADED
        assert doc.owner_id == test_user.id
        assert doc.doc_metadata is None

    def test_create_document_with_metadata(self, db_session, test_user, doc_service):
        """Test membuat document dengan JSONB metadata."""
        metadata = {
            "original_filename": "SOP-HR-2024.pdf",
            "content_type": "application/pdf",
            "file_size_bytes": 1024000,
            "page_count": 25,
        }
        doc_in = DocumentCreate(
            title="SOP HR 2024",
            file_path="s3://eka-documents/documents/sop.pdf",
            s3_key="documents/sop.pdf",
            owner_id=test_user.id,
            doc_metadata=metadata,
        )
        doc = doc_service.create(db_session, obj_in=doc_in)

        assert doc.doc_metadata is not None
        assert doc.doc_metadata["original_filename"] == "SOP-HR-2024.pdf"
        assert doc.doc_metadata["page_count"] == 25
        assert doc.doc_metadata["file_size_bytes"] == 1024000

    def test_create_document_timestamps(self, db_session, test_user, doc_service):
        """Test bahwa timestamps created_at dan updated_at ter-set."""
        doc_in = DocumentCreate(
            title="Test Doc",
            file_path="s3://eka/test.pdf",
            owner_id=test_user.id,
        )
        doc = doc_service.create(db_session, obj_in=doc_in)

        assert doc.created_at is not None
        assert doc.updated_at is not None


class TestDocumentServiceGet:
    def test_get_existing_document(self, db_session, test_user, doc_service):
        """Test mengambil document berdasarkan ID."""
        doc_in = DocumentCreate(
            title="Retrievable Doc",
            file_path="s3://eka/retrieve.pdf",
            owner_id=test_user.id,
        )
        created = doc_service.create(db_session, obj_in=doc_in)

        fetched = doc_service.get(db_session, document_id=created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.title == "Retrievable Doc"

    def test_get_nonexistent_document(self, db_session, doc_service):
        """Test mengambil document yang tidak ada mengembalikan None."""
        result = doc_service.get(db_session, document_id=uuid.uuid4())
        assert result is None

    def test_get_by_owner(self, db_session, test_user, doc_service):
        """Test mengambil semua document milik owner tertentu."""
        # Buat 3 dokumen
        for i in range(3):
            doc_in = DocumentCreate(
                title=f"Doc {i}",
                file_path=f"s3://eka/doc{i}.pdf",
                owner_id=test_user.id,
            )
            doc_service.create(db_session, obj_in=doc_in)

        docs = doc_service.get_by_owner(db_session, owner_id=test_user.id)
        assert len(docs) >= 3
        assert all(d.owner_id == test_user.id for d in docs)

    def test_get_by_owner_empty(self, db_session, doc_service):
        """Test get_by_owner untuk user yang belum punya dokumen."""
        random_user_id = uuid.uuid4()
        docs = doc_service.get_by_owner(db_session, owner_id=random_user_id)
        assert docs == []


class TestDocumentServiceUpdate:
    def test_update_document_title(self, db_session, test_user, doc_service):
        """Test update judul dokumen."""
        doc_in = DocumentCreate(
            title="Old Title",
            file_path="s3://eka/old.pdf",
            owner_id=test_user.id,
        )
        doc = doc_service.create(db_session, obj_in=doc_in)

        update = DocumentUpdate(title="New Title")
        updated = doc_service.update(db_session, db_obj=doc, obj_in=update)

        assert updated.title == "New Title"

    def test_update_document_status(self, db_session, test_user, doc_service):
        """Test update status document."""
        doc_in = DocumentCreate(
            title="Status Test",
            file_path="s3://eka/status.pdf",
            owner_id=test_user.id,
            status=DocumentStatus.UPLOADED,
        )
        doc = doc_service.create(db_session, obj_in=doc_in)

        update = DocumentUpdate(status=DocumentStatus.PROCESSING)
        updated = doc_service.update(db_session, db_obj=doc, obj_in=update)

        assert updated.status == DocumentStatus.PROCESSING

    def test_update_status_via_helper(self, db_session, test_user, doc_service):
        """Test update_status helper method dengan semua transisi valid."""
        doc_in = DocumentCreate(
            title="Transition Test",
            file_path="s3://eka/transition.pdf",
            owner_id=test_user.id,
            status=DocumentStatus.UPLOADED,
        )
        doc = doc_service.create(db_session, obj_in=doc_in)

        # UPLOADED -> PROCESSING
        updated = doc_service.update_status(
            db_session,
            document_id=doc.id,
            status=DocumentStatus.PROCESSING,
        )
        assert updated.status == DocumentStatus.PROCESSING

        # PROCESSING -> COMPLETED
        updated = doc_service.update_status(
            db_session,
            document_id=doc.id,
            status=DocumentStatus.COMPLETED,
        )
        assert updated.status == DocumentStatus.COMPLETED

    def test_update_status_nonexistent(self, db_session, doc_service):
        """Test update_status untuk document yang tidak ada."""
        result = doc_service.update_status(
            db_session,
            document_id=uuid.uuid4(),
            status=DocumentStatus.FAILED,
        )
        assert result is None

    def test_update_with_dict(self, db_session, test_user, doc_service):
        """Test update menggunakan dict sebagai input."""
        doc_in = DocumentCreate(
            title="Dict Update",
            file_path="s3://eka/dict.pdf",
            owner_id=test_user.id,
        )
        doc = doc_service.create(db_session, obj_in=doc_in)

        updated = doc_service.update(
            db_session,
            db_obj=doc,
            obj_in={"title": "Updated via Dict", "status": DocumentStatus.FAILED},
        )
        assert updated.title == "Updated via Dict"
        assert updated.status == DocumentStatus.FAILED


class TestDocumentServiceDelete:
    def test_delete_existing_document(self, db_session, test_user, doc_service):
        """Test menghapus document yang ada."""
        doc_in = DocumentCreate(
            title="To Delete",
            file_path="s3://eka/delete.pdf",
            owner_id=test_user.id,
        )
        doc = doc_service.create(db_session, obj_in=doc_in)
        doc_id = doc.id

        deleted = doc_service.delete(db_session, document_id=doc_id)
        assert deleted is not None
        assert deleted.id == doc_id

        # Verifikasi sudah terhapus
        fetched = doc_service.get(db_session, document_id=doc_id)
        assert fetched is None

    def test_delete_nonexistent_document(self, db_session, doc_service):
        """Test menghapus document yang tidak ada mengembalikan None."""
        result = doc_service.delete(db_session, document_id=uuid.uuid4())
        assert result is None


class TestDocumentServiceSearchAndFilter:
    def test_get_by_owner_search(self, db_session, test_user, doc_service):
        """Test pencarian berdasarkan judul."""
        doc_service.create(
            db_session,
            obj_in=DocumentCreate(
                title="Apple Document", file_path="s3://eka/1", owner_id=test_user.id
            ),
        )
        doc_service.create(
            db_session,
            obj_in=DocumentCreate(
                title="Banana Report", file_path="s3://eka/2", owner_id=test_user.id
            ),
        )

        # Search case-insensitive
        docs = doc_service.get_by_owner(
            db_session, owner_id=test_user.id, search="apple"
        )
        assert len(docs) == 1
        assert docs[0].title == "Apple Document"

        docs = doc_service.get_by_owner(
            db_session, owner_id=test_user.id, search="report"
        )
        assert len(docs) == 1
        assert docs[0].title == "Banana Report"

    def test_get_by_owner_filter_status(self, db_session, test_user, doc_service):
        """Test filter berdasarkan status."""
        doc_service.create(
            db_session,
            obj_in=DocumentCreate(
                title="Doc 1",
                file_path="s3://eka/1",
                owner_id=test_user.id,
                status=DocumentStatus.COMPLETED,
            ),
        )
        doc_service.create(
            db_session,
            obj_in=DocumentCreate(
                title="Doc 2",
                file_path="s3://eka/2",
                owner_id=test_user.id,
                status=DocumentStatus.FAILED,
            ),
        )

        docs = doc_service.get_by_owner(
            db_session, owner_id=test_user.id, status=DocumentStatus.COMPLETED
        )
        assert len(docs) == 1
        assert docs[0].status == DocumentStatus.COMPLETED

        docs = doc_service.get_by_owner(
            db_session, owner_id=test_user.id, status=DocumentStatus.FAILED
        )
        assert len(docs) == 1
        assert docs[0].status == DocumentStatus.FAILED

    def test_get_by_owner_sorting(self, db_session, test_user, doc_service):
        """Test sorting berdasarkan judul."""
        doc_service.create(
            db_session,
            obj_in=DocumentCreate(
                title="B Document", file_path="s3://eka/1", owner_id=test_user.id
            ),
        )
        doc_service.create(
            db_session,
            obj_in=DocumentCreate(
                title="A Document", file_path="s3://eka/2", owner_id=test_user.id
            ),
        )

        # Sort by title ASC
        docs = doc_service.get_by_owner(
            db_session, owner_id=test_user.id, sort_by="title", order="asc"
        )
        assert docs[0].title == "A Document"
        assert docs[1].title == "B Document"

        # Sort by title DESC
        docs = doc_service.get_by_owner(
            db_session, owner_id=test_user.id, sort_by="title", order="desc"
        )
        assert docs[0].title == "B Document"
        assert docs[1].title == "A Document"

    def test_get_multi_admin_search(self, db_session, test_user, doc_service):
        """Test get_multi (admin) dengan search."""
        doc_service.create(
            db_session,
            obj_in=DocumentCreate(
                title="Global Doc", file_path="s3://eka/1", owner_id=test_user.id
            ),
        )

        docs = doc_service.get_multi(db_session, search="global")
        assert len(docs) == 1
        assert docs[0].title == "Global Doc"


class TestDocumentStatusEnum:
    def test_all_status_values_exist(self):
        """Test semua nilai enum DocumentStatus tersedia."""
        assert DocumentStatus.UPLOADED.value == "uploaded"
        assert DocumentStatus.PROCESSING.value == "processing"
        assert DocumentStatus.COMPLETED.value == "completed"
        assert DocumentStatus.FAILED.value == "failed"

    def test_status_is_string_enum(self):
        """Test DocumentStatus adalah string enum (serializable)."""
        status = DocumentStatus.COMPLETED
        assert str(status) == "DocumentStatus.COMPLETED"
        assert status.value == "completed"
