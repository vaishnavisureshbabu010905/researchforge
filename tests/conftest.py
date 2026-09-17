"""Shared pytest fixtures: force mock providers and an in-memory SQLite DB for every test."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("RESEARCHFORGE_ENVIRONMENT", "test")
os.environ.setdefault("RESEARCHFORGE_SEARCH_PROVIDER", "mock")
os.environ.setdefault("RESEARCHFORGE_LLM_PROVIDER", "mock")
os.environ.setdefault("RESEARCHFORGE_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Every test gets fresh settings/database/registry singletons so tests don't leak state."""
    from researchforge.api.dependencies import reset_registry_singleton
    from researchforge.config.settings import get_settings
    from researchforge.storage.database import reset_database_singleton

    get_settings.cache_clear()
    reset_database_singleton()
    reset_registry_singleton()
    yield
    get_settings.cache_clear()
    reset_database_singleton()
    reset_registry_singleton()


@pytest.fixture
def mock_search():
    from researchforge.providers.mock import MockSearchProvider

    return MockSearchProvider()


@pytest.fixture
def mock_llm():
    from researchforge.providers.llm.mock import MockLLMProvider

    return MockLLMProvider()


@pytest.fixture
async def lifespan_client():
    """HTTP client that exercises FastAPI startup/shutdown lifespan."""
    import httpx
    from researchforge.api.app import create_app

    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
