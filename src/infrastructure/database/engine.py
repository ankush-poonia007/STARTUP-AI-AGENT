
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


# ============================================================
# DATABASE ENGINE FACTORY
# ============================================================
# Responsibility:
#   Create an asynchronous SQLAlchemy engine on demand.
#
# Why a factory?
#   Importing this module must not create database connections
#   or initialize infrastructure objects.
#
# The application startup layer will call this function later.


def create_database_engine(database_url: str) -> AsyncEngine:
    """
    Create an asynchronous database engine.

    Args:
        database_url: SQLAlchemy-compatible async database URL.

    Returns:
        An AsyncEngine configured for the supplied database.

    Note:
        This function creates the engine only when explicitly
        called. Importing this module does not create an engine.
    """
    return create_async_engine(database_url)


# ============================================================
# DATABASE SESSION FACTORY
# ============================================================
# Responsibility:
#   Create a session factory bound to an existing engine.
#
# Why separate this function?
#   The caller controls which engine the sessions use.
#   Tests can supply a test engine without changing globals.
#
# expire_on_commit=False keeps ORM attributes accessible
# after commit without automatically expiring their values.


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """
    Create an asynchronous SQLAlchemy session factory.

    Args:
        engine: The explicitly created database engine.

    Returns:
        A factory that creates AsyncSession instances.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
