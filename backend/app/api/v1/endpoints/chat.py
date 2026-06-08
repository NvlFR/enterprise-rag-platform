import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.chat import Conversation, Message
from app.models.user import User
from app.repositories.vector_repository import VectorRepository
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    FeedbackCreate,
    FeedbackResponse,
)
from app.services.chat_service import ChatService
from app.services.rag import RAGService
from app.services.retrieval import RetrievalService

router = APIRouter()


@router.post("/chat/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    current_user: User = Depends(deps.get_current_user),  # noqa: B008
    db: AsyncSession = Depends(deps.get_db),  # noqa: B008
) -> Any:
    """
    Send a message to the AI and get a response.
    Supports both streaming (SSE) and non-streaming modes.
    """
    chat_service = ChatService(db)
    vector_repo = VectorRepository(db)
    retrieval_service = RetrievalService(vector_repo)
    rag_service = RAGService(retrieval_service, chat_service)

    # 1. Ensure conversation exists
    conversation_id = request.conversation_id
    if conversation_id:
        conversation = await chat_service.get_conversation(conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create a new conversation if no ID provided
        # We can use a snippet of the message as the title
        title = (
            request.message[:50] + "..."
            if len(request.message) > 50
            else request.message
        )
        conversation = await chat_service.create_conversation(
            user_id=current_user.id, title=title
        )
        conversation_id = conversation.id

    # 2. Handle Streaming mode
    if request.stream:
        return StreamingResponse(
            rag_service.stream_generate_answer(
                question=request.message,
                top_k=request.top_k,
                rephrase=request.rephrase,
                rerank=request.rerank,
                context_window=request.context_window,
                check_hallucination=request.check_hallucination,
                conversation_id=conversation_id,
            ),
            media_type="text/event-stream",
        )

    # 3. Handle Non-streaming mode
    result = await rag_service.generate_answer(
        question=request.message,
        top_k=request.top_k,
        rephrase=request.rephrase,
        rerank=request.rerank,
        context_window=request.context_window,
        check_hallucination=request.check_hallucination,
        conversation_id=conversation_id,
    )

    return ChatResponse(
        conversation_id=conversation_id,
        answer=result["answer"],
        sources=result["sources"],
        verified_citations=result["verified_citations"],
        is_hallucination=result["is_hallucination"],
        search_query=result.get("search_query"),
    )


@router.post("/messages/{message_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    message_id: uuid.UUID,
    feedback: FeedbackCreate,
    current_user: User = Depends(deps.get_current_user),  # noqa: B008
    db: AsyncSession = Depends(deps.get_db),  # noqa: B008
) -> Any:
    """
    Submit feedback (thumbs up/down) for a specific AI message.
    """
    chat_service = ChatService(db)

    # 1. Verify message existence and ownership (via conversation)
    stmt = (
        select(Message)
        .join(Conversation)
        .where(Message.id == message_id)
        .where(Conversation.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    db_message = res.scalar_one_or_none()

    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")

    # 2. Update feedback
    updated_message = await chat_service.repository.update_message_feedback(
        message_id=message_id,
        is_useful=feedback.is_useful,
        feedback_comment=feedback.comment,
    )
    await db.commit()

    return FeedbackResponse(
        message_id=updated_message.id,
        is_useful=updated_message.is_useful,
        feedback_comment=updated_message.feedback_comment,
    )


@router.get("/chat/stream")
async def chat_stream_legacy(
    question: str,
    top_k: int = 5,
    rephrase: bool = False,
    rerank: bool = True,
    context_window: int = 1,
    check_hallucination: bool = False,
    db: AsyncSession = Depends(deps.get_db),  # noqa: B008
) -> Any:
    """
    Legacy stream endpoint for compatibility.
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
