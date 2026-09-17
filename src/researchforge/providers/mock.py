"""Deterministic mock search provider.

This is not a test-only stub — per CLAUDE.md rule 3, it is a first-class provider
that lets the entire application run and be demoed with zero external credentials.
Output is deterministic (seeded from the query string) so tests can assert on it.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from researchforge.providers.base import ScrapedPage, SearchProvider, SearchResultItem

_FAKE_DOMAINS = [
    ("docs.python.org", "Official documentation"),
    ("arxiv.org", "Academic preprint"),
    ("github.com", "Open-source repository"),
    ("techcrunch.com", "Industry news"),
    ("engineering.example-corp.com", "Engineering blog"),
    ("news.ycombinator.com", "Community discussion"),
    ("reuters.com", "Wire news"),
    ("medium.com", "Independent blog"),
]


def _seed(*parts: str) -> int:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return int(h[:8], 16)


class MockSearchProvider(SearchProvider):
    """Generates plausible, deterministic search results and page content."""

    name = "mock"

    async def search(self, query: str, *, limit: int = 8) -> list[SearchResultItem]:
        results: list[SearchResultItem] = []
        n = min(limit, len(_FAKE_DOMAINS))
        for i in range(n):
            domain, kind = _FAKE_DOMAINS[i]
            seed = _seed(query, domain, str(i))
            days_ago = seed % 900
            results.append(
                SearchResultItem(
                    title=f"{kind}: {query.strip().capitalize()} — result {i + 1}",
                    url=f"https://{domain}/articles/{seed % 100000}",
                    snippet=(
                        f"A {kind.lower()} discussing '{query.strip()}'. "
                        f"This mock result exists so ResearchForge can run without a live "
                        f"search API key; see providers/mock.py."
                    ),
                    published_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
                )
            )
        return results

    async def scrape(self, url: str) -> ScrapedPage:
        seed = _seed(url)
        title = f"Mock content for {url}"
        content = (
            f"[MOCK CONTENT] This is deterministic placeholder content generated because no "
            f"live search/scrape provider is configured (see providers/mock.py). "
            f"In a real deployment this would be the extracted, cleaned text of {url}. "
            f"Simulated key point #{seed % 7 + 1}: the topic involves trade-offs between "
            f"performance, maintainability, and correctness that a real source would "
            f"substantiate with specifics, benchmarks, or citations."
        )
        return ScrapedPage(
            url=url,
            title=title,
            content=content,
            published_at=datetime.now(timezone.utc) - timedelta(days=seed % 400),
        )
