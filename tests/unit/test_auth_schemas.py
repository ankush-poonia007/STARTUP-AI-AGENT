from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.api.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    UserResponse,
)


def test_register_validates_email_and_preserves_value_for_service():
    request = RegisterRequest(
        email="  User@Example.com  ",
        password="  password  ",
    )

    assert request.email == "  User@Example.com  "
    assert request.password == "  password  "


@pytest.mark.parametrize(
    "email",
    [
        "not-an-email",
        "",
        "a" * 244 + "@example.com",
    ],
)
def test_register_rejects_invalid_or_overlong_email(email):
    with pytest.raises(ValidationError):
        RegisterRequest(email=email, password="valid-password")


@pytest.mark.parametrize("password", ["short", "p" * 129])
def test_register_enforces_password_length(password):
    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", password=password)


def test_register_password_limits_are_inclusive():
    assert RegisterRequest(
        email="user@example.com",
        password="p" * 8,
    )
    assert RegisterRequest(
        email="user@example.com",
        password="p" * 128,
    )


def test_login_uses_loose_email_and_password_validation():
    request = LoginRequest(email="not an email", password="x")

    assert request.email == "not an email"
    assert request.password == "x"


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "", "password": "x"},
        {"email": "a" * 256, "password": "x"},
        {"email": "x", "password": ""},
        {"email": "x", "password": "p" * 129},
    ],
)
def test_login_enforces_only_length_bounds(payload):
    with pytest.raises(ValidationError):
        LoginRequest(**payload)


@pytest.mark.parametrize(
    "schema",
    [RefreshRequest, LogoutRequest],
)
def test_refresh_and_logout_token_length_bounds(schema):
    assert schema(refresh_token="x").refresh_token == "x"
    assert schema(refresh_token="t" * 512).refresh_token == "t" * 512

    with pytest.raises(ValidationError):
        schema(refresh_token="")
    with pytest.raises(ValidationError):
        schema(refresh_token="t" * 513)


def test_request_schemas_reject_server_controlled_fields():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="user@example.com",
            password="valid-password",
            user_id=str(uuid4()),
        )


def test_user_response_serializes_only_public_fields():
    user = type(
        "User",
        (),
        {
            "user_id": uuid4(),
            "email": "user@example.com",
            "created_at": datetime.now(timezone.utc),
            "password_hash": "must-not-appear",
        },
    )()

    response = UserResponse.model_validate(user)

    assert set(response.model_dump()) == {
        "user_id",
        "email",
        "created_at",
    }
    assert "password_hash" not in UserResponse.model_json_schema()["properties"]


def test_token_response_models_fix_token_type_to_bearer():
    pair = TokenPairResponse(
        access_token="access",
        refresh_token="refresh",
    )
    access = AccessTokenResponse(access_token="access")

    assert pair.token_type == access.token_type == "bearer"
    assert set(pair.model_dump()) == {
        "access_token",
        "refresh_token",
        "token_type",
    }
    assert set(access.model_dump()) == {"access_token", "token_type"}
