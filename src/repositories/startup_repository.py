# ============================================================
# STARTUP REPOSITORY
# ============================================================
#
# Responsibility:
#   Handles database operations for the Startup model.
#
# Flow:
#
#   API / Service
#        │
#        ▼
#   StartupRepository
#        │
#        ▼
#   AsyncSession
#        │
#        ▼
#   PostgreSQL
#
# Transaction ownership remains outside this repository.
# Repository methods query, modify, and flush data.
# Commit / rollback is handled by the database session layer.
# ============================================================


from uuid import UUID

from sqlalchemy import (
    func,
    and_,
    delete,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import StartupStage
from src.repositories.models import Startup


class StartupRepository:
    """
    Repository responsible for Startup database operations.

    The repository receives an existing AsyncSession and
    uses it for all database operations.
    """

    def __init__(self, session: AsyncSession):
        # Store the request-scoped database session.
        self.session = session

    # ========================================================
    # CREATE STARTUP
    # ========================================================

    async def create(
        self,
        owner_id: UUID,
        name: str,
        description: str,
        stage: StartupStage,
    ) -> Startup:
        """
        Create a new startup and return the ORM object.

        Flow:
            Startup data
                ↓
            Startup model
                ↓
            session.add()
                ↓
            session.flush()
                ↓
            return Startup
        """

        startup = Startup(
            owner_id=owner_id,
            name=name,
            description=description,
            stage=stage,
        )

        # Stage the startup inside the current transaction.
        self.session.add(startup)

        # Send INSERT to PostgreSQL.
        # This also populates the database-generated UUID.
        await self.session.flush()

        return startup

    # ========================================================
    # GET STARTUP BY ID
    # ========================================================

    async def get_by_id(
        self,
        startup_id: UUID,
    ) -> Startup | None:
        """
        Retrieve a startup using its primary key.

        Returns:
            Startup if found, otherwise None.
        """

        query = select(Startup).where(
            Startup.startup_id == startup_id
        )

        result = await self.session.execute(query)

        # startup_id is the primary key.
        return result.scalar_one_or_none()

    # ========================================================
    # GET STARTUP BY ID AND OWNER
    # ========================================================

    async def get_by_id_and_owner(
        self,
        startup_id: UUID,
        owner_id: UUID,
    ) -> Startup | None:
        """
        Retrieve a startup only when it belongs to the owner.

        This method is important for authorization.

        Flow:
            startup_id + owner_id
                    ↓
              ownership check
                    ↓
              Startup / None
        """

        query = select(Startup).where(
            and_(
                Startup.owner_id == owner_id,
                Startup.startup_id == startup_id,
            )
        )   

        result = await self.session.execute(query)

        # Returns None when the startup doesn't belong
        # to the requested owner.
        return result.scalar_one_or_none()

    # ========================================================
    # LIST STARTUPS BY OWNER
    # ========================================================

    async def list_by_owner(
        self,
        owner_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[Startup], int]:
        """
        Retrieve one page of startups belonging to an owner.

        Returns:
            (
                startups_for_current_page,
                total_startup_count,
            )

        Flow:
            owner_id
                │
                ├──► COUNT(*) ──────► total
                │
                └──► SELECT
                       │
                       ├── ORDER BY
                       ├── OFFSET
                       └── LIMIT
                              │
                              ▼
                           startups
        """

        # ----------------------------------------------------
        # PAGINATION OFFSET
        # ----------------------------------------------------
        # Page 1 starts at offset 0.
        # Page 2 starts after the first page.
        offset = (page - 1) * page_size

        # ----------------------------------------------------
        # FETCH CURRENT PAGE
        # ----------------------------------------------------

        query = (
            select(Startup)
            .where(Startup.owner_id == owner_id)
            .order_by(Startup.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(query)

        startups = result.scalars().all()

        # ----------------------------------------------------
        # COUNT TOTAL STARTUPS
        # ----------------------------------------------------

        count_query = select(
            func.count(Startup.startup_id)
        ).where(
            Startup.owner_id == owner_id
        )

        count_result = await self.session.execute(count_query)

        total = count_result.scalar_one()

        return startups, total

    # ========================================================
    # UPDATE STARTUP
    # ========================================================

    async def update(
        self,
        startup_id: UUID,
        fields: dict,
    ) -> Startup:
        """
        Update the provided Startup fields.

        Only fields supplied in the dictionary are changed.

        Flow:
            startup_id
                ↓
            Find Startup
                ↓
            Apply fields
                ↓
            flush()
                ↓
            return Startup
        """

        startup = await self.get_by_id(startup_id)

        if startup is None:
            raise ValueError(
                f"Startup {startup_id} not found"
            )

        # Apply only the fields supplied by the caller.
        for field, value in fields.items():
            setattr(startup, field, value)

        # Persist changes within the current transaction.
        await self.session.flush()

        return startup

    # ========================================================
    # DELETE STARTUP
    # ========================================================

    async def delete(
        self,
        startup_id: UUID,
    ) -> None:
        """
        Delete a startup using its primary key.

        Related conversations and memories are handled
        through the configured database cascade rules.
        """

        query = delete(Startup).where(
            Startup.startup_id == startup_id
        )

        # Execute DELETE within the current transaction.
        await self.session.execute(query)

        # Flush the deletion without committing the transaction.
        await self.session.flush()
        
        # Commit is intentionally handled outside the repository.
        return