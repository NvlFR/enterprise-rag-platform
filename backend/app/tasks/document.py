import asyncio
import os
import tempfile
import uuid

from celery import Task
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.enums import DocumentStatus
from app.services.document import document_service
from app.services.metadata import metadata_service
from app.services.parser import parser_service
from app.services.storage import storage_service

logger = get_task_logger(__name__)


class DocumentProcessingTask(Task):
    """Base class untuk document processing tasks dengan session management."""

    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handler saat task gagal — update status ke FAILED."""
        document_id = args[0] if args else kwargs.get("document_id")
        if document_id:
            logger.error(
                f"Task {task_id} GAGAL untuk document {document_id}: {exc}",
                exc_info=einfo,
            )
            db = SessionLocal()
            try:
                document_service.update_status(
                    db,
                    document_id=uuid.UUID(document_id),
                    status=DocumentStatus.FAILED,
                )
            except Exception as e:
                logger.error(f"Gagal mengupdate status document {document_id}: {e}")
            finally:
                db.close()

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handler saat task di-retry."""
        document_id = args[0] if args else kwargs.get("document_id")
        logger.warning(
            f"Task {task_id} sedang di-retry untuk document {document_id}: {exc}"
        )


@celery_app.task(
    bind=True,
    base=DocumentProcessingTask,
    name="app.tasks.document.process_document_task",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_document_task(self: Task, document_id: str) -> dict:
    """
    Background task untuk memproses dokumen yang baru diupload.

    Pipeline:
    1. Update status -> PROCESSING
    2. Extract text dari file (TODO: TASK-019)
    3. Chunking (TODO: TASK-020)
    4. Embedding (TODO: TASK-021)
    5. Simpan chunks ke Vector DB (TODO: TASK-022)
    6. Update status -> COMPLETED

    Args:
        document_id: UUID dokumen yang akan diproses.

    Returns:
        Dict dengan status hasil processing.
    """
    logger.info(f"Mulai memproses document: {document_id}")

    db = SessionLocal()
    try:
        doc_uuid = uuid.UUID(document_id)

        # Ambil document dari db yang aktif
        doc = document_service.get(db, document_id=doc_uuid)
        if not doc:
            logger.error(f"Document {document_id} tidak ditemukan di database.")
            db.close()
            return {"status": "error", "message": "Document not found"}

        # 1. Update status ke PROCESSING
        document_service.update_status(
            db, document_id=doc_uuid, status=DocumentStatus.PROCESSING
        )

        logger.info(f"Document {document_id} status: {doc.status}")

        # 2. Extract text dari file
        # Download file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            asyncio.run(storage_service.download_file(doc.s3_key, tmp_path))

            # Parse file
            file_type = doc.s3_key.split(".")[-1].lower()
            with open(tmp_path, "rb") as f:
                file_content = f.read()

            text = parser_service.parse(file_content, file_type)
            # Extract metadata
            metadata = metadata_service.extract(text)
            # Update document with metadata
            document_service.update(db, db_obj=doc, obj_in={"doc_metadata": metadata})

            logger.info(
                f"Text extracted and metadata generated for document {document_id}, "
                f"length: {len(text)}"
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # TODO (TASK-020): Chunking teks
        # chunks = chunking_service.chunk(text, chunk_size=512, overlap=100)

        # TODO (TASK-021): Generate embeddings
        # embeddings = embedding_service.embed(chunks)

        # TODO (TASK-022): Simpan ke pgvector
        # vector_store.save(document_id=doc_uuid, chunks=chunks, embeddings=embeddings)

        # 3. Update status ke COMPLETED (placeholder — akan diisi oleh task berikutnya)
        # Sementara langsung COMPLETED karena belum ada pipeline sebenarnya
        document_service.update_status(
            db, document_id=doc_uuid, status=DocumentStatus.COMPLETED
        )

        logger.info(f"Document {document_id} berhasil diproses.")
        return {
            "status": "success",
            "document_id": document_id,
            "message": "Document processing completed (skeleton pipeline).",
        }

    except Exception as exc:
        logger.error(f"Error memproses document {document_id}: {exc}", exc_info=True)
        # Update status ke FAILED
        try:
            document_service.update_status(
                db,
                document_id=uuid.UUID(document_id),
                status=DocumentStatus.FAILED,
            )
        except Exception as inner_exc:
            logger.error(f"Gagal mengupdate status FAILED: {inner_exc}")

        # Retry dengan exponential backoff
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1)) from exc
    finally:
        db.close()
