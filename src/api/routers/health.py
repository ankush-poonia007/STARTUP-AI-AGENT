"""Liveness and readiness endpoints."""

import asyncio
import logging

from fastapi import APIRouter, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.responses import JSONResponse

from src.core.constants import TIMEOUT_DATABASE
from src.infrastructure.state_keys import (
    CHROMA_CLIENT_STATE_KEY,
    ENGINE_STATE_KEY,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


async def _check_postgres(engine: AsyncEngine | None) -> str:
    """Run a bounded trivial query and hide database details from callers."""
    try:
        if engine is None:
            raise RuntimeError("Database engine is not configured.")

        async def ping() -> None:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))

        await asyncio.wait_for(ping(), timeout=TIMEOUT_DATABASE)
    except Exception:
        logger.exception("PostgreSQL readiness check failed.")
        return "error"

    return "ok"


async def _check_chroma(client: object | None) -> str:
    """Run a bounded Chroma heartbeat and hide client details from callers."""
    try:
        if client is None:
            raise RuntimeError("Chroma client is not configured.")

        heartbeat = getattr(client, "heartbeat")
        await asyncio.wait_for(
            asyncio.to_thread(heartbeat),
            timeout=TIMEOUT_DATABASE,
        )
    except Exception:
        logger.exception("Chroma readiness check failed.")
        return "error"

    return "ok"


@router.get("/live")
async def live() -> dict[str, str]:
    """Report that the process is running without checking dependencies."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    """Report whether the database and Chroma are ready to serve requests."""
    engine = getattr(request.app.state, ENGINE_STATE_KEY, None)
    chroma_client = getattr(
        request.app.state,
        CHROMA_CLIENT_STATE_KEY,
        None,
    )
    postgres_status, chroma_status = await asyncio.gather(
        _check_postgres(engine),
        _check_chroma(chroma_client),
    )

    dependencies = {
        "postgres": postgres_status,
        "chroma": chroma_status,
    }
    is_ready = all(status == "ok" for status in dependencies.values())

    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={
            "status": "ok" if is_ready else "degraded",
            "dependencies": dependencies,
        },
    )
