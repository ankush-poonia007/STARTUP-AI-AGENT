import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import MessageRole, StartupStage
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.startup_repository import StartupRepository
from src.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_message_repository(
    async_session: AsyncSession,
):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    conversation_repository = ConversationRepository(
        async_session
    )
    message_repository = MessageRepository(async_session)

    # Create owner
    user = await user_repository.create(
        email="message-owner@example.com",
        password_hash="hashed-password",
    )

    # Create startup
    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Message Startup",
        description="Test startup",
        stage=StartupStage.IDEA,
    )

    # Create conversation
    conversation = await conversation_repository.create(
        startup_id=startup.startup_id,
        title="Test Conversation",
    )

    # Append first message
    message_1 = await message_repository.append(
        conversation_id=conversation.conversation_id,
        role=MessageRole.USER,
        content="Hello",
    )

    assert message_1.message_id is not None
    assert message_1.conversation_id == conversation.conversation_id
    assert message_1.role == MessageRole.USER
    assert message_1.content == "Hello"
    assert message_1.sequence_number == 1

    # Append second message
    message_2 = await message_repository.append(
        conversation_id=conversation.conversation_id,
        role=MessageRole.ASSISTANT,
        content="Hello! How can I help?",
    )

    assert message_2.sequence_number == 2

    # Append third message
    message_3 = await message_repository.append(
        conversation_id=conversation.conversation_id,
        role=MessageRole.USER,
        content="Help me with my startup.",
    )

    assert message_3.sequence_number == 3

    # List messages
    messages, total = (
        await message_repository.list_by_conversation(
            conversation_id=conversation.conversation_id,
            page=1,
            page_size=10,
        )
    )

    assert total == 3
    assert len(messages) == 3

    # Verify chronological sequence
    assert messages[0].sequence_number == 1
    assert messages[1].sequence_number == 2
    assert messages[2].sequence_number == 3

    assert messages[0].content == "Hello"
    assert messages[1].content == "Hello! How can I help?"
    assert messages[2].content == "Help me with my startup."