"""Provider selection: the one place that turns Settings into live provider instances.

Falls back to mock providers whenever a configured provider is missing required
credentials, and always logs which provider is actually active — see
Settings.active_providers_summary() and CLAUDE.md rule 3.
"""

from __future__ import annotations

from researchforge.config.settings import LLMProviderName, SearchProviderName, Settings
from researchforge.observability.logging import get_logger
from researchforge.providers.base import SearchProvider
from researchforge.providers.llm.base import LLMProvider
from researchforge.providers.llm.mock import MockLLMProvider
from researchforge.providers.mock import MockSearchProvider

logger = get_logger(__name__)


def get_search_provider(settings: Settings) -> SearchProvider:
    if settings.search_provider == SearchProviderName.LINKUP and settings.linkup_api_key:
        from researchforge.providers.linkup import LinkUpSearchProvider

        return LinkUpSearchProvider(api_key=settings.linkup_api_key)

    if settings.search_provider == SearchProviderName.BRIGHTDATA and settings.brightdata_api_key:
        from researchforge.providers.brightdata import BrightDataSearchProvider

        return BrightDataSearchProvider(api_key=settings.brightdata_api_key, zone=settings.brightdata_zone)

    if settings.search_provider != SearchProviderName.MOCK:
        logger.warning(
            "search_provider_fallback_to_mock",
            configured=settings.search_provider.value,
            reason="missing_api_key",
        )
    return MockSearchProvider()


def get_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == LLMProviderName.ANTHROPIC and settings.anthropic_api_key:
        from researchforge.providers.llm.anthropic import AnthropicLLMProvider

        return AnthropicLLMProvider(api_key=settings.anthropic_api_key)

    if settings.llm_provider == LLMProviderName.OPENAI and settings.openai_api_key:
        from researchforge.providers.llm.openai import OpenAILLMProvider

        return OpenAILLMProvider(api_key=settings.openai_api_key)

    if settings.llm_provider == LLMProviderName.OLLAMA:
        from researchforge.providers.llm.ollama import OllamaLLMProvider

        return OllamaLLMProvider(base_url=settings.ollama_base_url)

    if settings.llm_provider != LLMProviderName.MOCK:
        logger.warning("llm_provider_fallback_to_mock", configured=settings.llm_provider.value, reason="missing_api_key")
    return MockLLMProvider()
