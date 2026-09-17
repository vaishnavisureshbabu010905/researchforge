"""Shared research-agent logic: search -> scrape top results -> normalize to Evidence.

web_researcher.py / technical_researcher.py / academic_researcher.py subclass this
with a domain-specific query augmentation and preferred source filter, rather than
each reimplementing the same search-and-normalize loop.
"""

from __future__ import annotations

import asyncio

from researchforge.agents.base import BaseAgent
from researchforge.evidence.manager import normalize
from researchforge.models.evidence import Evidence


class ResearcherAgent(BaseAgent):
    role = "researcher"
    query_suffix: str = ""
    scrape_top_n: int = 4

    async def research(self, subquestion: str, *, task_id: str, min_results: int) -> list[Evidence]:
        query = f"{subquestion} {self.query_suffix}".strip()
        self.logger.info("search_started", task_id=task_id, query=query, agent=self.role)

        results = await self.search.search(query, limit=max(min_results, self.scrape_top_n))
        if not results:
            self.logger.warning("search_returned_no_results", task_id=task_id, query=query)
            return []

        to_scrape = results[: self.scrape_top_n]
        pages = await asyncio.gather(*(self.search.scrape(str(r.url)) for r in to_scrape), return_exceptions=True)

        evidence: list[Evidence] = []
        for i, result in enumerate(results):
            page = pages[i] if i < len(pages) and not isinstance(pages[i], Exception) else None
            relevance = max(0.2, 1.0 - (i * 0.1))  # simple rank-based relevance proxy
            evidence.append(normalize(result=result, page=page, research_task_id=task_id, relevance_score=relevance))
            self.logger.info("source_processed", task_id=task_id, url=str(result.url))

        return evidence
