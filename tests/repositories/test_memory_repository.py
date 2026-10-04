import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import MemoryType, StartupStage
from src.repositories.memory_repository import MemoryRepository
from src.repositories.startup_repository import StartupRepository
from src.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_memory_repository(
    async_session: AsyncSession,
):
    user_repository = UserRepository(async_session)
    startup_repository = StartupRepository(async_session)
    memory_repository = MemoryRepository(async_session)

    # Create owner
    user = await user_repository.create(
        email="memory-owner@example.com",
        password_hash="hashed-password",
    )

    # Create startup
    startup = await startup_repository.create(
        owner_id=user.user_id,
        name="Memory Startup",
        description="Test startup",
        stage=StartupStage.IDEA,
    )

    # Create memory
    memory = await memory_repository.create(
        startup_id=startup.startup_id,
        memory_type=MemoryType.STARTUP_FACT,
        content="The startup targets college students.",
        importance=0.8,
    )

    assert memory.memory_id is not None
    assert memory.startup_id == startup.startup_id
    assert memory.memory_type == MemoryType.STARTUP_FACT
    assert memory.content == "The startup targets college students."
    assert memory.importance == 0.8

    # Get by ID
    found = await memory_repository.get_by_id(
        memory.memory_id
    )

    assert found is not None
    assert found.memory_id == memory.memory_id
    assert found.content == memory.content

    # List by startup
    memories, total = (
        await memory_repository.list_by_startup(
            startup_id=startup.startup_id,
            page=1,
            page_size=10,
        )
    )

    assert total == 1
    assert len(memories) == 1
    assert memories[0].memory_id == memory.memory_id

    # Delete
    await memory_repository.delete(
        memory.memory_id
    )

    # Verify deletion
    deleted = await memory_repository.get_by_id(
        memory.memory_id
    )

    assert deleted is None