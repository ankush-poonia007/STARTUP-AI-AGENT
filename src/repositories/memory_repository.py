# ============================================================
# MEMORY REPOSITORY
# ============================================================

# Responsibility:
#   Handles database operations for the Memory model.
#
# Flow:
#
#   API / Service
#        │
#        ▼
#   MemoryRepository
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
    select,
    delete,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import MemoryType
from src.repositories.models.memory import Memory


class MemoryRepository:
    """
    Repository responsible for Memory database operations.

    The repository receives an existing AsyncSession and
    uses it for all database operations.
    """

    def __init__(self, session: AsyncSession):
        # Store the request-scoped database session.
        self.session = session

    # ========================================================
    # CREATE MEMORY
    # ========================================================

    async def create(
        self,
        startup_id: UUID,
        memory_type: MemoryType,
        content: str,
        importance: float,
    ) -> Memory:
        """
        Create a new memory and return the ORM object.

        Flow:

            Memory data
                 ↓
            Memory model
                 ↓
            session.add()
                 ↓
            session.flush()
                 ↓
            return Memory
        """

        # Create the Memory ORM object.
        memory = Memory(
            startup_id=startup_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
        )

        # Stage the memory inside the current transaction.
        self.session.add(memory)

        # Send INSERT to PostgreSQL.
        # This also populates the database-generated UUID.
        await self.session.flush()

        return memory

    # ========================================================
    # GET MEMORY BY ID
    # ========================================================

    async def get_by_id(
        self,
        memory_id: UUID,
    ) -> Memory | None:
        """
        Retrieve a memory using its primary key.

        Returns:
            Memory if found, otherwise None.
        """

        # Build a query using the memory primary key.
        query = select(Memory).where(
            Memory.memory_id == memory_id
        )

        # Execute the SELECT query asynchronously.
        result = await self.session.execute(query)

        # Return the memory or None when not found.
        return result.scalar_one_or_none()

    # ========================================================
    # LIST MEMORIES BY STARTUP
    # ========================================================

    async def list_by_startup(
        self,
        startup_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[Memory], int]:
        """
        Retrieve one page of memories belonging to a startup.

        Returns:
            (
                memories_for_current_page,
                total_memory_count,
            )

        Flow:

            startup_id
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
                           memories
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

        # Retrieve memories belonging to this startup.
        query = (
            select(Memory)
            .where(
                Memory.startup_id == startup_id
            )
            .order_by(
                Memory.created_at.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        # Execute the paginated query.
        result = await self.session.execute(query)

        # Extract Memory ORM objects.
        memories = result.scalars().all()

        # ----------------------------------------------------
        # COUNT TOTAL MEMORIES
        # ----------------------------------------------------

        # Count every memory belonging to this startup.
        count_query = select(
            func.count(Memory.memory_id)
        ).where(
            Memory.startup_id == startup_id
        )

        # Execute the count query.
        count_result = await self.session.execute(
            count_query
        )

        # Extract the total memory count.
        total = count_result.scalar_one()

        return memories, total

    # ========================================================
    # DELETE MEMORY
    # ========================================================

    async def delete(
        self,
        memory_id: UUID,
    ) -> None:
        """
        Delete a memory using its primary key.

        Flow:

            memory_id
                ↓
            DELETE query
                ↓
             Execute
                ↓
              flush()
                ↓
              return
        """

        # Build a DELETE query using the memory primary key.
        query = delete(Memory).where(
            Memory.memory_id == memory_id
        )

        # Execute DELETE within the current transaction.
        await self.session.execute(query)

        # Flush the deletion without committing the transaction.
        await self.session.flush()

        # Commit is intentionally handled outside the repository.
        return