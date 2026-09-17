"""End-to-end orchestrator test: plan -> parallel research -> evidence -> claims
-> iteration -> synthesis -> citations -> quality, entirely on mock providers.
This is the test that proves the pipeline described in docs/ARCHITECTURE.md
actually runs, not just that each stage works in isolation.
"""

from __future__ import annotations

import pytest

from researchforge.config.settings import get_settings
from researchforge.models.research import ResearchJobStatus, ResearchMode
from researchforge.orchestration.orchestrator import Orchestrator, new_job
from researchforge.orchestration.state import ResearchState
from researchforge.providers.llm.mock import MockLLMProvider
from researchforge.providers.mock import MockSearchProvider


@pytest.mark.asyncio
async def test_quick_research_completes_end_to_end():
    settings = get_settings()
    orchestrator = Orchestrator(settings=settings, search=MockSearchProvider(), llm=MockLLMProvider())
    job = new_job("What are the trade-offs of microservices architecture?", mode=ResearchMode.QUICK)
    state = ResearchState(job=job)

    result_state = await orchestrator.run(state)

    assert result_state.job.status in (ResearchJobStatus.COMPLETED, ResearchJobStatus.PARTIAL)
    assert result_state.report is not None
    assert result_state.report.quality.overall >= 0
    assert result_state.evidence  # some evidence was actually collected
    assert any(e.event_type == "research_completed" for e in result_state.events)


@pytest.mark.asyncio
async def test_deep_research_produces_plan_and_report():
    settings = get_settings()
    orchestrator = Orchestrator(settings=settings, search=MockSearchProvider(), llm=MockLLMProvider())
    job = new_job("Compare approaches to building AI coding agents", mode=ResearchMode.DEEP)
    state = ResearchState(job=job)

    result_state = await orchestrator.run(state)

    assert result_state.job.plan is not None
    assert len(result_state.job.plan.tasks) > 0
    assert result_state.report is not None
    assert result_state.report.citation_validation.coverage_percent >= 0
    # Report markdown rendering should not blow up on a real, full report.
    markdown = result_state.report.to_markdown()
    assert "Executive Summary" in markdown
    assert "Sources" in markdown


@pytest.mark.asyncio
async def test_events_are_recorded_in_order():
    settings = get_settings()
    orchestrator = Orchestrator(settings=settings, search=MockSearchProvider(), llm=MockLLMProvider())
    job = new_job("Explain the CAP theorem", mode=ResearchMode.QUICK)
    state = ResearchState(job=job)

    result_state = await orchestrator.run(state)
    event_types = [e.event_type for e in result_state.events]

    assert event_types[0] == "research_started"
    assert "plan_created" in event_types
    assert event_types[-1] in ("research_completed", "research_failed")
