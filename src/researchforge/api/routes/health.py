"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from researchforge import __version__
from researchforge.api.schemas import HealthResponse
from researchforge.config.settings import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    summary = settings.active_providers_summary()
    return HealthResponse(
        status="ok",
        environment=summary["environment"],
        search_provider=summary["search_provider"],
        llm_provider=summary["llm_provider"],
        version=__version__,
    )
