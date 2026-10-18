from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from src.core.exceptions import (
    InvalidCredentials,
    InvalidToken,
    ResourceConflict,
    TokenExpired,
    TokenRevoked,
)
from src.core.security import hash_refresh_token
from src.services.auth_service import AuthService

SECRET = "test-secret-with-at-least-32-characters"


@pytest.fixture
def repositories():
    return AsyncMock(), AsyncMock()


@pytest.fixture
def service(repositories):
    users, tokens = repositories
    return AuthService(
        user_repository=users,
        refresh_token_repository=tokens,
        secret=SECRET,
        algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=30,
    )


@pytest.mark.asyncio
async def test_register_normalizes_email_and_hashes_in_worker(service, repositories):
    users, _ = repositories
    user = SimpleNamespace(user_id=uuid4())
    users.get_by_email.return_value = None
    users.create.return_value = user

    with patch(
        "src.services.auth_service.asyncio.to_thread",
        new=AsyncMock(return_value="argon-hash"),
    ) as to_thread:
        result = await service.register("  User@Example.COM ", " pass word ")

    assert result is user
    users.get_by_email.assert_awaited_once_with("user@example.com")
    to_thread.assert_awaited_once()
    assert to_thread.await_args.args[1:] == (" pass word ",)
    users.create.assert_awaited_once_with(
        email="user@example.com",
        password_hash="argon-hash",
    )


@pytest.mark.asyncio
async def test_register_existing_email_conflicts_without_hashing(
    service,
    repositories,
):
    users, _ = repositories
    users.get_by_email.return_value = object()

    with patch("src.services.auth_service.asyncio.to_thread") as to_thread:
        with pytest.raises(ResourceConflict):
            await service.register("USER@example.com", "password")

    to_thread.assert_not_called()
    users.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_register_race_unique_violation_becomes_conflict(service, repositories):
    users, _ = repositories
    users.get_by_email.return_value = None
    users.create.side_effect = IntegrityError(
        "INSERT",
        {},
        SimpleNamespace(sqlstate="23505"),
    )

    with (
        patch(
            "src.services.auth_service.asyncio.to_thread",
            new=AsyncMock(return_value="argon-hash"),
        ),
        pytest.raises(ResourceConflict),
    ):
        await service.register("user@example.com", "password")

    users.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_non_unique_integrity_error_bubbles(service, repositories):
    users, _ = repositories
    users.get_by_email.return_value = None
    users.create.side_effect = IntegrityError(
        "INSERT",
        {},
        SimpleNamespace(sqlstate="23503"),
    )

    with (
        patch(
            "src.services.auth_service.asyncio.to_thread",
            new=AsyncMock(return_value="argon-hash"),
        ),
        pytest.raises(IntegrityError),
    ):
        await service.register("user@example.com", "password")


