
"""
CoFoundr AI — Security primitives unit tests.

Current scope:
    Step 2a: Argon2id password hashing and verification.
    Step 2b: JWT access-token creation and validation.

Test boundaries:
    - No database or FastAPI application.
    - No external services.
    - Use a dedicated test secret.
    - Verify both successful behavior and security failures.

Future scope:
    Step 2c will add refresh-token generation and hashing tests.
"""

import base64
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import pytest

from src.core.constants import REFRESH_TOKEN_BYTE_LENGTH
from src.core.security import generate_refresh_token, hash_refresh_token

from src.core.exceptions import InvalidToken, TokenExpired
from src.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# =============================================================================
# SHARED TEST CONFIGURATION
# =============================================================================

# Use a sufficiently long secret for HS256 tests.
TEST_SECRET = "test-secret-key-at-least-32-characters-long"
TEST_ALGORITHM = "HS256"

TEST_USER_ID = UUID("123e4567-e89b-12d3-a456-426614174000")

TEST_PASSWORD = "CorrectHorseBatteryStaple!"
WRONG_PASSWORD = "DefinitelyWrongPassword!"


# =============================================================================
# STEP 2a — PASSWORD HASHING
# =============================================================================


def test_hash_password_returns_argon2id_hash() -> None:
    """Password hashing should produce an encoded Argon2id hash."""
    password_hash = hash_password(TEST_PASSWORD)

    assert isinstance(password_hash, str)
    assert password_hash.startswith("$argon2id$")


def test_correct_password_verifies_successfully() -> None:
    """The original password should match its stored hash."""
    password_hash = hash_password(TEST_PASSWORD)

    assert verify_password(TEST_PASSWORD, password_hash) is True


def test_wrong_password_returns_false() -> None:
    """An incorrect password must not verify."""
    password_hash = hash_password(TEST_PASSWORD)

    assert verify_password(WRONG_PASSWORD, password_hash) is False


def test_same_password_produces_different_hashes() -> None:
    """Random salts should produce different hashes for identical passwords."""
    first_hash = hash_password(TEST_PASSWORD)
    second_hash = hash_password(TEST_PASSWORD)

    assert first_hash != second_hash

    # Both hashes should still verify against the original password.
    assert verify_password(TEST_PASSWORD, first_hash) is True
    assert verify_password(TEST_PASSWORD, second_hash) is True


def test_malformed_stored_hash_returns_false() -> None:
    """Malformed hashes should return False instead of raising an exception."""
    assert verify_password(TEST_PASSWORD, "not-a-valid-argon2-hash") is False


# =============================================================================
# STEP 2b — ACCESS TOKEN CREATION
# =============================================================================


def test_access_token_round_trip() -> None:
    """A created access token should decode into its expected claims."""
    token = create_access_token(
        user_id=TEST_USER_ID,
        secret=TEST_SECRET,
        algorithm=TEST_ALGORITHM,
        lifetime=900,
    )

    claims = decode_access_token(
        token=token,
        secret=TEST_SECRET,
        algorithm=TEST_ALGORITHM,
    )

    assert claims["sub"] == str(TEST_USER_ID)
    assert isinstance(claims["sub"], str)
    assert claims["token_type"] == "access"
    assert "iat" in claims
    assert "exp" in claims
    assert claims["exp"] > claims["iat"]


def test_negative_lifetime_produces_expired_token() -> None:
    """A negative lifetime should create a token rejected as expired."""
    token = create_access_token(
        user_id=TEST_USER_ID,
        secret=TEST_SECRET,
        algorithm=TEST_ALGORITHM,
        lifetime=-10,
    )

    with pytest.raises(TokenExpired):
        decode_access_token(token, TEST_SECRET, TEST_ALGORITHM)


def _tamper_payload(token: str) -> str:
    """
    Change a JWT payload without updating its signature.

    This simulates payload tampering while retaining valid JSON and
    the original signature segment.
    """
    header_segment, payload_segment, signature_segment = token.split(".")

    # Decode the URL-safe Base64 payload.
    padding = "=" * (-len(payload_segment) % 4)
    payload_bytes = base64.urlsafe_b64decode(payload_segment + padding)
    payload = json.loads(payload_bytes)

    # Modify a signed claim without recomputing the signature.
    payload["sub"] = "tampered-user-id"

    # Encode the modified payload in URL-safe Base64 without padding.
    modified_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).rstrip(b"=").decode("ascii")

    return f"{header_segment}.{modified_payload}.{signature_segment}"


