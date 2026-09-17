"""SearchProvider interface. See docs/ARCHITECTURE.md for the provider boundary rule."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class SearchResultItem(BaseModel):
    """A single raw search hit, prior to normalization into an Evidence model."""

    title: str
    url: HttpUrl
    snippet: str = ""
    published_at: datetime | None = None


class ScrapedPage(BaseModel):
    """Raw scraped/extracted content for one URL."""

    url: HttpUrl
    title: str
    content: str
    published_at: datetime | None = None


class SearchProvider(ABC):
    """Interface every search/scrape backend must implement.

    Orchestration and agents depend only on this interface — see
    config/settings.py for how a concrete instance is selected.
    """

    name: str = "base"

    @abstractmethod
    async def search(self, query: str, *, limit: int = 8) -> list[SearchResultItem]:
        """Run a web search and return raw result items (not yet normalized)."""

    @abstractmethod
    async def scrape(self, url: str) -> ScrapedPage:
        """Fetch and extract the readable content of a single URL."""

    async def extract(self, url: str, *, instructions: str = "") -> str:
        """Extract targeted content from a URL given natural-language instructions.

        Default implementation scrapes and returns the full content; providers with
        native structured-extraction support (e.g. Bright Data) may override this.
        """
        page = await self.scrape(url)
        return page.content

    async def discover(self, domain: str, *, topic: str = "") -> list[str]:
        """Discover candidate URLs within a domain related to a topic.

        Default implementation delegates to `search` scoped with a `site:` filter.
        """
        results = await self.search(f"site:{domain} {topic}".strip(), limit=10)
        return [str(r.url) for r in results]