@pytest.mark.asyncio
async def test_login_unknown_email_hashes_then_raises(service, repositories):
    users, _ = repositories
    users.get_by_email.return_value = None
    thread_result = AsyncMock()

    with patch(
        "src.services.auth_service.asyncio.to_thread",
        thread_result,
    ) as to_thread:
        with pytest.raises(InvalidCredentials) as error:
            await service.login(" USER@example.com ", "password")

    users.get_by_email.assert_awaited_once_with("user@example.com")
    to_thread.assert_awaited_once()
    assert to_thread.await_args.args[1:] == ("password",)
    assert str(error.value) == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_wrong_password_uses_same_failure(service, repositories):
    users, _ = repositories
    users.get_by_email.return_value = SimpleNamespace(
        user_id=uuid4(),
        password_hash="stored-hash",
    )

    with patch(
        "src.services.auth_service.asyncio.to_thread",
        new=AsyncMock(return_value=False),
    ) as to_thread:
        with pytest.raises(InvalidCredentials) as error:
            await service.login("USER@example.com", "bad-password")

    to_thread.assert_awaited_once()
    assert str(error.value) == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_creates_token_pair_and_stores_only_hash(service, repositories):
    users, tokens = repositories
    user_id = uuid4()
    users.get_by_email.return_value = SimpleNamespace(
        user_id=user_id,
        password_hash="stored-hash",
    )

    with (
        patch(
            "src.services.auth_service.asyncio.to_thread",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "src.services.auth_service.generate_refresh_token",
            return_value="raw-refresh-token",
        ),
        patch(
            "src.services.auth_service.create_access_token",
            return_value="access-token",
        ) as create_access,
    ):
        access_token, raw_token = await service.login(
            "user@example.com",
            "password",
        )

    assert (access_token, raw_token) == (
        "access-token",
        "raw-refresh-token",
    )
    create_access.assert_called_once_with(
        user_id=user_id,
        secret=SECRET,
        algorithm="HS256",
        lifetime=900,
    )
    tokens.create.assert_awaited_once()
    token_hash = tokens.create.await_args.kwargs["token_hash"]
    assert token_hash == hash_refresh_token("raw-refresh-token")
    assert tokens.create.await_args.kwargs["user_id"] == user_id
    expiry = tokens.create.await_args.kwargs["expires_at"]
    assert expiry.tzinfo is not None
    assert timedelta(days=29, hours=23) < (
        expiry - datetime.now(timezone.utc)
    ) <= timedelta(days=30)
    assert "raw-refresh-token" not in repr(tokens.create.await_args)


@pytest.mark.asyncio
async def test_refresh_unknown_token_is_invalid(service, repositories):
    _, tokens = repositories
    tokens.get_by_hash.return_value = None

    with pytest.raises(InvalidToken):
        await service.refresh("unknown")

    tokens.get_by_hash.assert_awaited_once_with(hash_refresh_token("unknown"))


@pytest.mark.asyncio
async def test_refresh_revoked_token_is_rejected(service, repositories):
    _, tokens = repositories
    tokens.get_by_hash.return_value = SimpleNamespace(
        revoked_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        user_id=uuid4(),
    )

    with pytest.raises(TokenRevoked):
        await service.refresh("revoked")


@pytest.mark.asyncio
async def test_refresh_expired_token_is_rejected(service, repositories):
    _, tokens = repositories
    tokens.get_by_hash.return_value = SimpleNamespace(
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        user_id=uuid4(),
    )

    with pytest.raises(TokenExpired):
        await service.refresh("expired")


@pytest.mark.asyncio
async def test_refresh_active_token_returns_access_token_without_rotation(
    service,
    repositories,
):
    _, tokens = repositories
    user_id = uuid4()
    tokens.get_by_hash.return_value = SimpleNamespace(
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        user_id=user_id,
    )

    with patch(
        "src.services.auth_service.create_access_token",
        return_value="new-access-token",
    ) as create_access:
        result = await service.refresh("active")

    assert result == "new-access-token"
    create_access.assert_called_once_with(
        user_id=user_id,
        secret=SECRET,
        algorithm="HS256",
        lifetime=900,
    )
    tokens.create.assert_not_awaited()
    tokens.revoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_logout_revokes_only_owned_active_token(service, repositories):
    _, tokens = repositories
    user_id = uuid4()
    token = SimpleNamespace(
        user_id=user_id,
        revoked_at=None,
    )
    tokens.get_by_hash.return_value = token
    user = SimpleNamespace(user_id=user_id)

    await service.logout(user, "owned")

    tokens.get_by_hash.assert_awaited_once_with(hash_refresh_token("owned"))
    tokens.revoke.assert_awaited_once_with(token)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token",
    [
        None,
        SimpleNamespace(user_id=uuid4(), revoked_at=None),
        SimpleNamespace(user_id=uuid4(), revoked_at=datetime.now(timezone.utc)),
    ],
)
async def test_logout_ignores_missing_foreign_or_revoked_tokens(
    service,
    repositories,
    token,
):
    _, tokens = repositories
    tokens.get_by_hash.return_value = token

    await service.logout(
        SimpleNamespace(user_id=uuid4()),
        "not-owned-active",
    )

    tokens.revoke.assert_not_awaited()
