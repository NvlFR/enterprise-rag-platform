import uuid

import pytest
from app.models.chat import Conversation, Message
from app.repositories.chat_repository import ChatRepository


def test_conversation_model():
    user_id = uuid.uuid4()
    conv = Conversation(user_id=user_id, title="Test Conversation")
    assert conv.user_id == user_id
    assert conv.title == "Test Conversation"


def test_message_model():
    conv_id = uuid.uuid4()
    msg = Message(
        conversation_id=conv_id,
        role="user",
        content="Test Content",
        message_metadata={"test": "data"},
    )
    assert msg.conversation_id == conv_id
    assert msg.role == "user"
    assert msg.content == "Test Content"
    assert msg.message_metadata == {"test": "data"}


@pytest.mark.asyncio
async def test_chat_repository_create_conversation(db_mock):
    repo = ChatRepository(db_mock)
    user_id = uuid.uuid4()

    conv = await repo.create_conversation(user_id=user_id, title="Repo Test")

    assert conv.user_id == user_id
    assert conv.title == "Repo Test"
    db_mock.add.assert_called_once()


@pytest.mark.asyncio
async def test_chat_repository_create_message(db_mock):
    repo = ChatRepository(db_mock)
    conv_id = uuid.uuid4()

    msg = await repo.create_message(
        conversation_id=conv_id,
        role="assistant",
        content="Hello",
        metadata={"source": "test"},
    )

    assert msg.conversation_id == conv_id
    assert msg.role == "assistant"
    assert msg.content == "Hello"
    assert msg.message_metadata == {"source": "test"}
    db_mock.add.assert_called_once()
