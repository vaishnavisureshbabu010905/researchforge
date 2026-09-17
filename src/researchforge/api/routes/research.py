"""Research job endpoints: create, status, sources, claims, report, events (SSE), history."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from researchforge.api.dependencies import ResearchRegistry, get_registry
from researchforge.api.schemas import (
    ClaimsResponse,
    CreateResearchRequest,
    CreateResearchResponse,
    HistoryItem,
    HistoryResponse,
    ReportResponse,
    ResearchStatusResponse,
    SourcesResponse,
)
from researchforge.observability.logging import get_logger
from researchforge.storage.database import Database, get_database
from researchforge.storage.repositories import ResearchJobRepository

logger = get_logger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("", response_model=CreateResearchResponse, status_code=202)
async def create_research(
    body: CreateResearchRequest, registry: ResearchRegistry = Depends(get_registry)
) -> CreateResearchResponse:
    job = await registry.start(body.query, body.mode)
    return CreateResearchResponse(research_id=job.research_id, status=job.status.value, mode=job.mode)


async def _get_job_or_404(research_id: str, registry: ResearchRegistry):
    job = await registry.get_job(research_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"research job '{research_id}' not found")
    return job


@router.get("/history", response_model=HistoryResponse)
async def history(database: Database = Depends(get_database)) -> HistoryResponse:
    async with database.session() as session:
        jobs = await ResearchJobRepository(session).list_history()
        items = []
        for job in jobs:
            report = await ResearchJobRepository(session).get_report(job.research_id)
            items.append(
                HistoryItem(
                    research_id=job.research_id,
                    query=job.query,
                    mode=job.mode,
                    status=job.status.value,
                    quality=report.quality.overall if report else None,
                )
            )
    return HistoryResponse(items=items)


@router.get("/{research_id}", response_model=ResearchStatusResponse)
@router.get("/{research_id}/status", response_model=ResearchStatusResponse)
async def get_research_status(
    research_id: str, registry: ResearchRegistry = Depends(get_registry)
) -> ResearchStatusResponse:
    job = await _get_job_or_404(research_id, registry)
    return ResearchStatusResponse(
        research_id=job.research_id,
        query=job.query,
        mode=job.mode,
        status=job.status.value,
        iteration_count=job.iteration_count,
        plan=job.plan,
        error=job.error,
    )


@router.get("/{research_id}/sources", response_model=SourcesResponse)
async def get_sources(
    research_id: str,
    registry: ResearchRegistry = Depends(get_registry),
    database: Database = Depends(get_database),
) -> SourcesResponse:
    await _get_job_or_404(research_id, registry)
    live = registry.get_live_state(research_id)
    if live is not None:
        sources = live.evidence
    else:
        async with database.session() as session:
            sources = await ResearchJobRepository(session).get_evidence(research_id)
    return SourcesResponse(research_id=research_id, count=len(sources), sources=sources)


@router.get("/{research_id}/claims", response_model=ClaimsResponse)
async def get_claims(
    research_id: str,
    registry: ResearchRegistry = Depends(get_registry),
    database: Database = Depends(get_database),
) -> ClaimsResponse:
    await _get_job_or_404(research_id, registry)
    live = registry.get_live_state(research_id)
    if live is not None:
        claims = live.claims
    else:
        async with database.session() as session:
            claims = await ResearchJobRepository(session).get_claims(research_id)
    return ClaimsResponse(research_id=research_id, count=len(claims), claims=claims)


@router.get("/{research_id}/report", response_model=ReportResponse)
async def get_report(
    research_id: str,
    registry: ResearchRegistry = Depends(get_registry),
    database: Database = Depends(get_database),
) -> ReportResponse:
    await _get_job_or_404(research_id, registry)
    live = registry.get_live_state(research_id)
    report = live.report if live is not None else None
    if report is None:
        async with database.session() as session:
            report = await ResearchJobRepository(session).get_report(research_id)
    if report is None:
        raise HTTPException(status_code=409, detail="report not yet available; research still in progress")
    return ReportResponse(report=report)


@router.get("/{research_id}/events")
async def stream_events(
    research_id: str,
    registry: ResearchRegistry = Depends(get_registry),
    database: Database = Depends(get_database),
) -> StreamingResponse:
    """Stream persisted history plus live events, keeping the connection alive until terminal."""
    await _get_job_or_404(research_id, registry)
    live = registry.get_live_state(research_id)

    async def event_generator():
        seen: set[str] = set()

        async with database.session() as session:
            persisted_events = await ResearchJobRepository(session).get_events(research_id)

        for event in persisted_events:
            seen.add(event.event_id)
            yield _sse(event.event_type, event.model_dump_json())

        job = await registry.get_job(research_id)
        terminal = {"completed": "research_completed", "partial": "research_partial", "failed": "research_failed"}

        if live is None:
            if job is not None and job.status.value in terminal:
                event_type = terminal[job.status.value]
                if not any(e.event_type == event_type for e in persisted_events):
                    yield _sse(
                        event_type,
                        json.dumps({"research_id": research_id, "status": job.status.value, "message": "terminal status"}),
                    )
            return

        queue = live.subscribe()
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    if event.event_id in seen:
                        continue
                    seen.add(event.event_id)
                    yield _sse(event.event_type, event.model_dump_json())
                    if event.event_type in terminal.values():
                        break
                except asyncio.TimeoutError:
                    yield _sse("keepalive", "{}")
                    current = await registry.get_job(research_id)
                    if current is not None and current.status.value in terminal:
                        event_type = terminal[current.status.value]
                        yield _sse(
                            event_type,
                            json.dumps({"research_id": research_id, "status": current.status.value, "message": "terminal status"}),
                        )
                        break
        finally:
            live.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"
