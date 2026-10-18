"""Authentication dependencies for protected API routes."""

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import AuthenticationRequired, InvalidToken
from src.core.security import decode_access_token
from src.infrastructure.database.session import get_db
from src.repositories.models.user import User
from src.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        _bearer_scheme
    ),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Validate the bearer access token and return its existing user."""
    if credentials is None:
        raise AuthenticationRequired()

    claims = decode_access_token(
        credentials.credentials,
        secret=settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    try:
        user_id = UUID(claims["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidToken() from exc

    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise InvalidToken()

    return user
