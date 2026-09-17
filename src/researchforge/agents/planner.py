"""Research Planner agent: decomposes a query into a typed ResearchPlan."""

from __future__ import annotations

from researchforge.agents.base import BaseAgent
from researchforge.models.research import ResearchPlan, ResearchTask
from researchforge.models.sources import ResearchDomain

_DOMAIN_KEYWORDS = {
    ResearchDomain.TECHNICAL: ("implement", "architecture", "code", "library", "framework", "benchmark", "api", "agent"),
    ResearchDomain.ACADEMIC: ("research", "study", "theory", "evidence", "scientific", "paper", "mechanism"),
}


def _infer_domain(subquestion: str) -> ResearchDomain:
    lowered = subquestion.lower()
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            return domain
    return ResearchDomain.WEB


PLANNER_PROMPT = """You are the Research Planner for a deep-research system.

Research question: {query}

Produce a research plan: a clear objective restating the question, and a list of 2-5
non-redundant subquestions that together would let a thorough researcher answer it. Each
subquestion should be independently researchable (so it can run in parallel) and should not
duplicate another subquestion's scope.
"""


class PlannerAgent(BaseAgent):
    role = "planner"

    async def plan(self, query: str, *, max_tasks: int) -> ResearchPlan:
        prompt = PLANNER_PROMPT.format(query=query)
        draft, usage = await self.llm.generate_structured(
            prompt, model=self.model, output_model=ResearchPlan, system="You are a meticulous research planner."
        )
        self.logger.info("plan_created", subquestion_count=len(draft.subquestions), tokens=usage.output_tokens)

        tasks: list[ResearchTask] = []
        domains: set[ResearchDomain] = set()
        for sq in draft.subquestions[:max_tasks]:
            domain = _infer_domain(sq)
            domains.add(domain)
            tasks.append(ResearchTask(subquestion=sq, domain=domain, priority=0.7))

        return draft.model_copy(update={"objective": draft.objective, "tasks": tasks, "required_domains": list(domains)})

    async def plan_followup(
        self, query: str, gaps: list[str], *, max_tasks: int, iteration: int
    ) -> list[ResearchTask]:
        """Build follow-up tasks directly from identified gaps — no LLM call needed since the
        gaps themselves (unsupported claims / missing coverage) are already concrete questions.
        """
        tasks = []
        for gap in gaps[:max_tasks]:
            domain = _infer_domain(gap)
            tasks.append(
                ResearchTask(
                    subquestion=f"Find stronger evidence for: {gap}",
                    domain=domain,
                    priority=0.9,
                    iteration=iteration,
                )
            )
        self.logger.info("followup_tasks_created", iteration=iteration, count=len(tasks))
        return tasks
