# INTEGRATION TESTS — REPOSITORY LAYER
# Responsibility:
#   Verifies repository behavior against the real PostgreSQL test database.
# Flow:
#   Test -> Repository -> SQLAlchemy AsyncSession -> PostgreSQL
#   -> Assert persisted behavior -> Transaction rollback

import asyncio
import os
import subprocess
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from src.config.settings import TEST_DATABASE_URL
from src.core.enums import MemoryType, MessageRole, StartupStage
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.memory_repository import MemoryRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.startup_repository import StartupRepository
from src.repositories.user_repository import UserRepository
from tests.conftest import TestSessionLocal



@pytest.mark.asyncio
async def test_create_user(async_session):
    repository = UserRepository(async_session)
    
    user = await repository.create(
        email = "integration_test@example.com",
        password_hash="test-password-hash",
    )
    
    assert user is not None
    assert isinstance(user.user_id, UUID)
    assert user.email == "integration_test@example.com"
    
@pytest.mark.asyncio
async def test_duplicate_email(async_session):
    
    repository = UserRepository(async_session)
    
    await repository.create(
        email= "duplicate@example.com",
        password_hash="test-password-hash",
    )
    
    with pytest.raises(IntegrityError):
        async with async_session.begin_nested():
            await repository.create(
                email="duplicate@example.com",
                password_hash="test-password-hash",
            )
    

@pytest.mark.asyncio
async def test_get_user_by_email(async_session):
    repository = UserRepository(async_session)

    created_user = await repository.create(
        email="lookup@example.com",
        password_hash="test-password-hash",
    )

    user = await repository.get_by_email("lookup@example.com")
    
    assert user is not None
    assert user.user_id == created_user.user_id
    assert user.email == "lookup@example.com"
    

@pytest.mark.asyncio
async def test_create_startup(async_session):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)

    user = await user_repository.create(
        email="startup_owner@example.com",
        password_hash="test-password-hash",
    )

    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Integration Startup",
        description="Integration test startup",
        stage=StartupStage.IDEA,
    )

    assert startup is not None
    assert startup.owner_id == user.user_id
    assert startup.name == "Integration Startup"
    

@pytest.mark.asyncio
async def test_get_startup_wrong_owner(async_session):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)

    owner = await user_repository.create(
        email="owner@example.com",
        password_hash="test-password-hash",
    )

    other_user = await user_repository.create(
        email="other@example.com",
        password_hash="test-password-hash",
    )

    startup = await startup_repository.create(
        owner_id=owner.user_id,
        name="Private Startup",
        description="Ownership test",
        stage=StartupStage.IDEA,
    )

    result = await startup_repository.get_by_id_and_owner(
        startup.startup_id,
        owner_id=other_user.user_id,
    )

    assert result is None
    

@pytest.mark.asyncio
async def test_cascade_delete_startup(async_session):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    conversation_repository = ConversationRepository(async_session)
    message_repository = MessageRepository(async_session)
    memory_repository = MemoryRepository(async_session)

    user = await user_repository.create(
        email="cascade_owner@example.com",
        password_hash="test-password-hash",
    )

    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Cascade Startup",
        description="Cascade test",
        stage=StartupStage.IDEA,
    )

    conversation = await conversation_repository.create(
        startup_id=startup.startup_id,
        title="Cascade Conversation",
    )

    message = await message_repository.append(
        conversation_id=conversation.conversation_id,
        role=MessageRole.USER,
        content="Cascade test message",
    )

    memory = await memory_repository.create(
        startup_id=startup.startup_id,
        memory_type=MemoryType.STARTUP_FACT,
        content="Cascade test memory",
        importance=0.5,
    )

    await startup_repository.delete(startup.startup_id)

    deleted_conversation = await conversation_repository.get_by_id(
        conversation.conversation_id
    )
    remaining_messages, remaining_message_count = (
        await message_repository.list_by_conversation(
            conversation_id=conversation.conversation_id,
            page=1,
            page_size=10,
        )
    )
    deleted_memory = await memory_repository.get_by_id(
        memory.memory_id
    )

    assert deleted_conversation is None
    assert remaining_messages == []
    assert remaining_message_count == 0
    assert deleted_memory is None
    

@pytest.mark.asyncio
async def test_create_conversation(async_session):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    conversation_repository = ConversationRepository(async_session)

    user = await user_repository.create(
        email="conversation_owner@example.com",
        password_hash="test-password-hash",
    )

    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Conversation Startup",
        description="Conversation integration test",
        stage=StartupStage.IDEA,
    )

    conversation = await conversation_repository.create(
        startup_id=startup.startup_id,
        title="Integration Conversation",
    )

    assert conversation is not None
    assert conversation.startup_id == startup.startup_id
    assert conversation.title == "Integration Conversation"
    

@pytest.mark.asyncio
async def test_append_message_first(async_session):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    conversation_repository = ConversationRepository(async_session)
    message_repository = MessageRepository(async_session)

    user = await user_repository.create(
        email="message_first@example.com",
        password_hash="test-password-hash",
    )

    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Message First Startup",
        description="First message integration test",
        stage=StartupStage.IDEA,
    )

    conversation = await conversation_repository.create(
        startup_id=startup.startup_id,
        title="Message Sequence Test",
    )

    message = await message_repository.append(
        conversation_id=conversation.conversation_id,
        role=MessageRole.USER,
        content="First message",
    )

    assert message is not None
    assert message.conversation_id == conversation.conversation_id
    assert message.sequence_number == 1
    
    
