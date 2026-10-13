
from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.state_keys import (
    DATABASE_SESSION_MAKER_STATE_KEY,
)


# ============================================================
# DATABASE SESSION DEPENDENCY
# ============================================================
# Responsibility:
#   Provide one AsyncSession for each FastAPI request.
#
# Lifecycle:
#   Retrieve factory -> create session -> yield session
#   -> commit on success / rollback on failure -> close
#
# The application factory will register the session factory
# on app.state during startup.
#
# This module must not create an engine or session factory
# during import.


async def get_db(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an application-configured database session.

    Raises:
        RuntimeError: If startup has not registered the factory.
    """

    # --------------------------------------------------------
    # Retrieve the session factory configured by application
    # startup. Never construct a factory inside this dependency.
    # --------------------------------------------------------
    session_factory = getattr(
        request.app.state,
        DATABASE_SESSION_MAKER_STATE_KEY,
        None,
    )

    # Fail clearly if application startup wiring did not run.
    if session_factory is None:
        raise RuntimeError(
            f"Required app.state.{DATABASE_SESSION_MAKER_STATE_KEY} "
            "is missing. Application startup wiring did not run."
        )

    # Create a fresh session for this request.
    session = session_factory()

    try:
        # ----------------------------------------------------
        # Provide the session to the route handler.
        # ----------------------------------------------------
        yield session

        # Commit only after successful route execution.
        await session.commit()

    except Exception:
        # Roll back pending changes if execution fails.
        await session.rollback()
        raise

    finally:
        # Always release the request's session resources.
        await session.close()
