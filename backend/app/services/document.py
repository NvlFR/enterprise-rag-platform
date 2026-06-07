import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import DocumentStatus
from app.schemas.document import DocumentCreate, DocumentUpdate


class DocumentService:
    """Service layer untuk manajemen document CRUD."""

    def create(self, db: Session, *, obj_in: DocumentCreate) -> Document:
        """Buat record document baru di database."""
        db_obj = Document(
            title=obj_in.title,
            file_path=obj_in.file_path,
            s3_key=obj_in.s3_key,
            status=obj_in.status,
            owner_id=obj_in.owner_id,
            doc_metadata=obj_in.doc_metadata,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, *, document_id: uuid.UUID) -> Document | None:
        """Ambil document berdasarkan ID."""
        return db.query(Document).filter(Document.id == document_id).first()

    def get_by_owner(
        self,
        db: Session,
        *,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        """Ambil semua document milik user tertentu."""
        return (
            db.query(Document)
            .filter(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[Document]:
        """Ambil semua document (admin only)."""
        return (
            db.query(Document)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(
        self,
        db: Session,
        *,
        db_obj: Document,
        obj_in: DocumentUpdate | dict[str, Any],
    ) -> Document:
        """Update document record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_status(
        self, db: Session, *, document_id: uuid.UUID, status: DocumentStatus
    ) -> Document | None:
        """Update status document — helper untuk workflow processing."""
        doc = self.get(db, document_id=document_id)
        if not doc:
            return None
        doc.status = status
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    def delete(self, db: Session, *, document_id: uuid.UUID) -> Document | None:
        """Hapus document record dari database."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            db.delete(doc)
            db.commit()
        return doc


document_service = DocumentService()
