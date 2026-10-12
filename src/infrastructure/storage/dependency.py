
from typing import Any

from fastapi import Request

from src.infrastructure.state_keys import FILE_STORAGE_STATE_KEY


def get_file_storage(request: Request) -> Any:
    """Return the application-scoped FileStorage instance."""
    value = getattr(request.app.state, FILE_STORAGE_STATE_KEY, None)

    if value is None:
        raise RuntimeError(
            f"Required app.state.{FILE_STORAGE_STATE_KEY} is missing. "
            "Application startup wiring did not run."
        )

    return value
