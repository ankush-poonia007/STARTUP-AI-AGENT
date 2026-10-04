import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_database_connection(
    async_session: AsyncSession,
):
    result = await async_session.execute(
        text("SELECT 1")
    )

    assert result.scalar_one() == 1