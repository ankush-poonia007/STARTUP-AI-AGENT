from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import DATABASE_URL


# ============================================================
# ASYNC DATABASE ENGINE
# ============================================================
# Creates the async SQLAlchemy engine using the configured
# PostgreSQL database URL.

engine = create_async_engine(
    DATABASE_URL,
)


# ============================================================
# ASYNC SESSION FACTORY
# ============================================================
# Creates AsyncSession instances for database operations.
#
# expire_on_commit=False keeps ORM attributes accessible
# after commit without triggering another database query.

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)