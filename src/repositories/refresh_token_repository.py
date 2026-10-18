from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Database operations for refresh-token records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Insert a refresh-token record without committing the transaction."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(refresh_token)
        await self.session.flush()
        return refresh_token

    async def get_by_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        """Find the record matching a token hash."""
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash
            )
        )
        return result.scalar_one_or_none()

    async def revoke(
        self,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        """Revoke a token once, preserving its original revocation time."""
        if refresh_token.revoked_at is None:
            refresh_token.revoked_at = datetime.now(timezone.utc)
            await self.session.flush()
        return refresh_token
