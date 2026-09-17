"""Dependency injection wiring for the FastAPI app.

`ResearchRegistry` is the bridge between the (in-memory, per-process) live
`ResearchState` objects that SSE streams read from, and the durable
`ResearchJobRepository` that persists everything to the database. A job's live
state exists in-memory for the lifetime of the process; history/replay after a
restart comes from the database.
"""

from __future__ import annotations

import asyncio

from researchforge.config.settings import Settings, get_settings
from researchforge.models.research import ResearchJob, ResearchMode
from researchforge.observability.logging import get_logger
from researchforge.orchestration.orchestrator import Orchestrator, new_job
from researchforge.orchestration.state import ResearchState
from researchforge.providers.factory import get_llm_provider, get_search_provider
from researchforge.storage.database import Database, get_database
from researchforge.storage.repositories import ResearchJobRepository

logger = get_logger(__name__)


class ResearchRegistry:
    """Owns in-flight and recently-completed `ResearchState` objects, and persists
    them via the repository as they progress. One instance per process.
    """

    def __init__(self, *, settings: Settings, database: Database) -> None:
        self.settings = settings
        self.database = database
        self._states: dict[str, ResearchState] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._max_concurrent = asyncio.Semaphore(settings.max_concurrent_research_jobs)
        self._persisted_events: dict[str, set[str]] = {}

    def _build_orchestrator(self, *, checkpoint=None) -> Orchestrator:
        search = get_search_provider(self.settings)
        llm = get_llm_provider(self.settings)
        return Orchestrator(settings=self.settings, search=search, llm=llm, checkpoint=checkpoint)

    async def start(self, query: str, mode: ResearchMode) -> ResearchJob:
        job = new_job(query, mode)
        state = ResearchState(job=job)
        self._states[job.research_id] = state
        self._persisted_events[job.research_id] = set()

        async with self.database.session() as session:
            await ResearchJobRepository(session).save_job(job)

        asyncio.create_task(self._run_and_persist(state))
        return job

    async def _run_and_persist(self, state: ResearchState) -> None:
        async with self._max_concurrent:
            orchestrator = self._build_orchestrator(checkpoint=self._persist)
            try:
                await orchestrator.run(state)
            except Exception as exc:  # noqa: BLE001 - last-resort guard around the background task
                logger.error("registry_run_failed", research_id=state.job.research_id, error=str(exc))
            finally:
                await self._persist(state)

    async def _persist(self, state: ResearchState) -> None:
        async with self.database.session() as session:
            repo = ResearchJobRepository(session)
            await repo.save_job(state.job)
            if state.evidence:
                await repo.save_evidence(state.job.research_id, state.evidence)
            if state.claims:
                await repo.save_claims(state.job.research_id, state.claims)
            if state.report:
                await repo.save_report(state.report)
            persisted = self._persisted_events.setdefault(state.job.research_id, set())
            for event in state.events:
                if event.event_id not in persisted:
                    await repo.append_event(event)
                    persisted.add(event.event_id)

        if state.job.status.value in {"completed", "partial", "failed"}:
            self._states.pop(state.job.research_id, None)
            self._persisted_events.pop(state.job.research_id, None)

    def get_live_state(self, research_id: str) -> ResearchState | None:
        return self._states.get(research_id)

    async def get_job(self, research_id: str) -> ResearchJob | None:
        live = self.get_live_state(research_id)
        if live is not None:
            return live.job
        async with self.database.session() as session:
            return await ResearchJobRepository(session).get_job(research_id)


_registry: ResearchRegistry | None = None


def get_registry() -> ResearchRegistry:
    global _registry
    if _registry is None:
        settings = get_settings()
        _registry = ResearchRegistry(settings=settings, database=get_database(settings.database_url))
    return _registry


def reset_registry_singleton() -> None:
    """Test-only helper."""
    global _registry
    _registry = None
