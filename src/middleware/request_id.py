
"""
CoFoundr AI — Request ID Middleware.

Responsibilities:
    - Accept safe client-provided request IDs.
    - Generate UUIDs for missing or invalid IDs.
    - Store the ID on request.state.request_id.
    - Return the ID through the X-Request-ID response header.

Security:
    - Accept only ASCII letters, digits, hyphens, underscores, and dots.
    - Limit request IDs to 64 characters.
    - Never trust arbitrary client-provided values for logging.
"""

import re
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.constants import REQUEST_ID_HEADER


# Only allow ASCII letters, digits, hyphens, underscores, and dots.
_SAFE_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _get_valid_request_id(candidate: str | None) -> str:
    """
    Validate a supplied request ID or generate a replacement.

    Args:
        candidate: Request ID received from the client, if any.

    Returns:
        The validated ID or a newly generated UUID string.
    """
    if candidate is not None and _SAFE_REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate

    return str(uuid.uuid4())


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a validated request ID to every request and response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process a request with a validated request ID.

        The ID is available to downstream handlers through
        request.state.request_id.
        """
        candidate = request.headers.get(REQUEST_ID_HEADER)
        request_id = _get_valid_request_id(candidate)

        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id

        return response
