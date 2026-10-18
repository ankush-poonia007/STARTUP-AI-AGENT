"""Request-scoped providers for application services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.infrastructure.database.session import get_db
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService


def get_auth_service(
    session: AsyncSession = Depends(get_db),
) -> AuthService:
    """Build an auth service bound to this request's database session."""
    return AuthService(
        user_repository=UserRepository(session),
        refresh_token_repository=RefreshTokenRepository(session),
        secret=settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=(
            settings.access_token_expire_minutes
        ),
        refresh_token_expire_days=settings.refresh_token_expire_days,
    )
