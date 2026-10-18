from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from src.repositories.models.refresh_token import RefreshToken
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.repositories.user_repository import UserRepository


async def _create_user(session):
    return await UserRepository(session).create(
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
    )


@pytest.mark.asyncio
async def test_create_then_get_by_hash(async_session):
    user = await _create_user(async_session)
    repository = RefreshTokenRepository(async_session)
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    created = await repository.create(
        user.user_id,
        "sha256-hash-create",
        expires_at,
    )
    found = await repository.get_by_hash("sha256-hash-create")

    assert found is created
    assert found.user_id == user.user_id
    assert found.expires_at == expires_at
    assert found.revoked_at is None


@pytest.mark.asyncio
async def test_get_by_unknown_hash_returns_none(async_session):
    repository = RefreshTokenRepository(async_session)

    assert await repository.get_by_hash("unknown-sha256-hash") is None


@pytest.mark.asyncio
async def test_duplicate_hash_raises_integrity_error(async_session):
    user = await _create_user(async_session)
    repository = RefreshTokenRepository(async_session)
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    await repository.create(
        user.user_id,
        "sha256-hash-duplicate",
        expires_at,
    )

    with pytest.raises(IntegrityError):
        async with async_session.begin_nested():
            await repository.create(
                user.user_id,
                "sha256-hash-duplicate",
                expires_at,
            )


@pytest.mark.asyncio
async def test_revoke_sets_utc_timestamp(async_session):
    user = await _create_user(async_session)
    repository = RefreshTokenRepository(async_session)
    refresh_token = await repository.create(
        user.user_id,
        "sha256-hash-revoke",
        datetime.now(timezone.utc) + timedelta(days=30),
    )

    revoked = await repository.revoke(refresh_token)

    assert revoked is refresh_token
    assert revoked.revoked_at is not None
    assert revoked.revoked_at.tzinfo is not None


@pytest.mark.asyncio
async def test_revoke_twice_preserves_first_timestamp(async_session):
    user = await _create_user(async_session)
    repository = RefreshTokenRepository(async_session)
    refresh_token = await repository.create(
        user.user_id,
        "sha256-hash-revoke-twice",
        datetime.now(timezone.utc) + timedelta(days=30),
    )

    await repository.revoke(refresh_token)
    first_revocation = refresh_token.revoked_at
    await repository.revoke(refresh_token)

    assert refresh_token.revoked_at == first_revocation


@pytest.mark.asyncio
async def test_deleting_user_cascades_to_refresh_tokens(async_session):
    user = await _create_user(async_session)
    repository = RefreshTokenRepository(async_session)
    await repository.create(
        user.user_id,
        "sha256-hash-cascade",
        datetime.now(timezone.utc) + timedelta(days=30),
    )

    await UserRepository(async_session).delete(user.user_id)
    token_count = await async_session.scalar(
        select(func.count())
        .select_from(RefreshToken)
        .where(RefreshToken.user_id == user.user_id)
    )

    assert token_count == 0
