"""In-memory + event-emitting research job state.

`ResearchState` is the orchestrator's working copy of a job while it runs; it is
persisted through `storage/repositories.py` at each transition and is what the
SSE stream (`api/routes/research.py`) is fed from via `subscribe()`.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from researchforge.models.claims import Claim
from researchforge.models.evidence import Evidence
from researchforge.models.reports import ResearchReport
from researchforge.models.research import ResearchEvent, ResearchJob, ResearchJobStatus


@dataclass
class ResearchState:
    job: ResearchJob
    evidence: list[Evidence] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    report: ResearchReport | None = None
    _subscribers: list[asyncio.Queue] = field(default_factory=list)
    _events: list[ResearchEvent] = field(default_factory=list)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(q)
        for evt in self._events:  # replay history to a late subscriber
            q.put_nowait(evt)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    def emit(self, event_type: str, message: str, **data: object) -> ResearchEvent:
        evt = ResearchEvent(research_id=self.job.research_id, event_type=event_type, message=message, data=data)
        self._events.append(evt)
        for q in list(self._subscribers):
            q.put_nowait(evt)
        return evt

    def set_status(self, status: ResearchJobStatus) -> None:
        from datetime import datetime, timezone

        self.job.status = status
        self.job.updated_at = datetime.now(timezone.utc)

    @property
    def events(self) -> list[ResearchEvent]:
        return list(self._events)
