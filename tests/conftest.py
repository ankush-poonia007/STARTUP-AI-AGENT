# ============================================================
# TEST DATABASE CONFIGURATION
# ============================================================

# Responsibility:
#   Provides shared pytest configuration and fixtures.
#
# Flow:
#
#   pytest
#      │
#      ▼
#   TEST_DATABASE_URL
#      │
#      ▼
#   Local PostgreSQL
#      │
#      ▼
#   Alembic upgrade head
#      │
#      ▼
#   Test session
#      │
#      ▼
#   Test transaction
#      │
#      ▼
#   Test execution
#      │
#      ▼
#   Rollback
#
# Development DATABASE_URL is never used by tests.
# ============================================================


import asyncio
import os
import subprocess
from collections.abc import AsyncGenerator
from sqlalchemy.pool import NullPool

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.config import settings
from src.api.dependencies.auth import get_current_user
from src.api.dependencies.services import get_auth_service
from src.app import create_app
from src.infrastructure.database.session import get_db
from src.infrastructure.state_keys import (
    CHROMA_CLIENT_STATE_KEY,
    ENGINE_STATE_KEY,
)

# ============================================================
# TEST DATABASE URL
# ============================================================

# Read the dedicated local PostgreSQL test database URL.
#
# This must never point to the cloud development database.
TEST_DATABASE_URL = settings.TEST_DATABASE_URL


# ============================================================
# TEST DATABASE ENGINE
# ============================================================

# Create an async engine specifically for the test database.
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)


# Create sessions using the test database engine.
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class _HealthyChromaClient:
    def heartbeat(self) -> int:
        return 1


@pytest_asyncio.fixture
async def async_api(async_session: AsyncSession):
    """Provide an ASGI client with a rollback-scoped database session."""
    app = create_app()
    setattr(app.state, ENGINE_STATE_KEY, test_engine)
    setattr(
        app.state,
        CHROMA_CLIENT_STATE_KEY,
        _HealthyChromaClient(),
    )

    async def override_db() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    app.dependency_overrides[get_db] = override_db

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client, app


# ============================================================
# PYTEST CONFIGURATION
# ============================================================

def pytest_configure(config):
    """
    Prepare the test database before the test session starts.

    Flow:

        pytest starts
             ↓
        TEST_DATABASE_URL
             ↓
        Alembic
             ↓
        upgrade head
             ↓
        Test database ready
    """

    # Pass the local test database URL to Alembic.
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL

    # Apply all migrations to the test database.
    subprocess.run(
        ["alembic", "upgrade", "head"],
        env=env,
        check=True,
    )


# ============================================================
# ASYNC DATABASE SESSION
# ============================================================

@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a fresh transactional AsyncSession for each test.

    Flow:

        Test starts
             ↓
        Create AsyncSession
             ↓
        Begin transaction
             ↓
        Run test
             ↓
        Rollback
             ↓
        Close session
    """

    async with TestSessionLocal() as session:
        transaction = await session.begin()

        try:
            yield session
        finally:
            await transaction.rollback()

# ============================================================
# TEST DATABASE CLEANUP
# ============================================================

@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_test_engine():
    """
    Dispose the test database engine after the test session.
    """

    # Run all tests first.
    yield

    # Close all database connections.
    await test_engine.dispose()