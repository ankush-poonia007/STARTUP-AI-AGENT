"""End-to-end auth API tests against the rollback-per-test database fixture."""

import asyncio
import base64
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import jwt
import pytest
from sqlalchemy import select

from src.core.config import settings
from src.core.security import (
    create_access_token,
    hash_refresh_token,
)
from src.repositories.models.refresh_token import RefreshToken
from src.repositories.models.user import User
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.repositories.user_repository import UserRepository
from tests.conftest import TestSessionLocal, test_engine
from src.app import create_app
from src.infrastructure.state_keys import (
    CHROMA_CLIENT_STATE_KEY,
    ENGINE_STATE_KEY,
    SESSION_FACTORY_STATE_KEY,
)

PASSWORD = "correct horse battery staple"


async def _register(client: httpx.AsyncClient, email: str | None = None):
    email = email or f"{uuid4().hex}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD},
    )
    return email, response


async def _login(
    client: httpx.AsyncClient,
    email: str,
    password: str = PASSWORD,
):
    return await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


async def _logged_in_user(client: httpx.AsyncClient):
    email, registration = await _register(client)
    assert registration.status_code == 201
    login = await _login(client, email)
    assert login.status_code == 200
    return email, registration.json(), login.json()


async def _get_user(async_session, email: str) -> User:
    return await UserRepository(async_session).get_by_email(email)


def _auth(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


@pytest.mark.asyncio
async def test_register_persists_normalized_user_and_argon2_hash(
    async_api,
    async_session,
):
    client, _ = async_api
    password = "password with spaces"
    email = f"Mixed-{uuid4().hex}@Example.COM"

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"user_id", "email", "created_at"}
    assert body["email"] == email.lower()
    assert "password_hash" not in response.text

    user = await _get_user(async_session, email.lower())
    assert user is not None
    assert user.password_hash.startswith("$argon2id$")
    assert user.password_hash != password


