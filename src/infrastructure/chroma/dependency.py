
from typing import Any

from fastapi import Request

from src.infrastructure.state_keys import (
    CHROMA_DOCUMENTS_STATE_KEY,
    CHROMA_MEMORIES_STATE_KEY,
)


def _get_required_state(request: Request, key: str) -> Any:
    value = getattr(request.app.state, key, None)

    if value is None:
        raise RuntimeError(
            f"Required app.state.{key} is missing. "
            "Application startup wiring did not run."
        )

    return value


def get_chroma_documents(request: Request) -> Any:
    """Return the application-scoped Chroma documents collection."""
    return _get_required_state(request, CHROMA_DOCUMENTS_STATE_KEY)


def get_chroma_memories(request: Request) -> Any:
    """Return the application-scoped Chroma memories collection."""
    return _get_required_state(request, CHROMA_MEMORIES_STATE_KEY)
