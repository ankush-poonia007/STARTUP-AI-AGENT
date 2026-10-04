# ============================================================
# CONVERSATION REPOSITORY
# ============================================================

# Responsibility:
#   Handles database operations for the Conversation model.

# Flow:
#
#   API / Service
#        │
#        ▼
#   ConversationRepository
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
    delete,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.models.conversation import Conversation


class ConversationRepository:
    """
    Repository responsible for Conversation database operations.

    The repository receives an existing AsyncSession and
    uses it for all database operations.
    """

    def __init__(self, session: AsyncSession):
        # Store the request-scoped database session.
        self.session = session

    # ========================================================
    # CREATE CONVERSATION
    # ========================================================

    async def create(
        self,
        startup_id: UUID,
        title: str,
    ) -> Conversation:
        """
        Create a new conversation and return the ORM object.

        Flow:

            Conversation data
                    ↓
            Conversation model
                    ↓
              session.add()
                    ↓
              session.flush()
                    ↓
            return Conversation
        """

        # Create the Conversation ORM object.
        conversation = Conversation(
            startup_id=startup_id,
            title=title,
        )

        # Stage the conversation inside the current transaction.
        self.session.add(conversation)

        # Send INSERT to PostgreSQL.
        # This also populates the database-generated UUID.
        await self.session.flush()

        return conversation

    # ========================================================
    # GET CONVERSATION BY ID
    # ========================================================

    async def get_by_id(
        self,
        conversation_id: UUID,
    ) -> Conversation | None:
        """
        Retrieve a conversation using its primary key.

        Returns:
            Conversation if found, otherwise None.
        """

        # Build a query using the conversation primary key.
        query = select(Conversation).where(
            Conversation.conversation_id == conversation_id
        )

        # Execute the SELECT query asynchronously.
        result = await self.session.execute(query)

        # Return the conversation or None when not found.
        return result.scalar_one_or_none()

    # ========================================================
    # LIST CONVERSATIONS BY STARTUP
    # ========================================================

    async def list_by_startup(
        self,
        startup_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[Conversation], int]:
        """
        Retrieve one page of conversations belonging to a startup.

        Returns:
            (
                conversations_for_current_page,
                total_conversation_count,
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
                        conversations
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

        # Retrieve conversations belonging to this startup.
        query = (
            select(Conversation)
            .where(
                Conversation.startup_id == startup_id
            )
            .order_by(
                Conversation.created_at.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        # Execute the paginated query.
        result = await self.session.execute(query)

        # Extract Conversation ORM objects.
        conversations = result.scalars().all()

        # ----------------------------------------------------
        # COUNT TOTAL CONVERSATIONS
        # ----------------------------------------------------

        # Count every conversation belonging to this startup.
        count_query = select(
            func.count(Conversation.conversation_id)
        ).where(
            Conversation.startup_id == startup_id
        )

        # Execute the count query.
        count_result = await self.session.execute(
            count_query
        )

        # Extract the total conversation count.
        total = count_result.scalar_one()

        return conversations, total

    # ========================================================
    # UPDATE CONVERSATION
    # ========================================================

    async def update(
        self,
        conversation_id: UUID,
        title: str,
    ) -> Conversation:
        """
        Update the title of an existing conversation.

        Flow:

            conversation_id
                    ↓
            Find Conversation
                    ↓
            Conversation exists?
                 ↙       ↘
              No          Yes
              ↓            ↓
            Error      Update title
                           ↓
                         flush()
                           ↓
                    return Conversation
        """

        # Retrieve the conversation before updating it.
        conversation = await self.get_by_id(
            conversation_id
        )

        # Raise an error when the conversation doesn't exist.
        if conversation is None:
            raise ValueError(
                f"Conversation {conversation_id} not found"
            )

        # Update the conversation title.
        conversation.title = title

        # Persist the update within the current transaction.
        await self.session.flush()

        return conversation

    # ========================================================
    # DELETE CONVERSATION
    # ========================================================

    async def delete(
        self,
        conversation_id: UUID,
    ) -> None:
        """
        Delete a conversation using its primary key.

        Related messages are handled through the
        configured database cascade rules.
        """

        # Build a DELETE query using the conversation primary key.
        query = delete(Conversation).where(
            Conversation.conversation_id == conversation_id
        )

        # Execute DELETE within the current transaction.
        await self.session.execute(query)

        # Flush the deletion without committing the transaction.
        await self.session.flush()
        
        # Commit is intentionally handled outside the repository.
        return  