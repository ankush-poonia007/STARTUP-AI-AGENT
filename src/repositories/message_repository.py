# ============================================================
# MESSAGE REPOSITORY
# ============================================================

# Responsibility:
#   Handles database operations for the Message model.
#
# Flow:
#
#   API / Service
#        │
#        ▼
#   MessageRepository
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
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import MessageRole
from src.repositories.models.conversation import Conversation
from src.repositories.models.message import Message


class MessageRepository:
    """
    Repository responsible for Message database operations.

    The repository receives an existing AsyncSession and
    uses it for all database operations.
    """

    def __init__(self, session: AsyncSession):
        # Store the request-scoped database session.
        self.session = session

    # ========================================================
    # APPEND MESSAGE
    # ========================================================

    async def append(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
    ) -> Message:
        """
        Append a new message to a conversation.

        The conversation row is locked before calculating
        the next sequence number.

        Flow:

            conversation_id
                    ↓
            Lock Conversation
                    ↓
            Find MAX(sequence_number)
                    ↓
            Calculate next_seq
                    ↓
            Create Message
                    ↓
                session.add()
                    ↓
                session.flush()
                    ↓
            return Message
        """

        # ----------------------------------------------------
        # LOCK CONVERSATION ROW
        # ----------------------------------------------------

        # Lock the conversation to prevent concurrent
        # requests from calculating the same sequence number.
        conversation_query = (
            select(Conversation)
            .where(
                Conversation.conversation_id == conversation_id
            )
            .with_for_update()
        )

        # Execute the locking query.
        conversation_result = await self.session.execute(
            conversation_query
        )

        # Retrieve the locked conversation.
        conversation = conversation_result.scalar_one_or_none()

        # Ensure the conversation exists.
        if conversation is None:
            raise ValueError(
                f"Conversation {conversation_id} not found"
            )

        # ----------------------------------------------------
        # FIND CURRENT MAXIMUM SEQUENCE
        # ----------------------------------------------------

        # Find the highest sequence number for this conversation.
        max_query = select(
            func.max(Message.sequence_number)
        ).where(
            Message.conversation_id == conversation_id
        )

        # Execute the MAX query.
        max_result = await self.session.execute(max_query)

        # MAX returns None when no messages exist.
        max_sequence = max_result.scalar_one()

        # ----------------------------------------------------
        # CALCULATE NEXT SEQUENCE
        # ----------------------------------------------------

        # First message starts at sequence number 1.
        # Otherwise, increment the current maximum.
        next_seq = (
            max_sequence + 1
            if max_sequence is not None
            else 1
        )

        # ----------------------------------------------------
        # CREATE MESSAGE
        # ----------------------------------------------------

        # Create the Message ORM object.
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sequence_number=next_seq,
        )

        # Stage the message inside the current transaction.
        self.session.add(message)

        # Send INSERT to PostgreSQL.
        await self.session.flush()

        return message

    # ========================================================
    # LIST MESSAGES BY CONVERSATION
    # ========================================================

    async def list_by_conversation(
        self,
        conversation_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[Message], int]:
        """
        Retrieve one page of messages from a conversation.

        Messages are ordered by sequence_number ascending.

        Returns:
            (
                messages_for_current_page,
                total_message_count,
            )

        Flow:

            conversation_id
                    │
                    ├──► COUNT(*) ──────► total
                    │
                    └──► SELECT
                           │
                           ├── ORDER BY sequence_number ASC
                           ├── OFFSET
                           └── LIMIT
                                  │
                                  ▼
                               messages
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

        # Retrieve messages belonging to this conversation.
        query = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id
            )
            .order_by(
                Message.sequence_number.asc()
            )
            .offset(offset)
            .limit(page_size)
        )

        # Execute the paginated query.
        result = await self.session.execute(query)

        # Extract Message ORM objects.
        messages = result.scalars().all()

        # ----------------------------------------------------
        # COUNT TOTAL MESSAGES
        # ----------------------------------------------------

        # Count every message belonging to this conversation.
        count_query = select(
            func.count(Message.message_id)
        ).where(
            Message.conversation_id == conversation_id
        )

        # Execute the count query.
        count_result = await self.session.execute(
            count_query
        )

        # Extract the total message count.
        total = count_result.scalar_one()

        return messages, total