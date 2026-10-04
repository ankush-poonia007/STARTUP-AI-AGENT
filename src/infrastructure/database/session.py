from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.engine import async_session_maker


# ============================================================
# DATABASE SESSION DEPENDENCY
# ============================================================
# Provides one AsyncSession for each FastAPI request.
#
# Lifecycle:
#   Setup → yield session → commit / rollback → close
#
# The yield separates route execution from cleanup.

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session = async_session_maker()

    try:
        # ----------------------------------------------------
        # Provide session to the route handler.
        # ----------------------------------------------------
        yield session

        # ----------------------------------------------------
        # Commit when the route completes successfully.
        # ----------------------------------------------------
        await session.commit()

    except Exception:
        # ----------------------------------------------------
        # Roll back any uncommitted changes on failure.
        # ----------------------------------------------------
        await session.rollback()
        raise

    finally:
        # ----------------------------------------------------
        # Always release the database session.
        # ----------------------------------------------------
        await session.close()