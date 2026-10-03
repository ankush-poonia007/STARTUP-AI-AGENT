from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from src.core.enums import MessageRole
from src.repositories.base import Base


# ============================================================
# TYPE-CHECKING IMPORTS
# ============================================================
# Imported only during static type checking.
# Prevents circular imports between related models.

if TYPE_CHECKING:
    from src.repositories.models.conversation import Conversation


# ============================================================
# MESSAGE MODEL
# ============================================================
# Represents an individual message inside a conversation.
#
# Messages are append-only.
# Existing messages should not be updated.
#
# Relationships:
#   Conversation ──< Message


class Message(Base):

    # --------------------------------------------------------
    # TABLE CONFIGURATION
    # --------------------------------------------------------

    __tablename__ = "messages"

    # --------------------------------------------------------
    # TABLE CONSTRAINTS
    # --------------------------------------------------------
    # Prevents duplicate sequence numbers within one conversation.
    #
    # The same sequence number may exist in different conversations.

    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "sequence_number",
            name="uq_conversation_sequence_number",
        ),
    )

    # --------------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------------
    # PostgreSQL generates the UUID automatically.

    message_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )

    # --------------------------------------------------------
    # CONVERSATION FOREIGN KEY
    # --------------------------------------------------------
    # Every message belongs to exactly one conversation.
    # Deleting the conversation cascades to its messages.

    conversation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "conversations.conversation_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------
    # MESSAGE ROLE
    # --------------------------------------------------------
    # Stores whether the message belongs to the user,
    # assistant, or another role defined by MessageRole.

    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole),
        nullable=False,
    )

    # --------------------------------------------------------
    # MESSAGE CONTENT
    # --------------------------------------------------------
    # TEXT is used because message content can exceed 255 characters.

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # --------------------------------------------------------
    # MESSAGE ORDER
    # --------------------------------------------------------
    # Determines the message's position within its conversation.
    #
    # Combined with conversation_id, this must be unique.

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # --------------------------------------------------------
    # CREATION TIMESTAMP
    # --------------------------------------------------------
    # Messages are append-only.
    # Therefore, they intentionally do not have updated_at.

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # --------------------------------------------------------
    # CONVERSATION RELATIONSHIP
    # --------------------------------------------------------
    # Each message belongs to one conversation.
    #
    # Message.conversation <──> Conversation.messages

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )