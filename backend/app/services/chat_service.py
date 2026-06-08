import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Conversation, Message
from app.repositories.chat_repository import ChatRepository


class ChatService:
    """Service layer for managing chat conversations and history."""

    def __init__(self, db: AsyncSession):
        self.repository = ChatRepository(db)

    async def create_conversation(
        self, user_id: uuid.UUID, title: str | None = None
    ) -> Conversation:
        """Create a new conversation for a user."""
        return await self.repository.create_conversation(user_id=user_id, title=title)

    async def get_conversation(self, conversation_id: uuid.UUID) -> Conversation | None:
        """Retrieve a conversation by ID."""
        return await self.repository.get_conversation(conversation_id)

    async def list_conversations(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        """List conversations for a specific user."""
        return await self.repository.list_conversations(
            user_id=user_id, limit=limit, offset=offset
        )

    async def delete_conversation(self, conversation_id: uuid.UUID) -> None:
        """Delete a conversation and its history."""
        await self.repository.delete_conversation(conversation_id)

    async def save_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """Save a new message to the database."""
        return await self.repository.create_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata,
        )

    async def get_conversation_history(
        self, conversation_id: uuid.UUID, limit: int = 20
    ) -> list[Message]:
        """Retrieve the latest messages from a conversation."""
        return await self.repository.list_messages(
            conversation_id=conversation_id, limit=limit
        )

    async def format_history_for_prompt(
        self, conversation_id: uuid.UUID, limit: int = 10
    ) -> list[dict[str, str]]:
        """
        Retrieve history and format it as a list of message objects for LLM.
        """
        messages = await self.get_conversation_history(conversation_id, limit=limit)
        return [{"role": msg.role, "content": msg.content} for msg in messages]
