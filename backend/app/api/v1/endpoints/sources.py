import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.document import Document
from app.models.user import User
from app.repositories.vector_repository import VectorRepository
from app.services.storage import storage_service

router = APIRouter()


@router.get("/sources/{chunk_id}")
async def get_source_preview(
    chunk_id: uuid.UUID,
    window_size: int = Query(1, ge=0, le=5),
    current_user: User = Depends(deps.get_current_user),  # noqa: B008
    db: AsyncSession = Depends(deps.get_db),  # noqa: B008
) -> Any:
    """
    Retrieve a specific document chunk with metadata and surrounding context.
    Includes permission checks to ensure the user owns the document.
    """
    vector_repo = VectorRepository(db)

    # 1. Fetch the target chunk
    chunk = await vector_repo.get_chunk(chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Source chunk not found")

    # 2. Permission Check: Verify if the user owns the document
    # We need to fetch the document to check owner_id
    doc_result = await db.execute(
        select(Document).where(Document.id == chunk.document_id)
    )
    document = doc_result.scalar_one_or_none()

    if not document or document.owner_id != current_user.id:
        # In a real enterprise app, we might check RBAC or group permissions here
        raise HTTPException(status_code=403, detail="Not enough privileges")

    # 3. Fetch surrounding context if requested
    context_chunks = []
    if window_size > 0:
        context_chunks = await vector_repo.get_context_window(
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            window_size=window_size,
        )
    else:
        context_chunks = [chunk]

    # Generate presigned URL if S3 key exists
    presigned_url = None
    if document.s3_key:
        presigned_url = await storage_service.get_presigned_url(document.s3_key)

    # 4. Format response
    return {
        "chunk_id": str(chunk.id),
        "document_id": str(chunk.document_id),
        "document_title": document.title,
        "content": chunk.content,
        "metadata": chunk.chunk_metadata,
        "presigned_url": presigned_url,
        "context": [
            {
                "id": str(c.id),
                "index": c.chunk_index,
                "content": c.content,
                "is_target": c.id == chunk.id,
            }
            for c in context_chunks
        ],
    }
