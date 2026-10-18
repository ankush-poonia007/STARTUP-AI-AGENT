
"""
CoFoundr AI — Security Primitives.

Step 2a: Password hashing and verification using Argon2id.

Design principles:
    - Pure, synchronous security utilities.
    - No database, HTTP, or settings dependencies.
    - Use Argon2 library defaults without custom tuning.
    - Never log or expose plaintext passwords.
    - Return False for incorrect passwords and malformed stored hashes.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from src.core.constants import ACCESS_TOKEN_TYPE, REFRESH_TOKEN_BYTE_LENGTH
from src.core.exceptions import InvalidToken, TokenExpired

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2id.

    Argon2 generates a random salt and embeds it, along with the
    algorithm parameters, into the encoded hash string.

    Args:
        password: Plaintext password supplied by the caller.

    Returns:
        An encoded Argon2id hash suitable for persistent storage.

    Raises:
        TypeError: If password is not a string.
        ValueError: If password is empty.

    Security:
        Never log the password or include it in error messages.
        Password length validation belongs to the relevant input layer.
    """
    
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

    if not password:
        raise ValueError("Password must not be empty.")

    # Use library defaults; do not tune Argon2 parameters here.
    password_hasher = PasswordHasher()

    # The encoded result contains the salt and verification parameters.
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a plaintext password against a stored Argon2 hash.

    The Argon2 library extracts the salt and parameters from the
    stored hash and performs the verification securely.

    Args:
        password: Candidate plaintext password.
        stored_hash: Previously stored encoded Argon2 hash.

    Returns:
        True if the password matches; otherwise False.

    Security:
        Never compare password strings manually.
        Never log passwords or stored hashes.
        Malformed hashes and verification failures return False.
    """
    
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False

    if not password or not stored_hash:
        return False

    # A hasher object is local to this call; it performs no I/O.
    password_hasher = PasswordHasher()

    try:
        return password_hasher.verify(
            stored_hash,
            password
        )
        
    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError
    ):
        # Wrong passwords and invalid stored hashes are normal failures.
        return False


def create_access_token(
    user_id: UUID | str,
    secret: str,
    algorithm: str,
    lifetime: int | float,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        user_id: User identifier, converted to text before encoding.
        secret: Signing secret supplied by the caller.
        algorithm: JWT signing algorithm supplied by the caller.
        lifetime: Token lifetime in seconds; negative values are allowed
            for expired-token testing.

    Returns:
        The encoded JWT string.

    Claims:
        sub: User identifier as text.
        token_type: The access-token type.
        iat: Issued-at timestamp in UTC.
        exp: Expiration timestamp in UTC.
    """
    now = datetime.now(timezone.utc)

    claims = {
        "sub": str(user_id),
        "token_type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(seconds=lifetime),
    }

    return jwt.encode(claims, secret, algorithm=algorithm)


def decode_access_token(
    token: str,
    secret: str,
    algorithm: str,
) -> dict[str, Any]:
    """
    Decode and validate a signed JWT access token.

    Args:
        token: Encoded JWT string.
        secret: Verification secret supplied by the caller.
        algorithm: Expected signing algorithm.

    Returns:
        Validated token claims, with sub retained as text.

    Raises:
        TokenExpired: The token's expiration has passed.
        InvalidToken: Signature, claims, algorithm, or token type is invalid.
    """
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            options={
                "require": ["sub", "token_type", "iat", "exp"],
            },
        )
    except ExpiredSignatureError as exc:
        raise TokenExpired() from exc
    except InvalidTokenError as exc:
        raise InvalidToken() from exc
    except (TypeError, ValueError) as exc:
        raise InvalidToken() from exc

    if not isinstance(claims.get("sub"), str):
        raise InvalidToken()

    if claims.get("token_type") != ACCESS_TOKEN_TYPE:
        raise InvalidToken()

    return claims



# =============================================================================
# STEP 2c — REFRESH TOKEN UTILITIES
# =============================================================================


def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure refresh token.

    Returns:
        URL-safe encoded text generated from REFRESH_TOKEN_BYTE_LENGTH
        random bytes.

    Security:
        Uses Python's secrets module for cryptographically secure randomness.
        The raw token must not be logged.
    """
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTE_LENGTH)


def hash_refresh_token(raw_token: str) -> str:
    """
    Hash a raw refresh token using SHA-256.

    Args:
        raw_token: Raw refresh-token text.

    Returns:
        A deterministic 64-character hexadecimal SHA-256 digest.

    Note:
        Store the digest, not the raw refresh token, in the database.
    """
    if not isinstance(raw_token, str):
        raise TypeError("Refresh token must be a string.")

    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
