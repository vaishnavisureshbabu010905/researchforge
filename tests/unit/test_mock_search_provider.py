from __future__ import annotations

import pytest

from researchforge.providers.mock import MockSearchProvider


@pytest.mark.asyncio
async def test_search_is_deterministic_for_same_query():
    provider = MockSearchProvider()
    first = await provider.search("ai coding agents", limit=5)
    second = await provider.search("ai coding agents", limit=5)
    assert [str(r.url) for r in first] == [str(r.url) for r in second]


@pytest.mark.asyncio
async def test_search_respects_limit():
    provider = MockSearchProvider()
    results = await provider.search("test query", limit=3)
    assert len(results) <= 3


@pytest.mark.asyncio
async def test_different_queries_produce_different_results():
    provider = MockSearchProvider()
    a = await provider.search("topic a", limit=3)
    b = await provider.search("topic b", limit=3)
    assert [str(r.url) for r in a] != [str(r.url) for r in b]


@pytest.mark.asyncio
async def test_scrape_returns_nonempty_content():
    provider = MockSearchProvider()
    page = await provider.scrape("https://example.com/article")
    assert page.content
    assert str(page.url) == "https://example.com/article"
