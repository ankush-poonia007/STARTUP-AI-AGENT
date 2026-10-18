
"""Standardized API exception handlers."""

import logging
import uuid
from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from src.core.exceptions import AppException

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


def _get_request_id(request: Request) -> str:
    """Read the middleware-generated request ID defensively."""
    request_id = getattr(request.state, "request_id", None)

    if isinstance(request_id, str) and request_id:
        return request_id

    return str(uuid.uuid4())


def _build_error_response(
    status: int,
    code: str,
    message: str,
    request_id: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build the common error envelope."""
    response_headers = dict(headers or {})
    response_headers[REQUEST_ID_HEADER] = request_id

    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
        headers=response_headers,
    )


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """Handle expected application exceptions."""
    request_id = _get_request_id(request)

    log_message = (
        "Application exception request_id=%s method=%s path=%s code=%s"
    )
    log_args = (
        request_id,
        request.method,
        request.url.path,
        exc.code,
    )

    if 400 <= exc.status_code < 500:
        logger.warning(log_message, *log_args)
    elif exc.status_code >= 500:
        logger.error(log_message, *log_args)

    return _build_error_response(
        status=exc.status_code,
        code=exc.code,
        message=exc.message,
        request_id=request_id,
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle validation errors without exposing submitted values."""
    request_id = _get_request_id(request)
    errors = exc.errors()

    if errors:
        first_error = errors[0]
        location = first_error.get("loc", ())
        field = str(location[-1]) if location else "request"
        validation_message = str(
            first_error.get("msg", "Invalid value.")
        )
        message = f"{field}: {validation_message}"
    else:
        message = "Request validation failed."

    # Never log exc.errors(), its input values, or the request body.
    logger.warning(
        "Request validation failed request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )

    return _build_error_response(
        status=422,
        code="VALIDATION_ERROR",
        message=message,
        request_id=request_id,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle Starlette HTTP exceptions using standard status messages."""
    request_id = _get_request_id(request)

    if exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 405:
        code = "METHOD_NOT_ALLOWED"
    else:
        code = "HTTP_ERROR"

    try:
        message = HTTPStatus(exc.status_code).phrase
    except ValueError:
        message = "HTTP error."

    logger.warning(
        "HTTP exception request_id=%s method=%s path=%s status=%s",
        request_id,
        request.method,
        request.url.path,
        exc.status_code,
    )

    return _build_error_response(
        status=exc.status_code,
        code=code,
        message=message,
        request_id=request_id,
        headers=exc.headers,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Log unexpected failures while returning no internal details."""
    request_id = _get_request_id(request)

    logger.error(
        "Unhandled exception request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return _build_error_response(
        status=500,
        code="INTERNAL_ERROR",
        message="An internal error occurred.",
        request_id=request_id,
    )
