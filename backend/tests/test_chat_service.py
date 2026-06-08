import uuid

import pytest
from app.models.chat import Conversation, Message
from app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_create_conversation(db_mock):
    chat_service = ChatService(db_mock)
    user_id = uuid.uuid4()

    # Setup mock return value
    mock_conv = Conversation(id=uuid.uuid4(), user_id=user_id, title="Test")
    db_mock.execute.return_value.scalar_one_or_none.return_value = mock_conv

    conv = await chat_service.create_conversation(user_id, "Test")

    assert conv.user_id == user_id
    assert conv.title == "Test"
    db_mock.add.assert_called_once()


@pytest.mark.asyncio
async def test_save_message(db_mock):
    chat_service = ChatService(db_mock)
    conv_id = uuid.uuid4()

    await chat_service.save_message(conv_id, "user", "Hello")

    db_mock.add.assert_called_once()
    # Verify the message role and content
    args, _ = db_mock.add.call_args
    msg = args[0]
    assert isinstance(msg, Message)
    assert msg.conversation_id == conv_id
    assert msg.role == "user"
    assert msg.content == "Hello"


@pytest.mark.asyncio
async def test_get_conversation_history(db_mock):
    chat_service = ChatService(db_mock)
    conv_id = uuid.uuid4()

    # Setup mock return value for messages
    mock_messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there"),
    ]
    db_mock.execute.return_value.scalars.return_value.all.return_value = mock_messages

    history = await chat_service.get_conversation_history(conv_id)

    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"


@pytest.mark.asyncio
async def test_format_history_for_prompt(db_mock):
    chat_service = ChatService(db_mock)
    conv_id = uuid.uuid4()

    mock_messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there"),
    ]
    db_mock.execute.return_value.scalars.return_value.all.return_value = mock_messages

    formatted = await chat_service.format_history_for_prompt(conv_id)

    assert len(formatted) == 2
    assert formatted[0] == {"role": "user", "content": "Hello"}
    assert formatted[1] == {"role": "assistant", "content": "Hi there"}