def test_tampered_payload_is_rejected() -> None:
    """Changing a signed claim must invalidate the token."""
    token = create_access_token(
        TEST_USER_ID,
        TEST_SECRET,
        TEST_ALGORITHM,
        900,
    )
    tampered_token = _tamper_payload(token)

    with pytest.raises(InvalidToken):
        decode_access_token(tampered_token, TEST_SECRET, TEST_ALGORITHM)


def test_wrong_secret_is_rejected() -> None:
    """A token signed with another secret must fail verification."""
    token = create_access_token(
        TEST_USER_ID,
        TEST_SECRET,
        TEST_ALGORITHM,
        900,
    )

    wrong_secret = "different-secret-key-at-least-32-characters"

    with pytest.raises(InvalidToken):
        decode_access_token(token, wrong_secret, TEST_ALGORITHM)


def test_none_algorithm_is_rejected() -> None:
    """An unsigned JWT must not be accepted as an access token."""
    now = datetime.now(timezone.utc)

    claims = {
        "sub": str(TEST_USER_ID),
        "token_type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }

    # Construct an unsigned JWT to test algorithm allowlisting.
    unsigned_token = jwt.encode(claims, key="", algorithm="none")

    with pytest.raises(InvalidToken):
        decode_access_token(unsigned_token, TEST_SECRET, TEST_ALGORITHM)


@pytest.mark.parametrize("missing_claim", ["sub", "token_type", "iat", "exp"])
def test_missing_required_claim_is_rejected(missing_claim: str) -> None:
    """Every required claim must be present in an access token."""
    now = datetime.now(timezone.utc)

    claims = {
        "sub": str(TEST_USER_ID),
        "token_type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }

    claims.pop(missing_claim)

    malformed_token = jwt.encode(
        claims,
        TEST_SECRET,
        algorithm=TEST_ALGORITHM,
    )

    with pytest.raises(InvalidToken):
        decode_access_token(
            malformed_token,
            TEST_SECRET,
            TEST_ALGORITHM,
        )


def test_refresh_type_token_is_rejected_as_access_token() -> None:
    """A validly signed refresh-type token must fail access-token validation."""
    now = datetime.now(timezone.utc)

    claims = {
        "sub": str(TEST_USER_ID),
        "token_type": "refresh",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }

    refresh_type_token = jwt.encode(
        claims,
        TEST_SECRET,
        algorithm=TEST_ALGORITHM,
    )

    with pytest.raises(InvalidToken):
        decode_access_token(
            refresh_type_token,
            TEST_SECRET,
            TEST_ALGORITHM,
        )



# =============================================================================
# STEP 2c — REFRESH TOKEN TESTS
# =============================================================================


def test_generate_refresh_tokens_are_unique() -> None:
    """One thousand generated refresh tokens should all be unique."""
    tokens = [generate_refresh_token() for _ in range(1000)]

    assert len(set(tokens)) == 1000
    assert all(isinstance(token, str) for token in tokens)
    assert all(token for token in tokens)

    # Identical generation settings should produce consistent text lengths.
    assert len({len(token) for token in tokens}) == 1


def test_refresh_token_length_matches_configured_random_bytes() -> None:
    """The encoded token length should match the configured byte count."""
    token = generate_refresh_token()

    # URL-safe Base64 encoding produces text longer than the input byte count.
    expected_length = len(
        __import__("base64").urlsafe_b64encode(
            b"\x00" * REFRESH_TOKEN_BYTE_LENGTH
        ).rstrip(b"=")
    )

    assert len(token) == expected_length


def test_refresh_token_hash_is_deterministic() -> None:
    """Identical raw tokens must produce identical SHA-256 digests."""
    raw_token = generate_refresh_token()

    first_hash = hash_refresh_token(raw_token)
    second_hash = hash_refresh_token(raw_token)

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_different_refresh_tokens_have_different_hashes() -> None:
    """Different generated tokens should produce different digests."""
    first_token = generate_refresh_token()
    second_token = generate_refresh_token()

    assert first_token != second_token
    assert hash_refresh_token(first_token) != hash_refresh_token(second_token)
