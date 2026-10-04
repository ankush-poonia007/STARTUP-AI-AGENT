from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from src.core.enums import StartupStage
from src.repositories.base import Base, TimestampMixin


# ============================================================
# TYPE-CHECKING IMPORTS
# ============================================================
# Imported only for static type checking.
# Avoids runtime circular imports between related models.

if TYPE_CHECKING:
    from src.repositories.models.conversation import Conversation
    from src.repositories.models.memory import Memory
    from src.repositories.models.user import User


# ============================================================
# STARTUP MODEL
# ============================================================
# Represents a startup idea owned by a user.
#
# Relationships:
#   User     ──< Startup
#   Startup  ──< Conversation
#   Startup  ──< Memory
#
# Soft deletion is not currently used by this model.


class Startup(Base, TimestampMixin):

    # --------------------------------------------------------
    # TABLE CONFIGURATION
    # --------------------------------------------------------

    __tablename__ = "startups"

    # --------------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------------
    # PostgreSQL generates the UUID automatically.
    # UUID(as_uuid=True) exposes it as Python's UUID object.

    startup_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )

    # --------------------------------------------------------
    # OWNER FOREIGN KEY
    # --------------------------------------------------------
    # Each startup belongs to exactly one user.
    # Deleting the user cascades deletion to their startups.

    owner_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.user_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------
    # STARTUP INFORMATION
    # --------------------------------------------------------

    # Startup's display name.
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Optional longer description of the startup idea.
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Current lifecycle stage of the startup.
    # Defaults to IDEA when a startup is created.

    stage: Mapped[StartupStage] = mapped_column(
        Enum(StartupStage),
        nullable=False,
        default=StartupStage.IDEA,
    )

    # --------------------------------------------------------
    # USER RELATIONSHIP
    # --------------------------------------------------------
    # Many startups can belong to one user.
    #
    # User.startups  <──>  Startup.owner

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="startups",
    )

    # --------------------------------------------------------
    # CONVERSATION RELATIONSHIP
    # --------------------------------------------------------
    # One startup can contain multiple conversations.
    #
    # Startup.conversations  <──>  Conversation.startups
    #
    # Deleting the startup removes its conversations.

    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="startup",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # --------------------------------------------------------
    # MEMORY RELATIONSHIP
    # --------------------------------------------------------
    # One startup can contain multiple memories.
    #
    # Startup.memories  <──>  Memory.startups
    #
    # Deleting the startup removes its memories.

    memories: Mapped[list["Memory"]] = relationship(
        "Memory",
        back_populates="startup",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )