
from typing import Any

from fastapi import Request


DATABASE_SESSION_MAKER_STATE_KEY = "database_session_maker"
CHROMA_DOCUMENTS_STATE_KEY = "chroma_documents"
CHROMA_MEMORIES_STATE_KEY = "chroma_memories"
FILE_STORAGE_STATE_KEY = "file_storage"
EMBEDDER_STATE_KEY = "embedder"


def get_required_state(request: Request, key: str) -> Any:
    """Return a required application-state object."""
    value = getattr(request.app.state, key, None)

    if value is None:
        raise RuntimeError(
            f"Required app.state.{key} is missing. "
            "Application startup wiring did not run."
        )

    return value