@pytest.mark.asyncio
async def test_register_duplicate_and_case_variant_return_conflict(async_api):
    client, _ = async_api
    email = f"Case-{uuid4().hex}@Example.com"

    first = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD},
    )
    exact_duplicate = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD},
    )
    case_duplicate = await client.post(
        "/api/v1/auth/register",
        json={"email": email.swapcase(), "password": PASSWORD},
    )

    assert first.status_code == 201
    for response in (exact_duplicate, case_duplicate):
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "RESOURCE_CONFLICT"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("notanemail", PASSWORD),
        ("valid@example.com", "short"),
        ("valid@example.com", "p" * 129),
    ],
)
async def test_register_validation_errors(async_api, email, password):
    client, _ = async_api
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_register_race_unique_violation_returns_conflict(
    async_api,
    monkeypatch,
):
    client, _ = async_api
    email = f"race-{uuid4().hex}@example.com"
    existing = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD},
    )
    assert existing.status_code == 201

    async def miss_precheck(self, normalized_email):
        return None

    monkeypatch.setattr(
        UserRepository,
        "get_by_email",
        miss_precheck,
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESOURCE_CONFLICT"


@pytest.mark.asyncio
async def test_login_success_hash_storage_casefold_and_multiple_sessions(
    async_api,
    async_session,
):
    client, _ = async_api
    email, registration = await _register(client)
    assert registration.status_code == 201

    first_login = await _login(client, email.upper())
    second_login = await _login(client, email)

    assert first_login.status_code == second_login.status_code == 200
    first_body = first_login.json()
    assert set(first_body) == {
        "access_token",
        "refresh_token",
        "token_type",
    }
    assert first_body["token_type"] == "bearer"

    first_record = await RefreshTokenRepository(async_session).get_by_hash(
        hash_refresh_token(first_body["refresh_token"])
    )
    assert first_record is not None
    assert first_record.token_hash != first_body["refresh_token"]
    assert len(first_record.token_hash) == 64

    user = await _get_user(async_session, email)
    active_tokens = (
        await async_session.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user.user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
    ).all()
    assert len(active_tokens) == 2


@pytest.mark.asyncio
async def test_login_failure_is_uniform_and_short_password_is_auth_failure(
    async_api,
):
    client, _ = async_api
    email, registration = await _register(client)
    assert registration.status_code == 201

    wrong_password = await _login(client, email, "wrong password")
    wrong_email = await _login(
        client,
        f"unknown-{uuid4().hex}@example.com",
        "wrong password",
    )
    short_password = await _login(client, email, "x")

    assert wrong_password.status_code == wrong_email.status_code == 401
    assert wrong_password.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert (
        wrong_password.json()["error"]["code"]
        == wrong_email.json()["error"]["code"]
    )
    assert (
        wrong_password.json()["error"]["message"]
        == wrong_email.json()["error"]["message"]
    )
    assert short_password.status_code == 401
    assert short_password.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_real_concurrent_registration_has_one_winner_and_cleans_user():
    app = create_app()
    setattr(app.state, ENGINE_STATE_KEY, test_engine)
    setattr(
        app.state,
        CHROMA_CLIENT_STATE_KEY,
        type("HealthyChroma", (), {"heartbeat": lambda self: 1})(),
    )
    setattr(app.state, SESSION_FACTORY_STATE_KEY, TestSessionLocal)
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    email = f"concurrent-{uuid4().hex}@example.com"
    payload = {"email": email, "password": PASSWORD}

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        responses = await asyncio.gather(
            client.post("/api/v1/auth/register", json=payload),
            client.post("/api/v1/auth/register", json=payload),
        )

    assert sorted(response.status_code for response in responses) == [201, 409]

    async with TestSessionLocal() as cleanup_session:
        user = await UserRepository(cleanup_session).get_by_email(email)
        assert user is not None
        await UserRepository(cleanup_session).delete(user.user_id)
        await cleanup_session.commit()


@pytest.mark.asyncio
async def test_me_rejects_missing_wrong_expired_tampered_and_invalid_tokens(
    async_api,
):
    client, _ = async_api
    email, registration, login = await _logged_in_user(client)
    access_token = login["access_token"]
    valid_user = await client.get(
        "/api/v1/auth/me",
        headers=_auth(access_token),
    )
    assert valid_user.status_code == 200
    assert valid_user.json()["user_id"] == registration["user_id"]

    no_header = await client.get("/api/v1/auth/me")
    wrong_scheme = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Token abc"},
    )
    assert no_header.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert wrong_scheme.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    user_id = registration["user_id"]
    expired = create_access_token(
        user_id,
        settings.jwt_secret_key.get_secret_value(),
        settings.jwt_algorithm,
        -60,
    )
    invalid_tokens = [
        expired,
        jwt.encode(
            {
                "sub": user_id,
                "token_type": "access",
                "iat": 1,
                "exp": 4_102_444_800,
            },
            "different-test-secret",
            algorithm="HS256",
        ),
        login["refresh_token"],
    ]

    tampered = list(access_token)
    tampered[len(tampered) // 2] = (
        "A" if tampered[len(tampered) // 2] != "A" else "B"
    )
    invalid_tokens.append("".join(tampered))

    invalid_tokens.append(
        jwt.encode(
            {
                "sub": user_id,
                "token_type": "refresh",
                "iat": 1,
                "exp": 4_102_444_800,
            },
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        )
    )
    invalid_tokens.append(
        jwt.encode(
            {
                "token_type": "access",
                "iat": 1,
                "exp": 4_102_444_800,
            },
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        )
    )
    invalid_tokens.append(
        jwt.encode(
            {
                "sub": "not-a-uuid",
                "token_type": "access",
                "iat": 1,
                "exp": 4_102_444_800,
            },
            settings.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        )
    )

    unsigned_header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    unsigned_payload = base64.urlsafe_b64encode(
        json.dumps(
            {
                "sub": user_id,
                "token_type": "access",
                "iat": 1,
                "exp": 4_102_444_800,
            }
        ).encode()
    ).rstrip(b"=").decode()
    invalid_tokens.append(f"{unsigned_header}.{unsigned_payload}.")

    expired_response = await client.get(
        "/api/v1/auth/me",
        headers=_auth(expired),
    )
    assert expired_response.status_code == 401
    assert expired_response.json()["error"]["code"] == "TOKEN_EXPIRED"

    for token in invalid_tokens[1:]:
        response = await client.get(
            "/api/v1/auth/me",
            headers=_auth(token),
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_me_rejects_deleted_user(async_api, async_session):
    client, _ = async_api
    email, registration, login = await _logged_in_user(client)
    user = await _get_user(async_session, email)
    await UserRepository(async_session).delete(user.user_id)

    response = await client.get(
        "/api/v1/auth/me",
        headers=_auth(login["access_token"]),
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_refresh_success_unknown_revoked_expired_and_no_write(
    async_api,
    async_session,
):
    client, _ = async_api
    email, registration, login = await _logged_in_user(client)
    raw_token = login["refresh_token"]
    token_repo = RefreshTokenRepository(async_session)
    token_record = await token_repo.get_by_hash(
        hash_refresh_token(raw_token)
    )
    before = (token_record.revoked_at, token_record.updated_at)

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": raw_token},
    )
    assert refresh_response.status_code == 200
    access_response = await client.get(
        "/api/v1/auth/me",
        headers=_auth(refresh_response.json()["access_token"]),
    )
    assert access_response.status_code == 200
    assert access_response.json()["user_id"] == registration["user_id"]
    assert (token_record.revoked_at, token_record.updated_at) == before

    unknown = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "unknown-refresh-token"},
    )
    assert unknown.status_code == 401
    assert unknown.json()["error"]["code"] == "INVALID_TOKEN"

    expired_raw = f"expired-{uuid4().hex}"
    await token_repo.create(
        user_id=registration["user_id"],
        token_hash=hash_refresh_token(expired_raw),
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    expired = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_raw},
    )
    assert expired.status_code == 401
    assert expired.json()["error"]["code"] == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_logout_idempotent_unknown_and_other_users_token(
    async_api,
    async_session,
):
    client, _ = async_api
    email_a, registration_a, login_a = await _logged_in_user(client)
    email_b, registration_b_response = await _register(client)
    assert registration_b_response.status_code == 201
    login_b_response = await _login(client, email_b)
    assert login_b_response.status_code == 200
    login_b = login_b_response.json()

    headers_a = _auth(login_a["access_token"])
    logout = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login_a["refresh_token"]},
        headers=headers_a,
    )
    logout_twice = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login_a["refresh_token"]},
        headers=headers_a,
    )
    missing_access = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login_a["refresh_token"]},
    )
    unknown = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "unknown-refresh"},
        headers=headers_a,
    )
    foreign_token = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login_b["refresh_token"]},
        headers=headers_a,
    )

    assert logout.status_code == logout_twice.status_code == 200
    assert logout.json() == logout_twice.json() == {}
    assert missing_access.status_code == 401
    assert unknown.status_code == foreign_token.status_code == 200

    repo = RefreshTokenRepository(async_session)
    token_a = await repo.get_by_hash(hash_refresh_token(login_a["refresh_token"]))
    token_b = await repo.get_by_hash(hash_refresh_token(login_b["refresh_token"]))
    assert token_a.revoked_at is not None
    assert token_b.revoked_at is None

    revoked_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_a["refresh_token"]},
    )
    assert revoked_refresh.status_code == 401
    assert revoked_refresh.json()["error"]["code"] == "TOKEN_REVOKED"
