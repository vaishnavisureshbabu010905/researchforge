from __future__ import annotations

import pytest

from researchforge.agents.planner import PlannerAgent
from researchforge.providers.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_planner_produces_bounded_subquestions(mock_llm: MockLLMProvider):
    planner = PlannerAgent(llm=mock_llm, model="mock-reasoning")
    plan = await planner.plan("Compare approaches to building AI coding agents", max_tasks=3)

    assert plan.objective
    assert 1 <= len(plan.tasks) <= 3
    assert all(t.subquestion for t in plan.tasks)


@pytest.mark.asyncio
async def test_planner_is_deterministic(mock_llm: MockLLMProvider):
    planner = PlannerAgent(llm=mock_llm, model="mock-reasoning")
    plan_a = await planner.plan("Explain quantum error correction", max_tasks=4)
    plan_b = await planner.plan("Explain quantum error correction", max_tasks=4)
    assert plan_a.subquestions == plan_b.subquestions


@pytest.mark.asyncio
async def test_followup_tasks_are_generated_from_gaps(mock_llm: MockLLMProvider):
    planner = PlannerAgent(llm=mock_llm, model="mock-reasoning")
    tasks = await planner.plan_followup(
        "some query", ["claim A needs more evidence", "claim B needs more evidence"], max_tasks=5, iteration=2
    )
    assert len(tasks) == 2
    assert all(t.iteration == 2 for t in tasks)
