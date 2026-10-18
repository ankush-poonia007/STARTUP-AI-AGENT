"""
CoFoundr AI — Common API Schemas.

Contains reusable Pydantic schemas shared across API endpoints.
"""

from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    """Structured details describing an API error."""

    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    """Standard API error response envelope."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "password: String should have at least 8 characters",
                    "request_id": "a1b2c3d4-5678-4abc-9def-1234567890ab",
                }
            }
        }
    )

    error: ErrorDetail