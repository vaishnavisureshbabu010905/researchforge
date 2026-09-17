"""FastAPI application factory.

Run with: `uvicorn researchforge.api.app:app --reload` (or `make run`).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from researchforge.api.routes import claims, health, research
from researchforge.api.schemas import ErrorResponse
from researchforge.config.settings import get_settings
from researchforge.observability.logging import configure_logging, get_logger
from researchforge.storage.database import get_database

logger = get_logger(__name__)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects request bodies larger than `settings.max_request_body_bytes` (security requirement)."""

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_body_bytes:
            return JSONResponse(
                status_code=413,
                content=ErrorResponse(error="payload_too_large", detail="Request body exceeds the configured limit.").model_dump(),
            )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)
    database = get_database(settings.database_url)
    await database.create_all()
    logger.info("app_startup", **settings.active_providers_summary())
    yield
    await database.dispose()
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ResearchForge API",
        description="Multi-Agent Deep Research, Built for Evidence.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never leak stack traces or internal details to the client (security requirement).
        logger.error("unhandled_exception", path=str(request.url.path), error_type=type(exc).__name__, error=str(exc))
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error="internal_server_error", detail="An unexpected error occurred.").model_dump(),
        )

    app.include_router(health.router)
    app.include_router(research.router)
    app.include_router(claims.router)

    return app


app = create_app()
