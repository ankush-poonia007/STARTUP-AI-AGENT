"""Authentication request and response schemas."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def _validate_email_format(value: str) -> str:
    """Validate email syntax without normalizing the submitted value."""
    try:
        validate_email(value.strip(), check_deliverability=False)
    except EmailNotValidError as exc:
        raise ValueError("Enter a valid email address.") from exc

    return value


RegisterEmail = Annotated[
    str,
    Field(max_length=255),
    AfterValidator(_validate_email_format),
]


class AuthRequest(BaseModel):
    """Base request that rejects fields controlled by the server."""

    model_config = ConfigDict(extra="forbid")


class RegisterRequest(AuthRequest):
    """Registration input with strict email and password validation."""

    email: RegisterEmail
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(AuthRequest):
    """Login input keeps validation loose for uniform auth failures."""

    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(AuthRequest):
    """Refresh-token input."""

    refresh_token: str = Field(min_length=1, max_length=512)


class LogoutRequest(RefreshRequest):
    """Logout uses the same refresh-token input contract."""


class UserResponse(BaseModel):
    """Public user fields; password hashes are never serialized."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: str
    created_at: datetime


class TokenPairResponse(BaseModel):
    """Access and refresh tokens returned after authentication."""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class AccessTokenResponse(BaseModel):
    """New access token returned when refreshing a session."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
