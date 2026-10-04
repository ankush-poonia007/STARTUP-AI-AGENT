# ============================================================
# USER REPOSITORY
# ============================================================
#
# Responsibility:
#   Handles database operations for the User model.
#
# Flow:
#
#   Service / API
#        │
#        ▼
#   UserRepository
#        │
#        ▼
#   AsyncSession
#        │
#        ▼
#   PostgreSQL
#
# Transaction ownership remains outside this repository.
# The repository performs queries and flushes, but does not commit.
# ============================================================

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.models.user import User


class UserRepository:
    """
    Repository responsible for User database operations.

    The repository receives an existing AsyncSession and uses it
    for all database operations.
    """

    def __init__(self, session: AsyncSession):
        # Store the request-scoped database session.
        self.session = session


    # ========================================================
    # CREATE USER
    # ========================================================
    async def create(
        self,
        email: str,
        password_hash: str,
    ) -> User:
        """
        Create a new User and return the persisted ORM object.

        Flow:
            User data
                ↓
            User model
                ↓
            session.add()
                ↓
            session.flush()
                ↓
            return User
        """

        user = User(
            email=email,
            password_hash=password_hash,
        )

        # Stage the new object in the current transaction.
        self.session.add(user)

        # Send INSERT to the database.
        # PostgreSQL generates the UUID and timestamps.
        await self.session.flush()

        return user


    # ========================================================
    # GET USER BY ID
    # ========================================================
    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        """
        Retrieve a User by primary key.

        Returns:
            User if found, otherwise None.
        """

        query = select(User).where(
            User.user_id == user_id,
        )

        result = await self.session.execute(query)

        # user_id is the primary key, so at most one row exists.
        return result.scalar_one_or_none()


    # ========================================================
    # GET USER BY EMAIL
    # ========================================================
    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        """
        Retrieve a User by unique email address.

        Returns:
            User if found, otherwise None.
        """

        query = select(User).where(
            User.email == email,
        )

        result = await self.session.execute(query)

        # email has a UNIQUE database constraint.
        return result.scalar_one_or_none()


    # ========================================================
    # DELETE USER
    # ========================================================
    async def delete(
        self,
        user_id: UUID,
    ) -> None:
        """
        Delete a User by primary key.

        Related startups are handled by the database's
        ON DELETE CASCADE constraint.
        """

        query = delete(User).where(
            User.user_id == user_id,
        )

        # Execute DELETE inside the current transaction.
        await self.session.execute(query)

        # Flush the deletion without committing the transaction.
        await self.session.flush()
        
        # Commit is intentionally handled outside the repository.
        return