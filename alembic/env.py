from logging.config import fileConfig
import asyncio

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from src.config import settings
from src.repositories.base import Base

# Import all models so SQLAlchemy registers them
# with Base.metadata for Alembic autogeneration.
from src.repositories.models import (
    user,
    startup,
    conversation,
    message,
    memory,
)


# ============================================================
# ALEMBIC CONFIGURATION
# ============================================================
# Provides access to alembic.ini configuration.

config = context.config


# ============================================================
# DATABASE URL
# ============================================================
# Alembic receives the database URL from application settings.
#
# Alembic migrations use the synchronous PostgreSQL driver.
# The application itself uses asyncpg.

database_url = settings.DATABASE_URL

config.set_main_option(
    "sqlalchemy.url",
    database_url,
)


# ============================================================
# LOGGING CONFIGURATION
# ============================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================================
# TARGET METADATA
# ============================================================
# Alembic compares this metadata against the database schema.
# All model modules must be imported above.

target_metadata = Base.metadata


# ============================================================
# OFFLINE MIGRATIONS
# ============================================================

def run_migrations_offline() -> None:
    """
    Run migrations without establishing a database connection.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# ONLINE MIGRATIONS
# ============================================================

def do_run_migrations(connection) -> None:
    """
    Configure Alembic using an active database connection.
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations using SQLAlchemy's asynchronous engine.
    """

    connectable = async_engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            do_run_migrations,
        )

    await connectable.dispose()


# ============================================================
# MIGRATION ENTRY POINT
# ============================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(
        run_migrations_online(),
    )