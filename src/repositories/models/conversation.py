from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import text

from src.repositories.base import Base, TimestampMixin


# ============================================================
# TYPE-CHECKING IMPORTS
# ============================================================

if TYPE_CHECKING:
    from src.repositories.models.message import Message
    from src.repositories.models.startup import Startup


# ============================================================
# CONVERSATION MODEL
# ============================================================
# Represents a conversation thread belonging to a startup.
#
# Relationships:
#   Startup       ──< Conversation
#   Conversation  ──< Message


class Conversation(Base, TimestampMixin):

    # --------------------------------------------------------
    # TABLE CONFIGURATION
    # --------------------------------------------------------

    __tablename__ = "conversations"

    # --------------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------------

    conversation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )

    # --------------------------------------------------------
    # STARTUP FOREIGN KEY
    # --------------------------------------------------------

    startup_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "startups.startup_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------
    # CONVERSATION INFORMATION
    # --------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # --------------------------------------------------------
    # STARTUP RELATIONSHIP
    # --------------------------------------------------------
    # Each conversation belongs to one startup.
    #
    # Conversation.startup <──> Startup.conversations

    startup: Mapped["Startup"] = relationship(
        "Startup",
        back_populates="conversations",
    )

    # --------------------------------------------------------
    # MESSAGE RELATIONSHIP
    # --------------------------------------------------------
    # Each conversation can contain multiple messages.
    #
    # Conversation.messages <──> Message.conversation

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )