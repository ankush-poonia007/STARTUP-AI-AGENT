import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_transaction_rollback(
    async_session: AsyncSession,
):
    await async_session.execute(
        text(
            "CREATE TABLE IF NOT EXISTS "
            "rollback_test (id INTEGER)"
        )
    )

    await async_session.execute(
        text(
            "INSERT INTO rollback_test VALUES (1)"
        )
    )