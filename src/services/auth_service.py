"""Authentication use cases independent of the HTTP layer."""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from src.core.exceptions import (
    InvalidCredentials,
    InvalidToken,
    ResourceConflict,
    TokenExpired,
    TokenRevoked,
)
from src.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from src.repositories.models.refresh_token import RefreshToken
from src.repositories.models.user import User
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.repositories.user_repository import UserRepository


def _is_unique_violation(error: IntegrityError) -> bool:
    """Check the PostgreSQL unique-violation SQLSTATE through driver wrappers."""
    current: BaseException | None = error.orig
    visited: set[int] = set()

    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if (
            getattr(current, "sqlstate", None) == "23505"
            or getattr(current, "pgcode", None) == "23505"
        ):
            return True
        current = getattr(current, "__cause__", None)

    return False


class AuthService:
    """Implement registration and token lifecycle operations."""

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        secret: str,
        algorithm: str,
        access_token_expire_minutes: int,
        refresh_token_expire_days: int,
    ) -> None:
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository
        self.secret = secret
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    def _create_access_token(self, user_id: UUID) -> str:
        return create_access_token(
            user_id=user_id,
            secret=self.secret,
            algorithm=self.algorithm,
            lifetime=self.access_token_expire_minutes * 60,
        )

    async def register(self, email: str, password: str) -> User:
        """Create an account, translating a concurrent duplicate email."""
        normalized_email = self._normalize_email(email)
        existing_user = await self.user_repository.get_by_email(
            normalized_email
        )
        if existing_user is not None:
            raise ResourceConflict()

        password_hash = await asyncio.to_thread(hash_password, password)
        try:
            return await self.user_repository.create(
                email=normalized_email,
                password_hash=password_hash,
            )
        except IntegrityError as exc:
            if not _is_unique_violation(exc):
                raise
            raise ResourceConflict() from exc

    async def login(
        self,
        email: str,
        password: str,
    ) -> tuple[str, str]:
        """Authenticate credentials and create an access/refresh token pair."""
        normalized_email = self._normalize_email(email)
        user = await self.user_repository.get_by_email(normalized_email)

        if user is None:
            await asyncio.to_thread(hash_password, password)
            raise InvalidCredentials()

        is_valid = await asyncio.to_thread(
            verify_password,
            password,
            user.password_hash,
        )
        if not is_valid:
            raise InvalidCredentials()

        access_token = self._create_access_token(user.user_id)
        raw_refresh_token = generate_refresh_token()
        token_hash = hash_refresh_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.refresh_token_expire_days
        )
        await self.refresh_token_repository.create(
            user_id=user.user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return access_token, raw_refresh_token

    async def refresh(self, raw_refresh_token: str) -> str:
        """Issue a new access token for an active refresh token."""
        token_hash = hash_refresh_token(raw_refresh_token)
        refresh_token = await self.refresh_token_repository.get_by_hash(
            token_hash
        )
        if refresh_token is None:
            raise InvalidToken()
        if refresh_token.revoked_at is not None:
            raise TokenRevoked()
        if refresh_token.expires_at <= datetime.now(timezone.utc):
            raise TokenExpired()

        return self._create_access_token(refresh_token.user_id)

    async def logout(self, user: User, raw_refresh_token: str) -> None:
        """Idempotently revoke only an active token owned by this user."""
        token_hash = hash_refresh_token(raw_refresh_token)
        refresh_token = await self.refresh_token_repository.get_by_hash(
            token_hash
        )
        if (
            refresh_token is not None
            and refresh_token.revoked_at is None
            and refresh_token.user_id == user.user_id
        ):
            await self.refresh_token_repository.revoke(refresh_token)
