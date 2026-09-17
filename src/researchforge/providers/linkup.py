"""LinkUp search provider adapter.

Isolates the `linkup-sdk` dependency to this module only (see CLAUDE.md rule 2).
Import of the SDK is deferred into `__init__` so the rest of the app can be
imported even when `linkup-sdk` isn't installed (e.g. in mock-only environments).
"""

from __future__ import annotations

from datetime import datetime

from researchforge.providers.base import ScrapedPage, SearchProvider, SearchResultItem


class LinkUpSearchProvider(SearchProvider):
    """Adapter over LinkUp's search API.

    Configure via `RESEARCHFORGE_LINKUP_API_KEY`. If the key is missing,
    `config/settings.py::get_search_provider` falls back to `MockSearchProvider`
    rather than constructing this class — see that function for the switch logic.
    """

    name = "linkup"

    def __init__(self, api_key: str) -> None:
        try:
            from linkup import LinkupClient  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - exercised only without the dep installed
            raise RuntimeError(
                "The 'linkup-sdk' package is required for LinkUpSearchProvider. "
                "Install it (`pip install linkup-sdk`) or use the mock provider."
            ) from exc
        self._client = LinkupClient(api_key=api_key)

    async def search(self, query: str, *, limit: int = 8) -> list[SearchResultItem]:
        import asyncio

        response = await asyncio.to_thread(
            self._client.search, query=query, depth="standard", output_type="searchResults"
        )
        items: list[SearchResultItem] = []
        for raw in getattr(response, "results", [])[:limit]:
            items.append(
                SearchResultItem(
                    title=getattr(raw, "name", "") or getattr(raw, "title", "Untitled"),
                    url=getattr(raw, "url"),
                    snippet=getattr(raw, "content", "") or getattr(raw, "snippet", ""),
                    published_at=_safe_date(getattr(raw, "published_at", None)),
                )
            )
        return items

    async def scrape(self, url: str) -> ScrapedPage:
        import asyncio

        response = await asyncio.to_thread(
            self._client.search, query=url, depth="deep", output_type="searchResults"
        )
        results = getattr(response, "results", [])
        content = results[0].content if results and hasattr(results[0], "content") else ""
        title = results[0].name if results and hasattr(results[0], "name") else url
        return ScrapedPage(url=url, title=title, content=content or "")


def _safe_date(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None
