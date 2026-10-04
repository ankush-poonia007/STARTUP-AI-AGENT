import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_user_repository(
    async_session: AsyncSession,
):
    repository = UserRepository(async_session)

    # ----------------------------------------------------
    # CREATE USER
    # ----------------------------------------------------

    user = await repository.create(
        email="test@example.com",
        password_hash="hashed-password",
    )

    assert user.email == "test@example.com"
    assert user.password_hash == "hashed-password"
    assert user.user_id is not None

    # ----------------------------------------------------
    # GET USER BY ID
    # ----------------------------------------------------

    found_by_id = await repository.get_by_id(
        user.user_id
    )

    assert found_by_id is not None
    assert found_by_id.user_id == user.user_id
    assert found_by_id.email == "test@example.com"

    # ----------------------------------------------------
    # GET USER BY EMAIL
    # ----------------------------------------------------

    found_by_email = await repository.get_by_email(
        "test@example.com"
    )

    assert found_by_email is not None
    assert found_by_email.user_id == user.user_id

    # ----------------------------------------------------
    # DELETE USER
    # ----------------------------------------------------

    await repository.delete(user.user_id)

    # ----------------------------------------------------
    # VERIFY DELETION
    # ----------------------------------------------------

    deleted_user = await repository.get_by_id(
        user.user_id
    )

    assert deleted_user is None