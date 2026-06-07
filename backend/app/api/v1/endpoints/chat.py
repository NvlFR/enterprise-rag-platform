from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.repositories.vector_repository import VectorRepository
from app.services.rag import RAGService
from app.services.retrieval import RetrievalService

router = APIRouter()


@router.get("/chat/stream")
async def chat_stream(
    question: str,
    top_k: int = 5,
    rephrase: bool = False,
    rerank: bool = True,
    context_window: int = 1,
    check_hallucination: bool = False,
    db: AsyncSession = Depends(deps.get_db),  # noqa: B008
) -> Any:
    """
    Stream a RAG answer for a given question.
    """
    vector_repo = VectorRepository(db)
    retrieval_service = RetrievalService(vector_repo)
    rag_service = RAGService(retrieval_service)

    return StreamingResponse(
        rag_service.stream_generate_answer(
            question=question,
            top_k=top_k,
            rephrase=rephrase,
            rerank=rerank,
            context_window=context_window,
            check_hallucination=check_hallucination,
        ),
        media_type="text/event-stream",
    )
