from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import StartupStage
from src.repositories.models.user import User
from src.repositories.startup_repository import StartupRepository


@pytest.mark.asyncio
async def test_startup_repository(
    async_session: AsyncSession,
):
    # ----------------------------------------------------
    # CREATE OWNER
    # ----------------------------------------------------

    owner = User(
        email="startup-test@example.com",
        password_hash="hashed-password",
    )

    async_session.add(owner)
    await async_session.flush()

    repository = StartupRepository(async_session)

    # ----------------------------------------------------
    # CREATE STARTUP
    # ----------------------------------------------------

    startup = await repository.create(
        owner_id=owner.user_id,
        name="Test Startup",
        description="Test startup description",
        stage=StartupStage.IDEA,
    )

    assert startup.startup_id is not None
    assert startup.owner_id == owner.user_id
    assert startup.name == "Test Startup"
    assert startup.stage == StartupStage.IDEA

    # ----------------------------------------------------
    # GET STARTUP BY ID
    # ----------------------------------------------------

    found = await repository.get_by_id(
        startup.startup_id
    )

    assert found is not None
    assert found.startup_id == startup.startup_id

    # ----------------------------------------------------
    # GET STARTUP BY ID AND OWNER
    # ----------------------------------------------------

    owned_startup = await repository.get_by_id_and_owner(
        startup_id=startup.startup_id,
        owner_id=owner.user_id,
    )

    assert owned_startup is not None
    assert owned_startup.startup_id == startup.startup_id

    # ----------------------------------------------------
    # VERIFY WRONG OWNER IS REJECTED
    # ----------------------------------------------------

    wrong_owner = await repository.get_by_id_and_owner(
        startup_id=startup.startup_id,
        owner_id=uuid4(),
    )

    assert wrong_owner is None

    # ----------------------------------------------------
    # LIST STARTUPS BY OWNER
    # ----------------------------------------------------

    startups, total = await repository.list_by_owner(
        owner_id=owner.user_id,
        page=1,
        page_size=10,
    )

    assert total == 1
    assert len(startups) == 1
    assert startups[0].startup_id == startup.startup_id

    # ----------------------------------------------------
    # UPDATE STARTUP
    # ----------------------------------------------------

    updated = await repository.update(
        startup_id=startup.startup_id,
        fields={
            "name": "Updated Startup",
            "description": "Updated description",
        },
    )

    assert updated.name == "Updated Startup"
    assert updated.description == "Updated description"

    # ----------------------------------------------------
    # DELETE STARTUP
    # ----------------------------------------------------

    await repository.delete(
        startup.startup_id
    )

    deleted = await repository.get_by_id(
        startup.startup_id
    )

    assert deleted is None