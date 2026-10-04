from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from src.core.enums import MemoryType
from src.repositories.base import Base, TimestampMixin


# ============================================================
# TYPE-CHECKING IMPORTS
# ============================================================
# Imported only during static type checking.
# Prevents circular imports between related models.

if TYPE_CHECKING:
    from src.repositories.models.startup import Startup


# ============================================================
# MEMORY MODEL
# ============================================================
# Represents an extracted fact about a startup.
#
# Memories persist across conversations and sessions.
#
# Relationships:
#   Startup ──< Memory


class Memory(Base, TimestampMixin):

    # --------------------------------------------------------
    # TABLE CONFIGURATION
    # --------------------------------------------------------

    __tablename__ = "memories"

    # --------------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------------
    # PostgreSQL generates the UUID automatically.

    memory_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )

    # --------------------------------------------------------
    # STARTUP FOREIGN KEY
    # --------------------------------------------------------
    # Every memory belongs to exactly one startup.
    # Deleting the startup cascades to its memories.

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
    # MEMORY TYPE
    # --------------------------------------------------------
    # Defines the category of the stored memory.
    # MemoryType is represented as a database enum.

    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType),
        nullable=False,
    )

    # --------------------------------------------------------
    # MEMORY CONTENT
    # --------------------------------------------------------
    # Stores the extracted fact or information.

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # --------------------------------------------------------
    # MEMORY IMPORTANCE
    # --------------------------------------------------------
    # Represents the relative importance of this memory.
    # Defaults to 0.5 when no explicit value is provided.

    importance: Mapped[float] = mapped_column(
        Float,
        default=0.5,
        server_default="0.5",
        nullable=False,
    )

    # --------------------------------------------------------
    # STARTUP RELATIONSHIP
    # --------------------------------------------------------
    # Each memory belongs to one startup.
    #
    # Memory.startup <──> Startup.memories

    startup: Mapped["Startup"] = relationship(
        "Startup",
        back_populates="memories",
    )