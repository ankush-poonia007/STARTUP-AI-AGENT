from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from src.repositories.base import Base, TimestampMixin


# ============================================================
# TYPE-CHECKING IMPORTS
# ============================================================
# Imported only during static type checking.
# Prevents circular imports between User and Startup.

if TYPE_CHECKING:
    from src.repositories.models.startup import Startup


# ============================================================
# USER MODEL
# ============================================================
# Root entity for application users.
#
# Relationships:
#   User ──< Startup
#
# A user can own multiple startups.


class User(Base, TimestampMixin):

    # --------------------------------------------------------
    # TABLE CONFIGURATION
    # --------------------------------------------------------

    __tablename__ = "users"

    # --------------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------------
    # PostgreSQL generates the UUID automatically.

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )

    # --------------------------------------------------------
    # USER CREDENTIALS
    # --------------------------------------------------------

    # User's unique login email.
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    # Password is stored as a hash, never plaintext.
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # --------------------------------------------------------
    # STARTUP RELATIONSHIP
    # --------------------------------------------------------
    # One user can own multiple startups.
    #
    # User.startups  <──>  Startup.owner

    startups: Mapped[list["Startup"]] = relationship(
        "Startup",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )