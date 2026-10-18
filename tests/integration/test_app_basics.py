
"""Integration tests for request IDs and API exception handlers."""

import logging
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions import (
    AppException,
    AuthenticationRequired,
    FileTooLarge,
    Forbidden,
    InvalidCredentials,
    InvalidToken,
    RateLimited,
    ResourceConflict,
    ResourceNotFound,
    TokenExpired,
    TokenRevoked,
    UnsupportedFileType,
)
from src.middleware.exception_handler import (
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.middleware.request_id import RequestIDMiddleware

REQUEST_ID_HEADER = "X-Request-ID"


class PasswordRequest(BaseModel):
    password: str = Field(min_length=8)


def create_test_app() -> FastAPI:
    """Build an isolated app without modifying the production app."""
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
    app.add_exception_handler(
        __import__(
            "fastapi.exceptions",
            fromlist=["RequestValidationError"],
        ).RequestValidationError,
        validation_exception_handler,
    )

    @app.get("/test/success")
    async def success():
        return {"status": "ok"}

    @app.post("/test/password")
    async def validate_password(payload: PasswordRequest):
        return {"status": "accepted"}

    @app.get("/test/crash")
    async def crash():
        raise RuntimeError("PRIVATE_INTERNAL_DIAGNOSTIC")

    return app


@pytest.fixture
def client():
    app = create_test_app()

    # Required: let the 500 handler return its response to the client.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def assert_error_envelope(response, expected_status, expected_code):
    assert response.status_code == expected_status

    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "request_id"}

    assert body["error"]["code"] == expected_code
    assert body["error"]["request_id"]
    assert response.headers[REQUEST_ID_HEADER] == body["error"]["request_id"]


def test_success_propagates_request_id(client):
    supplied_id = "trace-123"

    response = client.get(
        "/test/success",
        headers={REQUEST_ID_HEADER: supplied_id},
    )

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == supplied_id


def test_missing_request_id_is_generated(client):
    response = client.get("/test/success")

    assert response.status_code == 200
    generated_id = response.headers[REQUEST_ID_HEADER]
    assert str(uuid4().__class__(generated_id)) == generated_id


def test_unknown_route_returns_not_found(client):
    response = client.get("/route-that-does-not-exist")

    assert_error_envelope(response, 404, "NOT_FOUND")


def test_wrong_method_returns_method_not_allowed(client):
    response = client.post("/test/success")

    assert_error_envelope(response, 405, "METHOD_NOT_ALLOWED")


@pytest.mark.parametrize(
    "exception_type",
    [
        AuthenticationRequired,
        InvalidCredentials,
        InvalidToken,
        TokenExpired,
        TokenRevoked,
        Forbidden,
        ResourceNotFound,
        ResourceConflict,
        FileTooLarge,
        UnsupportedFileType,
        RateLimited,
    ],
)
def test_application_exception_types(exception_type):
    app = create_test_app()

    @app.get("/test/app-exception")
    async def raise_application_exception():
        raise exception_type()

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/test/app-exception")

    expected = exception_type()
    assert_error_envelope(
        response,
        expected.status_code,
        expected.code,
    )
    assert response.json()["error"]["message"] == expected.message


def test_application_exception_preserves_headers():
    app = create_test_app()

    @app.get("/test/custom-exception")
    async def raise_custom_exception():
        raise AppException(
            message="A controlled application error.",
            headers={"X-Test-Error": "preserved"},
        )

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/test/custom-exception")

    assert response.headers["X-Test-Error"] == "preserved"


def test_short_password_is_not_exposed_or_logged(client, caplog):
    submitted_password = "tiny"

    with caplog.at_level(logging.WARNING):
        response = client.post(
            "/test/password",
            json={"password": submitted_password},
        )

    assert_error_envelope(response, 422, "VALIDATION_ERROR")
    assert "password:" in response.json()["error"]["message"]
    assert submitted_password not in response.text
    assert submitted_password not in caplog.text


def test_unhandled_exception_returns_safe_500(client, caplog):
    with caplog.at_level(logging.ERROR):
        response = client.get("/test/crash")

    assert_error_envelope(response, 500, "INTERNAL_ERROR")
    assert response.json()["error"]["message"] == (
        "An internal error occurred."
    )
    assert "PRIVATE_INTERNAL_DIAGNOSTIC" not in response.text
    assert "PRIVATE_INTERNAL_DIAGNOSTIC" in caplog.text

    request_id = response.json()["error"]["request_id"]
    assert request_id in caplog.text
    assert "GET" in caplog.text
    assert "/test/crash" in caplog.text
