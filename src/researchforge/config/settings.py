"""Centralized, environment-driven configuration.

Nothing outside this module should call `os.environ` directly for application
configuration — this is the single seam that lets tests and CI run with zero
external credentials while production deployments opt into real providers.
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SearchProviderName(str, Enum):
    MOCK = "mock"
    LINKUP = "linkup"
    BRIGHTDATA = "brightdata"


class LLMProviderName(str, Enum):
    MOCK = "mock"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"


# Domain reputation tiers used by the credibility scorer. Deliberately small and
# editable — this is a starting point, not a claim of completeness.
DOMAIN_REPUTATION: dict[str, int] = {
    # tier 3: primary / standards / official docs — highest trust
    "arxiv.org": 3,
    "docs.python.org": 3,
    "github.com": 3,
    "developer.mozilla.org": 3,
    "*.gov": 3,
    "*.edu": 3,
    # tier 2: reputable secondary reporting
    "reuters.com": 2,
    "nature.com": 2,
    "acm.org": 2,
    "ieee.org": 2,
    "techcrunch.com": 2,
    # tier 1: general web / blogs — neutral default applies if not listed at all
    "medium.com": 1,
}


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / `.env`."""

    model_config = SettingsConfigDict(env_prefix="RESEARCHFORGE_", env_file=".env", extra="ignore")

    environment: str = Field(default="development")

    # --- providers -----------------------------------------------------
    search_provider: SearchProviderName = Field(default=SearchProviderName.MOCK)
    llm_provider: LLMProviderName = Field(default=LLMProviderName.MOCK)

    linkup_api_key: str | None = Field(default=None)
    brightdata_api_key: str | None = Field(default=None)
    brightdata_zone: str | None = Field(default=None)

    anthropic_api_key: str | None = Field(default=None)
    openai_api_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)
    ollama_base_url: str = Field(default="http://localhost:11434")

    # per-task model routing (task -> model id); providers interpret the id
    planner_model: str = Field(default="mock-reasoning")
    extraction_model: str = Field(default="mock-fast")
    fact_check_model: str = Field(default="mock-reasoning")
    synthesis_model: str = Field(default="mock-quality")

    # --- persistence -----------------------------------------------------
    database_url: str = Field(default="sqlite+aiosqlite:///./researchforge.db")

    # --- orchestration limits -----------------------------------------------------
    max_concurrent_research_jobs: int = Field(default=5)
    default_task_timeout_seconds: int = Field(default=60)
    provider_max_retries: int = Field(default=3)
    provider_retry_backoff_seconds: float = Field(default=1.5)

    # --- API -----------------------------------------------------
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    max_request_body_bytes: int = Field(default=1_000_000)
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- observability -----------------------------------------------------
    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=True)

    def active_providers_summary(self) -> dict[str, str]:
        """Human-readable summary of which providers are actually live vs. mocked.

        Used at startup and in `/api/health` so the app never silently pretends
        a live provider is active when credentials are missing.
        """
        search = self.search_provider.value
        if self.search_provider == SearchProviderName.LINKUP and not self.linkup_api_key:
            search = "mock (LINKUP_API_KEY missing, falling back)"
        if self.search_provider == SearchProviderName.BRIGHTDATA and not self.brightdata_api_key:
            search = "mock (BRIGHTDATA_API_KEY missing, falling back)"

        llm = self.llm_provider.value
        key_map = {
            LLMProviderName.ANTHROPIC: self.anthropic_api_key,
            LLMProviderName.OPENAI: self.openai_api_key,
            LLMProviderName.GEMINI: self.gemini_api_key,
        }
        if self.llm_provider in key_map and not key_map[self.llm_provider]:
            llm = f"mock ({self.llm_provider.value.upper()}_API_KEY missing, falling back)"

        return {"search_provider": search, "llm_provider": llm, "environment": self.environment}


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Tests override via `RESEARCHFORGE_*` env vars
    and should call `get_settings.cache_clear()` after mutating `os.environ`.
    """
    return Settings()


def is_test_environment() -> bool:
    return os.environ.get("RESEARCHFORGE_ENVIRONMENT", "development") == "test"
