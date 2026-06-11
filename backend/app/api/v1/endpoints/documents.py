import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.enums import DocumentStatus, UserRole
from app.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentListItem,
    DocumentRead,
    DocumentUpdate,
)
from app.services.document import document_service
from app.services.storage import storage_service
from app.tasks.document import process_document_task

router = APIRouter()

# Tipe file yang diizinkan
ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
}

# Batas ukuran file: 50MB
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


@router.post(
    "/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document",
    description="Upload dokumen baru (PDF, DOCX, TXT) ke platform EKA.",
)
async def upload_document(
    file: Annotated[UploadFile, File(description="File dokumen yang akan diupload")],
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> DocumentRead:
    """
    Upload dokumen baru ke sistem.

    - **file**: File yang diupload (PDF, DOCX, atau TXT), maks 50MB.
    - Memerlukan autentikasi.
    """
    # 1. Validasi content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Tipe file '{file.content_type}' tidak diizinkan. "
                f"Gunakan: {', '.join(ALLOWED_CONTENT_TYPES.keys())}"
            ),
        )

    # 2. Baca file content dan validasi ukuran
    file_content = await file.read()
    limit_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ukuran file melebihi batas {limit_mb}MB.",
        )

    # 3. Generate unique S3 key menggunakan UUID untuk menghindari collision
    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    s3_key = f"documents/{current_user.id}/{uuid.uuid4()}{extension}"
    file_path = f"s3://{settings.S3_BUCKET}/{s3_key}"

    # 4. Upload file ke storage
    import io

    file_obj = io.BytesIO(file_content)
    try:
        await storage_service.upload_file(
            file_obj, s3_key, content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal mengupload file ke storage.",
        ) from e

    # 5. Buat record di database dengan status UPLOADED
    doc_in = DocumentCreate(
        title=file.filename or s3_key.split("/")[-1],
        file_path=file_path,
        s3_key=s3_key,
        owner_id=current_user.id,
        status=DocumentStatus.UPLOADED,
        doc_metadata={
            "original_filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": len(file_content),
        },
    )
    document = document_service.create(db, obj_in=doc_in)

    # 6. Trigger background processing task (TASK-018)
    process_document_task.delay(str(document.id))

    return document


@router.get(
    "/documents",
    response_model=list[DocumentListItem],
    summary="List documents",
    description="Ambil daftar dokumen milik user yang login.",
)
def list_documents(
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    status: DocumentStatus | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> list[DocumentListItem]:
    """
    Ambil daftar dokumen.

    - Admin melihat semua dokumen.
    - User biasa hanya melihat dokumen miliknya sendiri.
    - Mendukung pencarian, filter status, dan sorting.
    """
    if current_user.role == UserRole.ADMIN:
        docs = document_service.get_multi(
            db,
            skip=skip,
            limit=limit,
            search=search,
            status=status,
            sort_by=sort_by,
            order=order,
        )
    else:
        docs = document_service.get_by_owner(
            db,
            owner_id=current_user.id,
            skip=skip,
            limit=limit,
            search=search,
            status=status,
            sort_by=sort_by,
            order=order,
        )
    return docs


@router.get(
    "/documents/{document_id}",
    response_model=DocumentRead,
    summary="Get document detail",
    description="Ambil detail dokumen berdasarkan ID.",
)
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> DocumentRead:
    """Ambil detail document. User hanya bisa mengakses dokumen miliknya sendiri."""
    doc = document_service.get(db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document tidak ditemukan.",
        )

    # Cek ownership (admin bisa akses semua)
    if current_user.role != UserRole.ADMIN and doc.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke dokumen ini.",
        )

    return doc


@router.patch(
    "/documents/{document_id}",
    response_model=DocumentRead,
    summary="Update document",
    description="Update metadata atau judul dokumen.",
)
def update_document(
    document_id: uuid.UUID,
    obj_in: DocumentUpdate,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> DocumentRead:
    """Update dokumen. User hanya bisa mengupdate dokumen miliknya sendiri."""
    doc = document_service.get(db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document tidak ditemukan.",
        )

    # Cek ownership (admin bisa update semua)
    if current_user.role != UserRole.ADMIN and doc.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses untuk mengupdate dokumen ini.",
        )

    return document_service.update(db, db_obj=doc, obj_in=obj_in)


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Hapus dokumen berdasarkan ID.",
)
async def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> None:
    """Hapus dokumen. User hanya bisa menghapus dokumen miliknya sendiri."""
    doc = document_service.get(db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document tidak ditemukan.",
        )

    # Cek ownership (admin bisa hapus semua)
    if current_user.role != UserRole.ADMIN and doc.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke dokumen ini.",
        )

    # Hapus dari S3 storage jika ada s3_key
    if doc.s3_key:
        try:
            await storage_service.delete_file(doc.s3_key)
        except Exception as e:
            # Log tapi jangan block delete dari DB
            from app.core.logging import get_logger

            logger = get_logger(__name__)
            logger.error(f"Gagal menghapus file dari storage: {e}")

    document_service.delete(db, document_id=document_id)
