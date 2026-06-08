import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's question or message.")
    conversation_id: uuid.UUID | None = Field(
        None,
        description="Existing conversation ID. If None, a new one is created.",
    )
    stream: bool = Field(False, description="Whether to stream the response using SSE.")
    top_k: int = Field(5, description="Number of chunks to retrieve.")
    rephrase: bool = Field(
        False, description="Whether to rephrase the query for better retrieval."
    )
    rerank: bool = Field(
        True, description="Whether to use a reranker for retrieved chunks."
    )
    context_window: int = Field(
        1, description="Size of the context window around each chunk."
    )
    check_hallucination: bool = Field(
        False, description="Whether to perform a hallucination check."
    )


class CitationSchema(BaseModel):
    id: int
    source: str
    page: int | None = None
    text: str


class SourceSchema(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any]
    score: float


class ChatResponse(BaseModel):
    message_id: uuid.UUID | None = None
    conversation_id: uuid.UUID
    answer: str
    sources: list[SourceSchema]
    verified_citations: list[dict[str, Any]]
    is_hallucination: bool = False
    search_query: str | None = None


class MessageSchema(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    message_metadata: dict[str, Any] | None = None
    created_at: datetime


class ConversationSchema(BaseModel):
    id: uuid.UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageSchema] | None = None


class FeedbackCreate(BaseModel):
    is_useful: bool = Field(..., description="Whether the AI response was helpful.")
    comment: str | None = Field(
        None, description="Optional user comment about the response."
    )


class FeedbackResponse(BaseModel):
    message_id: uuid.UUID
    is_useful: bool
    feedback_comment: str | None = None