@pytest.mark.asyncio
async def test_append_message_second(async_session):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    conversation_repository = ConversationRepository(async_session)
    message_repository = MessageRepository(async_session)

    user = await user_repository.create(
        email="message_second@example.com",
        password_hash="test-password-hash",
    )

    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Message Second Startup",
        description="Second message integration test",
        stage=StartupStage.IDEA,
    )

    conversation = await conversation_repository.create(
        startup_id=startup.startup_id,
        title="Message Sequence Test",
    )

    first_message = await message_repository.append(
        conversation_id=conversation.conversation_id,
        role=MessageRole.USER,
        content="First message",
    )

    second_message = await message_repository.append(
        conversation_id=conversation.conversation_id,
        role=MessageRole.ASSISTANT,
        content="Second message",
    )

    assert first_message.sequence_number == 1
    assert second_message.sequence_number == 2
    assert second_message.conversation_id == conversation.conversation_id
    
    

@pytest.mark.asyncio
async def test_message_sequence_concurrent():
    async with TestSessionLocal() as setup_session:
        user = await UserRepository(setup_session).create(
            email="concurrent@example.com",
            password_hash="test-password-hash",
        )

        startup = await StartupRepository(setup_session).create(
            owner_id=user.user_id,
            name="Concurrent Startup",
            description="Concurrent sequence test",
            stage=StartupStage.IDEA,
        )

        conversation = await ConversationRepository(setup_session).create(
            startup_id=startup.startup_id,
            title="Concurrent Message Test",
        )
        await setup_session.commit()

    async def append_message(index):
        async with TestSessionLocal() as session:
            repository = MessageRepository(session)

            message = await repository.append(
                conversation_id=conversation.conversation_id,
                role=MessageRole.USER,
                content=f"Concurrent message {index}",
            )

            await session.commit()
            return message.sequence_number

    try:
        sequence_numbers = await asyncio.gather(
            *(append_message(index) for index in range(10))
        )

        assert len(sequence_numbers) == 10
        assert len(set(sequence_numbers)) == 10
        assert sorted(sequence_numbers) == list(range(1, 11))
    finally:
        async with TestSessionLocal() as cleanup_session:
            await UserRepository(cleanup_session).delete(user.user_id)
            await cleanup_session.commit()


@pytest.mark.asyncio
async def test_list_messages_asc_order(async_session):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    conversation_repository = ConversationRepository(async_session)
    message_repository = MessageRepository(async_session)

    user = await user_repository.create(
        email="message_order@example.com",
        password_hash="test-password-hash",
    )

    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Message Order Startup",
        description="Message ordering integration test",
        stage=StartupStage.IDEA,
    )

    conversation = await conversation_repository.create(
        startup_id=startup.startup_id,
        title="Message Order Test",
    )

    for index in range(5):
        await message_repository.append(
            conversation_id=conversation.conversation_id,
            role=MessageRole.USER,
            content=f"Message {index + 1}",
        )

    messages, total = await message_repository.list_by_conversation(
        conversation_id=conversation.conversation_id,
        page=1,
        page_size=10,
    )

    sequence_numbers = [
        message.sequence_number
        for message in messages
    ]

    assert sequence_numbers == [1, 2, 3, 4, 5]
    assert total == 5
    
    
@pytest.mark.asyncio
async def test_create_memory(async_session):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    memory_repository = MemoryRepository(async_session)

    user = await user_repository.create(
        email="memory_create@example.com",
        password_hash="test-password-hash",
    )

    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Memory Startup",
        description="Memory creation integration test",
        stage=StartupStage.IDEA,
    )

    memory = await memory_repository.create(
        startup_id=startup.startup_id,
        memory_type=MemoryType.STARTUP_FACT,
        content="The startup targets college students.",
        importance=1.0,
    )

    assert memory is not None
    assert memory.startup_id == startup.startup_id
    assert memory.memory_type == MemoryType.STARTUP_FACT
    
    
@pytest.mark.asyncio
async def test_delete_memory(async_session):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    memory_repository = MemoryRepository(async_session)

    user = await user_repository.create(
        email="memory_delete@example.com",
        password_hash="test-password-hash",
    )

    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Memory Delete Startup",
        description="Memory deletion integration test",
        stage=StartupStage.IDEA,
    )

    memory = await memory_repository.create(
        startup_id=startup.startup_id,
        memory_type=MemoryType.STARTUP_FACT,
        content="Memory to delete.",
        importance=1.0,
    )

    await memory_repository.delete(memory.memory_id)

    deleted_memory = await memory_repository.get_by_id(memory.memory_id)

    assert deleted_memory is None
    
    
@pytest.mark.asyncio
async def test_pagination(async_session):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    conversation_repository = ConversationRepository(async_session)
    message_repository = MessageRepository(async_session)

    user = await user_repository.create(
        email="pagination@example.com",
        password_hash="test-password-hash",
    )

    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Pagination Startup",
        description="Pagination integration test",
        stage=StartupStage.IDEA,
    )

    conversation = await conversation_repository.create(
        startup_id=startup.startup_id,
        title="Pagination Test",
    )

    for index in range(25):
        await message_repository.append(
            conversation_id=conversation.conversation_id,
            role=MessageRole.USER,
            content=f"Message {index + 1}",
        )

    messages, total = await message_repository.list_by_conversation(
        conversation_id=conversation.conversation_id,
        page=1,
        page_size=10,
    )

    assert len(messages) == 10
    assert total == 25
    
    
def test_migration_upgrade():
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL

    downgrade = subprocess.run(
        ["alembic", "downgrade", "base"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert downgrade.returncode == 0

    upgrade = subprocess.run(
        ["alembic", "upgrade", "head"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert upgrade.returncode == 0
    
    
def test_migration_downgrade():
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL

    result = subprocess.run(
        ["alembic", "downgrade", "base"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0