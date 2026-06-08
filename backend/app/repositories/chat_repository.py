import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Conversation, Message


class ChatRepository:
    """Repository for managing chat conversations and messages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self, user_id: uuid.UUID, title: str | None = None
    ) -> Conversation:
        """Create a new conversation."""
        db_conversation = Conversation(user_id=user_id, title=title)
        self.db.add(db_conversation)
        return db_conversation

    async def get_conversation(self, conversation_id: uuid.UUID) -> Conversation | None:
        """Retrieve a conversation by ID."""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self, user_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[Conversation]:
        """List conversations for a specific user."""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete_conversation(self, conversation_id: uuid.UUID) -> None:
        """Delete a conversation and all its messages (cascade delete)."""
        await self.db.execute(
            delete(Conversation).where(Conversation.id == conversation_id)
        )

    async def create_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """Create a new message in a conversation."""
        db_message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata,
        )
        self.db.add(db_message)
        return db_message

    async def list_messages(
        self, conversation_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[Message]:
        """List all messages for a specific conversation."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_message_feedback(
        self,
        message_id: uuid.UUID,
        is_useful: bool,
        feedback_comment: str | None = None,
    ) -> Message | None:
        """Update feedback for a specific message."""
        result = await self.db.execute(select(Message).where(Message.id == message_id))
        db_message = result.scalar_one_or_none()
        if db_message:
            db_message.is_useful = is_useful
            db_message.feedback_comment = feedback_comment
            await self.db.flush()
        return db_message
