from __future__ import annotations

import pytest

from researchforge.models.research import ResearchJobStatus, ResearchMode
from researchforge.orchestration.orchestrator import new_job
from researchforge.orchestration.state import ResearchState


def test_new_job_starts_pending():
    state = ResearchState(job=new_job("A sufficiently long research question", ResearchMode.QUICK))
    assert state.job.status == ResearchJobStatus.PENDING
    assert state.events == []


def test_state_emits_events_and_replays_to_late_subscriber():
    state = ResearchState(job=new_job("A sufficiently long research question", ResearchMode.QUICK))
    first = state.emit("plan_created", "plan")
    second = state.emit("research_completed", "done")

    queue = state.subscribe()
    assert queue.get_nowait().event_id == first.event_id
    assert queue.get_nowait().event_id == second.event_id
