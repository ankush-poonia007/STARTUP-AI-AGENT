from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from starlette.exceptions import HTTPException as StarletteHTTPException

import src.api.dependencies.auth as auth_dependency
from src.api.dependencies.auth import get_current_user
from src.core.exceptions import (
    AppException,
    AuthenticationRequired,
    InvalidToken,
    TokenExpired,
)
from src.core.security import create_access_token
from src.infrastructure.database.session import get_db
from src.middleware.exception_handler import (
    app_exception_handler,
    http_exception_handler,
)

TEST_SECRET = "test-signing-secret-with-at-least-32-bytes"


def _make_test_app(user):
    app = FastAPI()
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )

    async def override_db():
        yield object()

    app.dependency_overrides[get_db] = override_db

    @app.get("/test/me")
    async def read_me(current_user=Depends(get_current_user)):
        return {"user_id": str(current_user.user_id)}

    return app, user


def _token(user_id=None, *, secret=None, lifetime=60):
    return create_access_token(
        user_id or uuid4(),
        secret=secret or TEST_SECRET,
        algorithm="HS256",
        lifetime=lifetime,
    )


@pytest.fixture
def auth_client(monkeypatch):
    monkeypatch.setattr(
        auth_dependency,
        "settings",
        SimpleNamespace(
            jwt_secret_key=SecretStr(TEST_SECRET),
            jwt_algorithm="HS256",
        ),
    )
    user_id = uuid4()
    user = SimpleNamespace(user_id=user_id)
    app, _ = _make_test_app(user)
    lookup = AsyncMock(return_value=user)
    with patch(
        "src.api.dependencies.auth.UserRepository.get_by_id",
        lookup,
    ):
        with TestClient(app) as client:
            yield client, user_id, lookup, user


def test_get_current_user_returns_user_from_repository(auth_client):
    client, user_id, lookup, user = auth_client

    response = client.get(
        "/test/me",
        headers={"Authorization": f"Bearer {_token(user_id)}"},
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": str(user_id)}
    lookup.assert_awaited_once()
    assert lookup.await_args.args[0] == user_id


@pytest.mark.parametrize(
    "authorization",
    [None, "Basic dXNlcjpwYXNz"],
)
def test_missing_or_wrong_scheme_requires_authentication(
    auth_client,
    authorization,
):
    client, _, lookup, _ = auth_client
    headers = {}
    if authorization is not None:
        headers["Authorization"] = authorization

    response = client.get("/test/me", headers=headers)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    lookup.assert_not_awaited()


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        _token(secret="incorrect-signing-secret-with-at-least-32-bytes"),
        jwt.encode(
            {
                "sub": str(uuid4()),
                "iat": 1,
                "exp": 4_102_444_800,
            },
            TEST_SECRET,
            algorithm="HS256",
        ),
        jwt.encode(
            {
                "sub": str(uuid4()),
                "token_type": "refresh",
                "iat": 1,
                "exp": 4_102_444_800,
            },
            TEST_SECRET,
            algorithm="HS256",
        ),
    ],
)
def test_invalid_token_is_rejected(auth_client, token):
    client, _, lookup, _ = auth_client

    response = client.get(
        "/test/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
    lookup.assert_not_awaited()


def test_expired_token_keeps_expired_code(auth_client):
    client, user_id, lookup, _ = auth_client

    response = client.get(
        "/test/me",
        headers={
            "Authorization": f"Bearer {_token(user_id, lifetime=-60)}"
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"
    lookup.assert_not_awaited()


@pytest.mark.parametrize("subject", ["not-a-uuid", None])
def test_invalid_subject_is_rejected(auth_client, subject):
    client, _, lookup, _ = auth_client
    claims = {
        "sub": subject,
        "token_type": "access",
        "iat": 1,
        "exp": 4_102_444_800,
    }
    token = jwt.encode(
        claims,
        TEST_SECRET,
        algorithm="HS256",
    )

    response = client.get(
        "/test/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
    lookup.assert_not_awaited()


def test_deleted_user_is_invalid_token(auth_client):
    client, user_id, lookup, _ = auth_client
    lookup.return_value = None

    response = client.get(
        "/test/me",
        headers={"Authorization": f"Bearer {_token(user_id)}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
