import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.conversation_repository import ConversationRepository
from src.repositories.startup_repository import StartupRepository
from src.repositories.user_repository import UserRepository
from src.core.enums import StartupStage


@pytest.mark.asyncio
async def test_conversation_repository(
    async_session: AsyncSession,
):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    conversation_repository = ConversationRepository(
        async_session
    )

    # Create owner
    user = await user_repository.create(
        email="conversation-owner@example.com",
        password_hash="hashed-password",
    )

    # Create startup
    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Conversation Startup",
        description="Test startup",
        stage=StartupStage.IDEA,
    )

    # Create conversation
    conversation = await conversation_repository.create(
        startup_id=startup.startup_id,
        title="Initial Conversation",
    )

    assert conversation.conversation_id is not None
    assert conversation.startup_id == startup.startup_id
    assert conversation.title == "Initial Conversation"

    # Get by ID
    found = await conversation_repository.get_by_id(
        conversation.conversation_id
    )

    assert found is not None
    assert found.conversation_id == conversation.conversation_id
    assert found.title == "Initial Conversation"

    # List by startup
    conversations, total = (
        await conversation_repository.list_by_startup(
            startup_id=startup.startup_id,
            page=1,
            page_size=10,
        )
    )

    assert total == 1
    assert len(conversations) == 1
    assert (
        conversations[0].conversation_id
        == conversation.conversation_id
    )

    # Update
    updated = await conversation_repository.update(
        conversation.conversation_id,
        "Updated Conversation",
    )

    assert updated.title == "Updated Conversation"

    # Delete
    await conversation_repository.delete(
        conversation.conversation_id
    )

    deleted = await conversation_repository.get_by_id(
        conversation.conversation_id
    )

    assert deleted is None