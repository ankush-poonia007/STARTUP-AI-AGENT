
from typing import Any

from fastapi import Request

from src.infrastructure.state_keys import EMBEDDER_STATE_KEY


def get_embedder(request: Request) -> Any:
    """Return the application-scoped embedder instance."""
    value = getattr(request.app.state, EMBEDDER_STATE_KEY, None)

    if value is None:
        raise RuntimeError(
            f"Required app.state.{EMBEDDER_STATE_KEY} is missing. "
            "Application startup wiring did not run."
        )

    return value
