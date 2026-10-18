"""Route-level tests for authentication endpoints."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.services import get_auth_service
from src.api.routers.auth import router as auth_router
from src.core.exceptions import (
    AppException,
    InvalidCredentials,
    ResourceConflict,
    TokenExpired,
    TokenRevoked,
)
from src.middleware.exception_handler import (
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.middleware.request_id import RequestIDMiddleware


@pytest.fixture
def auth_api():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )
    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )
    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.include_router(auth_router, prefix="/api/v1")

    user = SimpleNamespace(
        user_id=uuid4(),
        email="user@example.com",
        created_at=datetime.now(timezone.utc),
        password_hash="must-not-be-serialized",
    )
    service = SimpleNamespace(
        register=AsyncMock(return_value=user),
        login=AsyncMock(return_value=("access", "refresh")),
        refresh=AsyncMock(return_value="new-access"),
        logout=AsyncMock(return_value=None),
    )
    app.dependency_overrides[get_auth_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: user

    with TestClient(app) as client:
        yield client, service, user, app


def test_register_returns_201_and_public_user(auth_api):
    client, service, user, _ = auth_api

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "valid-password"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "user_id": str(user.user_id),
        "email": user.email,
        "created_at": user.created_at.isoformat().replace("+00:00", "Z"),
    }
    assert "password_hash" not in response.text
    service.register.assert_awaited_once_with(
        "user@example.com",
        "valid-password",
    )


def test_register_conflict_uses_error_envelope(auth_api):
    client, service, _, _ = auth_api
    service.register.side_effect = ResourceConflict()

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "valid-password"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESOURCE_CONFLICT"


def test_login_returns_token_pair(auth_api):
    client, service, _, _ = auth_api

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "access",
        "refresh_token": "refresh",
        "token_type": "bearer",
    }
    service.login.assert_awaited_once_with(
        "user@example.com",
        "password",
    )


def test_login_failure_uses_invalid_credentials_envelope(auth_api):
    client, service, _, _ = auth_api
    service.login.side_effect = InvalidCredentials()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.parametrize(
    ("exception", "code"),
    [
        (TokenExpired(), "TOKEN_EXPIRED"),
        (TokenRevoked(), "TOKEN_REVOKED"),
    ],
)
def test_refresh_failure_codes(auth_api, exception, code):
    client, service, _, _ = auth_api
    service.refresh.side_effect = exception

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "refresh"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == code


def test_refresh_returns_access_token(auth_api):
    client, service, _, _ = auth_api

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "refresh"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access",
        "token_type": "bearer",
    }
    service.refresh.assert_awaited_once_with("refresh")


def test_logout_returns_empty_object_and_calls_service(auth_api):
    client, service, user, _ = auth_api

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "refresh"},
    )

    assert response.status_code == 200
    assert response.json() == {}
    service.logout.assert_awaited_once_with(user, "refresh")


def test_me_returns_public_user(auth_api):
    client, _, user, _ = auth_api

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["user_id"] == str(user.user_id)
    assert "password_hash" not in response.text


def test_auth_routes_and_safe_schemas_are_in_openapi(auth_api):
    _, _, _, app = auth_api
    schema = app.openapi()
    paths = schema["paths"]

    assert {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/me",
    } <= paths.keys()
    assert "password_hash" not in str(schema["components"]["schemas"])
