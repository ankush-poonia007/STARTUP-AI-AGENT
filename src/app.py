"""FastAPI application factory and process lifespan wiring."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from src.api.routers.auth import router as auth_router
from src.api.routers.health import router as health_router
from src.core.config import Settings, settings
from src.core.exceptions import AppException
from src.infrastructure.chroma.client import create_chroma_client
from src.infrastructure.chroma.collection import create_phase6_collections
from src.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)
from src.infrastructure.state_keys import (
    CHROMA_CLIENT_STATE_KEY,
    CHROMA_DOCUMENTS_STATE_KEY,
    CHROMA_MEMORIES_STATE_KEY,
    EMBEDDER_STATE_KEY,
    ENGINE_STATE_KEY,
    FILE_STORAGE_STATE_KEY,
    SESSION_FACTORY_STATE_KEY,
)
from src.infrastructure.storage.file_storage import create_file_storage
from src.middleware.exception_handler import (
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.middleware.request_id import RequestIDMiddleware

logger = logging.getLogger(__name__)


def _create_embedder():
    """Import and construct the embedder only during application startup."""
    from src.infrastructure.chroma.embedder import Embedder

    return Embedder()


def create_app(app_settings: Settings = settings) -> FastAPI:
    """Build the API application without initializing infrastructure."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        engine = None

        try:
            engine = create_database_engine(app_settings.database_url)
            setattr(application.state, ENGINE_STATE_KEY, engine)
            session_factory = create_session_factory(engine)
            setattr(
                application.state,
                SESSION_FACTORY_STATE_KEY,
                session_factory,
            )
            logger.info("Database engine and session factory configured.")

            try:
                chroma_client = create_chroma_client(
                    app_settings.chroma_persist_directory
                )
            except Exception as exc:
                logger.exception(
                    "Failed to initialize Chroma at configured path %s.",
                    app_settings.chroma_persist_directory,
                )
                raise RuntimeError(
                    "Unable to initialize Chroma storage at "
                    f"{app_settings.chroma_persist_directory!r}."
                ) from exc

            setattr(
                application.state,
                CHROMA_CLIENT_STATE_KEY,
                chroma_client,
            )
            logger.info(
                "Chroma client configured at %s.",
                app_settings.chroma_persist_directory,
            )

            documents, memories = create_phase6_collections(chroma_client)
            setattr(
                application.state,
                CHROMA_DOCUMENTS_STATE_KEY,
                documents,
            )
            setattr(
                application.state,
                CHROMA_MEMORIES_STATE_KEY,
                memories,
            )
            logger.info("Chroma collections configured.")

            setattr(
                application.state,
                FILE_STORAGE_STATE_KEY,
                create_file_storage(),
            )
            logger.info("File storage configured.")

            setattr(
                application.state,
                EMBEDDER_STATE_KEY,
                _create_embedder(),
            )
            logger.info("Embedder configured.")
            logger.info(
                "Application startup complete: environment=%s chroma_path=%s",
                app_settings.environment,
                app_settings.chroma_persist_directory,
            )

            yield
        finally:
            if engine is not None:
                await engine.dispose()
                logger.info("Database engine disposed.")

    application = FastAPI(
        title="CoFoundr AI API",
        lifespan=lifespan,
    )

    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
        ],
        expose_headers=["X-Request-ID"],
    )

    application.add_exception_handler(
        AppException,
        app_exception_handler,
    )
    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    application.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )
    application.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

    application.include_router(
        health_router,
        prefix="/api/v1",
    )
    application.include_router(
        auth_router,
        prefix="/api/v1",
    )

    return application


app = create_app()