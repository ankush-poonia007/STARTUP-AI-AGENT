
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.infrastructure.database.session import get_db


class FakeSession:
    def __init__(self):
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.close = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        await self.close()
        return False


class FakeSessionFactory:
    def __init__(self):
        self.sessions = []

    def __call__(self):
        session = FakeSession()
        self.sessions.append(session)
        return session


def make_request(factory):
    return SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                database_session_maker=factory,
            )
        )
    )


@pytest.mark.asyncio
async def test_get_db_yields_session_and_commits_on_success():
    factory = FakeSessionFactory()
    dependency = get_db(make_request(factory))

    session = await anext(dependency)
    assert session is factory.sessions[0]

    with pytest.raises(StopAsyncIteration):
        await anext(dependency)

    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_db_rolls_back_on_exception():
    factory = FakeSessionFactory()
    dependency = get_db(make_request(factory))

    session = await anext(dependency)

    with pytest.raises(RuntimeError, match="simulated failure"):
        await dependency.athrow(RuntimeError("simulated failure"))

    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_db_creates_a_new_session_per_dependency_use():
    factory = FakeSessionFactory()

    first_dependency = get_db(make_request(factory))
    first_session = await anext(first_dependency)
    with pytest.raises(StopAsyncIteration):
        await anext(first_dependency)

    second_dependency = get_db(make_request(factory))
    second_session = await anext(second_dependency)
    with pytest.raises(StopAsyncIteration):
        await anext(second_dependency)

    assert first_session is not second_session
    assert len(factory.sessions) == 2


@pytest.mark.asyncio
async def test_get_db_closes_session_after_commit_failure():
    factory = FakeSessionFactory()
    dependency = get_db(make_request(factory))

    session = await anext(dependency)
    session.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        await anext(dependency)

    session.close.assert_awaited_once()
