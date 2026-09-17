"""Bright Data provider adapter.

Bright Data exposes both a REST "Web Unlocker"/SERP API and an MCP server. This
adapter targets the REST surface directly via `httpx` so ResearchForge's own MCP
server (src/researchforge/mcp/server.py) doesn't need to proxy another MCP server
inside itself. Swapping to Bright Data's MCP server instead would only require a
new class implementing `SearchProvider` — orchestration code does not change.

Configure via `RESEARCHFORGE_BRIGHTDATA_API_KEY` (and optionally
`RESEARCHFORGE_BRIGHTDATA_ZONE`). See README.md#provider-architecture for setup.
"""

from __future__ import annotations

from datetime import datetime

from researchforge.providers.base import ScrapedPage, SearchProvider, SearchResultItem

_SERP_ENDPOINT = "https://api.brightdata.com/serp/req"
_UNLOCKER_ENDPOINT = "https://api.brightdata.com/request"


class BrightDataSearchProvider(SearchProvider):
    """Adapter over Bright Data's SERP + Web Unlocker REST APIs."""

    name = "brightdata"

    def __init__(self, api_key: str, zone: str | None = None) -> None:
        self._api_key = api_key
        self._zone = zone or "serp_api1"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    async def search(self, query: str, *, limit: int = 8) -> list[SearchResultItem]:
        import httpx

        payload = {"zone": self._zone, "query": query, "format": "json", "num_results": limit}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(_SERP_ENDPOINT, json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()

        items: list[SearchResultItem] = []
        for raw in data.get("organic", [])[:limit]:
            items.append(
                SearchResultItem(
                    title=raw.get("title", "Untitled"),
                    url=raw.get("link"),
                    snippet=raw.get("snippet", ""),
                    published_at=_safe_date(raw.get("date")),
                )
            )
        return items

    async def scrape(self, url: str) -> ScrapedPage:
        import httpx

        payload = {"zone": self._zone, "url": url, "format": "raw"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(_UNLOCKER_ENDPOINT, json=payload, headers=self._headers())
            resp.raise_for_status()
            content = resp.text

        return ScrapedPage(url=url, title=url, content=content)


def _safe_date(value: object) -> datetime | None:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None
