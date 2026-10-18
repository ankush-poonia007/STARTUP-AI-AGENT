"""
Application exception hierarchy.

Phase 5:
    Preserves existing pipeline, agent, tool, and workflow exceptions.

SP-03:
    Introduces HTTP-aware application exceptions for FastAPI.
    Each HTTP exception defines:
        - status_code: HTTP response status
        - code: Stable machine-readable error code
        - default_message: Safe, user-facing default message
        - headers: Optional HTTP response headers

Architecture rules:
    - Existing Phase 5 exception classes remain unchanged.
    - Existing storage exception names remain unchanged.
    - Storage exceptions inherit from AppException.
    - Custom messages override defaults without changing error codes.
"""

# =============================================================================
# PHASE 5 — EXISTING PIPELINE EXCEPTIONS
# Do not modify these classes as part of SP-03.
# =============================================================================

class PipelineInitError(Exception):
    """Raised when IntentRouterAgent fails — stops entire pipeline"""


class AgentExecutionError(Exception):
    """Raised when an agent fails after MAX_RETRIES exhausted"""


class ToolConnectionError(Exception):
    """Raised when a tool (Tavily/Groq/Gemini/ChromaDB) is unreachable"""


class WorkflowStateError(Exception):
    """Raised when a required workflow_state key is missing or wrong type"""


class NonRetryableError(Exception):
    """Raised when a failure cannot succeed on retry — auth, malformed
    request, oversized payload, or invalid schema"""
   

# =============================================================================
# SP-03 — BASE APPLICATION EXCEPTION
# =============================================================================


class AppException(Exception):
    """
    Base class for HTTP-aware application exceptions.

    Subclasses define their own status_code, code, and default_message.
    An optional message overrides the default message.
    Optional headers allow exceptions to specify HTTP response headers.
    """

    status_code = 500
    code = "INTERNAL_ERROR"
    default_message = "An internal error occurred."
    default_headers: dict[str, str] = {}

    def __init__(
        self,
        message: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the application exception.

        Args:
            message: Optional user-facing message override.
            headers: Optional HTTP headers for the error response.
        """
        self.message = (
            message if message is not None else self.default_message
        )

        # Copy defaults so instances cannot mutate class-level headers.
        self.headers = dict(self.default_headers)
        if headers is not None:
            self.headers.update(headers)

        # Initialize Exception so str(exception) returns the message.
        super().__init__(self.message)


# =============================================================================
# AUTHENTICATION EXCEPTIONS — HTTP 401
# =============================================================================


class AuthenticationRequired(AppException):
    """Raised when authentication credentials are missing."""

    status_code = 401
    code = "AUTHENTICATION_REQUIRED"
    default_message = "Authentication is required."
    default_headers = {"WWW-Authenticate": "Bearer"}


class InvalidCredentials(AppException):
    """Raised when login credentials are invalid."""

    status_code = 401
    code = "INVALID_CREDENTIALS"
    default_message = "Invalid email or password."
    default_headers = {"WWW-Authenticate": "Bearer"}


class InvalidToken(AppException):
    """Raised when a supplied token is invalid."""

    status_code = 401
    code = "INVALID_TOKEN"
    default_message = "The token is invalid."
    default_headers = {"WWW-Authenticate": "Bearer"}


class TokenExpired(AppException):
    """Raised when a supplied token has expired."""

    status_code = 401
    code = "TOKEN_EXPIRED"
    default_message = "The token has expired."
    default_headers = {"WWW-Authenticate": "Bearer"}


class TokenRevoked(AppException):
    """Raised when a token has been revoked."""

    status_code = 401
    code = "TOKEN_REVOKED"
    default_headers = {"WWW-Authenticate": "Bearer"}
    default_message = "The token has been revoked."


# =============================================================================
# AUTHORIZATION EXCEPTIONS — HTTP 403
# =============================================================================


class Forbidden(AppException):
    """Raised when an authenticated user lacks permission."""

    status_code = 403
    code = "FORBIDDEN"
    default_message = "You do not have access to this resource."


# =============================================================================
# RESOURCE EXCEPTIONS — HTTP 404 AND 409
# =============================================================================


class ResourceNotFound(AppException):
    """Raised when a requested resource does not exist."""

    status_code = 404
    code = "RESOURCE_NOT_FOUND"
    default_message = "The resource was not found."


class ResourceConflict(AppException):
    """Raised when a resource conflicts with existing data."""

    status_code = 409
    code = "RESOURCE_CONFLICT"
    default_message = "The resource already exists."


# =============================================================================
# STORAGE EXCEPTIONS — HTTP 413 AND 422
# Preserve the existing names for SP-02 compatibility.
# =============================================================================


class FileTooLarge(AppException):
    """Raised when a file exceeds the configured maximum size."""

    status_code = 413
    code = "FILE_TOO_LARGE"
    default_message = "The file exceeds the size limit."


class UnsupportedFileType(AppException):
    """Raised when a file extension is not supported."""

    status_code = 422
    code = "UNSUPPORTED_FILE_TYPE"
    default_message = "This file type is not allowed."


# =============================================================================
# RATE LIMITING EXCEPTION — HTTP 429
# =============================================================================


class RateLimited(AppException):
    """Raised when a client exceeds the permitted request rate."""

    status_code = 429
    code = "RATE_LIMITED"
    default_message = "Too many requests."
