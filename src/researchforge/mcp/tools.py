"""MCP tool implementations.

Kept separate from `mcp/server.py` (which just registers these with FastMCP) so
the tool logic is independently testable without spinning up an MCP transport.
Reuses `api.dependencies.ResearchRegistry` — the same orchestration/persistence
path the HTTP API uses, so behavior is identical across both surfaces (see
docs/ARCHITECTURE.md "api/ and mcp/ ... neither contains research logic").
"""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field

from researchforge.api.dependencies import get_registry
from researchforge.evidence.manager import build_collection, normalize
from researchforge.models.claims import Claim
from researchforge.models.evidence import Evidence
from researchforge.models.research import ResearchMode
from researchforge.observability.logging import get_logger
from researchforge.storage.database import get_database
from researchforge.storage.repositories import ResearchJobRepository
from researchforge.verification.confidence import assess
from researchforge.verification.conflicts import find_conflicts

logger = get_logger(__name__)

_POLL_INTERVAL_SECONDS = 1.0
_MAX_WAIT_SECONDS = 180  # a single MCP tool call still returns eventually rather than hanging forever


class ResearchResult(BaseModel):
    research_id: str
    status: str
    query: str
    mode: str
    quality_score: int | None = None
    executive_summary: str | None = None
    key_findings: list[str] = Field(default_factory=list)
    citation_coverage_percent: float | None = None
    error: str | None = None


class ResearchStatusResult(BaseModel):
    research_id: str
    status: str
    iteration_count: int
    subquestions: list[str] = Field(default_factory=list)


class SourcesResult(BaseModel):
    research_id: str
    count: int
    sources: list[Evidence]


class ClaimVerificationResult(BaseModel):
    claim_text: str
    status: str
    confidence: float
    supporting_evidence_count: int
    conflicting_evidence_count: int


class HistoryItemResult(BaseModel):
    research_id: str
    query: str
    mode: str
    status: str
    quality_score: int | None = None


async def tool_research(query: str, mode: str = "deep", *, wait: bool = True) -> ResearchResult:
    """Run (or start) a research job. If `wait` is True, blocks (up to a bound) for completion."""
    registry = get_registry()
    try:
        research_mode = ResearchMode(mode)
    except ValueError as exc:
        raise ValueError(f"invalid mode '{mode}'; must be one of {[m.value for m in ResearchMode]}") from exc

    job = await registry.start(query, research_mode)

    if wait:
        elapsed = 0.0
        while elapsed < _MAX_WAIT_SECONDS:
            current = await registry.get_job(job.research_id)
            if current and current.status.value in ("completed", "failed", "partial"):
                break
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)
            elapsed += _POLL_INTERVAL_SECONDS

    return await tool_get_research(job.research_id)


async def tool_research_status(research_id: str) -> ResearchStatusResult:
    registry = get_registry()
    job = await registry.get_job(research_id)
    if job is None:
        raise ValueError(f"research job '{research_id}' not found")
    return ResearchStatusResult(
        research_id=job.research_id,
        status=job.status.value,
        iteration_count=job.iteration_count,
        subquestions=job.plan.subquestions if job.plan else [],
    )


async def tool_get_research(research_id: str) -> ResearchResult:
    registry = get_registry()
    job = await registry.get_job(research_id)
    if job is None:
        raise ValueError(f"research job '{research_id}' not found")

    live = registry.get_live_state(research_id)
    report = live.report if live else None
    if report is None:
        database = get_database()
        async with database.session() as session:
            report = await ResearchJobRepository(session).get_report(research_id)

    return ResearchResult(
        research_id=job.research_id,
        status=job.status.value,
        query=job.query,
        mode=job.mode.value,
        quality_score=report.quality.overall if report else None,
        executive_summary=report.executive_summary if report else None,
        key_findings=report.key_findings if report else [],
        citation_coverage_percent=report.citation_validation.coverage_percent if report else None,
        error=job.error,
    )


async def tool_get_sources(research_id: str) -> SourcesResult:
    registry = get_registry()
    job = await registry.get_job(research_id)
    if job is None:
        raise ValueError(f"research job '{research_id}' not found")

    live = registry.get_live_state(research_id)
    if live is not None:
        sources = live.evidence
    else:
        database = get_database()
        async with database.session() as session:
            sources = await ResearchJobRepository(session).get_evidence(research_id)
    return SourcesResult(research_id=research_id, count=len(sources), sources=sources)


async def tool_verify_claim(claim_text: str, research_id: str | None = None) -> ClaimVerificationResult:
    """Verify an arbitrary claim, either against a job's evidence pool or a fresh search.

    Mirrors api/routes/claims.py::verify_claim — kept as separate, simple code here
    rather than importing the FastAPI route function, since MCP tools must not
    depend on the HTTP layer (CLAUDE.md: api/ and mcp/ are peer adapters).
    """
    import re

    from researchforge.config.settings import get_settings
    from researchforge.providers.factory import get_search_provider

    if research_id:
        registry = get_registry()
        live = registry.get_live_state(research_id)
        if live is not None:
            evidence = live.evidence
        else:
            database = get_database()
            async with database.session() as session:
                evidence = await ResearchJobRepository(session).get_evidence(research_id)
    else:
        search = get_search_provider(get_settings())
        results = await search.search(claim_text, limit=5)
        raw = [normalize(result=r, page=None, research_task_id="ad_hoc", relevance_score=0.8) for r in results]
        evidence = build_collection(raw).items

    claim = Claim(text=claim_text)
    conflicting_ids = find_conflicts(claim, evidence)
    claim_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", claim_text)}
    supporting_ids = [
        e.evidence_id
        for e in evidence
        if len({w.lower() for w in re.findall(r"[a-zA-Z]{4,}", f"{e.title} {e.summary}")} & claim_words) >= 2
        and e.evidence_id not in conflicting_ids
    ]
    claim = claim.model_copy(update={"supporting_evidence_ids": supporting_ids, "conflicting_evidence_ids": conflicting_ids})
    result = assess(claim, {e.evidence_id: e for e in evidence})

    return ClaimVerificationResult(
        claim_text=claim_text,
        status=result.status.value,
        confidence=result.confidence,
        supporting_evidence_count=len(result.supporting_evidence_ids),
        conflicting_evidence_count=len(result.conflicting_evidence_ids),
    )


async def tool_get_research_history(limit: int = 20) -> list[HistoryItemResult]:
    database = get_database()
    async with database.session() as session:
        repo = ResearchJobRepository(session)
        jobs = await repo.list_history(limit=limit)
        items = []
        for job in jobs:
            report = await repo.get_report(job.research_id)
            items.append(
                HistoryItemResult(
                    research_id=job.research_id,
                    query=job.query,
                    mode=job.mode.value,
                    status=job.status.value,
                    quality_score=report.quality.overall if report else None,
                )
            )
        return items
