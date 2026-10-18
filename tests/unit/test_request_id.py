
"""
CoFoundr AI — Request ID Middleware Unit Tests.

Tests:
    - Valid request IDs are preserved.
    - Missing and empty IDs are replaced with UUIDs.
    - IDs longer than 64 characters are rejected.
    - Unsafe characters are rejected.
    - All permitted characters are accepted.
"""

import uuid

import pytest

from src.middleware.request_id import _get_valid_request_id


# =============================================================================
# VALID REQUEST IDs
# =============================================================================


@pytest.mark.parametrize(
    "request_id",
    [
        "request-123",
        "abc_DEF",
        "trace.id.01",
        "A1-b2_C3.d4",
    ],
)
def test_valid_request_id_is_preserved(request_id: str) -> None:
    """A valid client-provided request ID should remain unchanged."""
    assert _get_valid_request_id(request_id) == request_id


# =============================================================================
# MISSING OR EMPTY REQUEST IDs
# =============================================================================


@pytest.mark.parametrize("request_id", [None, ""])
def test_missing_or_empty_request_id_generates_uuid(
    request_id: str | None,
) -> None:
    """Missing or empty IDs should be replaced with valid UUID strings."""
    generated_id = _get_valid_request_id(request_id)

    assert isinstance(generated_id, str)
    assert str(uuid.UUID(generated_id)) == generated_id


# =============================================================================
# LENGTH VALIDATION
# =============================================================================


def test_request_id_of_64_characters_is_accepted() -> None:
    """The maximum permitted request ID length is 64 characters."""
    request_id = "a" * 64

    assert _get_valid_request_id(request_id) == request_id


def test_request_id_longer_than_64_characters_is_replaced() -> None:
    """IDs exceeding the length limit should be replaced with UUIDs."""
    request_id = "a" * 65

    generated_id = _get_valid_request_id(request_id)

    assert generated_id != request_id
    assert str(uuid.UUID(generated_id)) == generated_id


# =============================================================================
# CHARACTER VALIDATION
# =============================================================================


@pytest.mark.parametrize(
    "request_id",
    [
        "request id",       # Space
        "request/id",       # Slash
        "request@id",       # At sign
        "request\nid",      # Newline
        "request\tid",      # Tab
        "réquest-id",       # Non-ASCII character
    ],
)
def test_unsafe_request_id_is_replaced(request_id: str) -> None:
    """IDs containing disallowed characters should be replaced."""
    generated_id = _get_valid_request_id(request_id)

    assert generated_id != request_id
    assert str(uuid.UUID(generated_id)) == generated_id
