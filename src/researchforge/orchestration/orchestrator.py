"""Research Orchestrator: the single place that owns a research job's lifecycle.

This is what api/routes and mcp/tools both call into — neither contains research
logic (see docs/ARCHITECTURE.md "layers and boundaries").
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from researchforge.agents.academic_researcher import AcademicResearchAgent
from researchforge.agents.evaluator import QualityEvaluatorAgent
from researchforge.agents.fact_checker import FactCheckerAgent
from researchforge.agents.planner import PlannerAgent
from researchforge.agents.synthesizer import SynthesizerAgent
from researchforge.agents.technical_researcher import TechnicalResearchAgent
from researchforge.agents.web_researcher import WebResearchAgent
from researchforge.citations.validator import validate_citations
from researchforge.config.settings import Settings
from researchforge.evidence.manager import build_collection
from researchforge.evidence.ranking import diversify
from researchforge.models.claims import Claim
from researchforge.models.evidence import Evidence
from researchforge.models.reports import ResearchReport
from researchforge.models.research import ResearchJob, ResearchJobStatus, ResearchMode, ResearchTask
from researchforge.models.sources import ResearchDomain
from researchforge.observability.logging import get_logger
from researchforge.orchestration.execution import run_tasks
from researchforge.orchestration.modes import get_mode_config
from researchforge.orchestration.state import ResearchState
from researchforge.providers.base import SearchProvider
from researchforge.providers.llm.base import LLMProvider
from researchforge.verification.fact_checker import unsupported_important_claims

logger = get_logger(__name__)

_DOMAIN_AGENTS = {
    ResearchDomain.WEB: WebResearchAgent,
    ResearchDomain.TECHNICAL: TechnicalResearchAgent,
    ResearchDomain.ACADEMIC: AcademicResearchAgent,
}


class Orchestrator:
    """Stateless coordinator: holds providers + settings, operates on a `ResearchState`
    passed in per job. Job state itself lives in the caller-owned registry
    (see api/dependencies.py::ResearchRegistry) so multiple jobs can run concurrently.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        search: SearchProvider,
        llm: LLMProvider,
        checkpoint: Callable[[ResearchState], Awaitable[None]] | None = None,
    ) -> None:
        self.settings = settings
        self.search = search
        self.llm = llm
        self.planner = PlannerAgent(llm=llm, model=settings.planner_model)
        self.fact_checker = FactCheckerAgent(llm=llm, model=settings.fact_check_model)
        self.synthesizer = SynthesizerAgent(llm=llm, model=settings.synthesis_model)
        self.evaluator = QualityEvaluatorAgent()
        self._checkpoint = checkpoint

    async def _save_checkpoint(self, state: ResearchState) -> None:
        if self._checkpoint is not None:
            await self._checkpoint(state)

    def _researcher_for(self, domain: ResearchDomain):
        agent_cls = _DOMAIN_AGENTS[domain]
        return agent_cls(llm=self.llm, search=self.search, model=self.settings.extraction_model)

    async def run(self, state: ResearchState) -> ResearchState:
        job = state.job
        mode_config = get_mode_config(job.mode)
        state.emit("research_started", f"Starting {job.mode.value} research", query=job.query)

        try:
            state.set_status(ResearchJobStatus.PLANNING)
            plan = await self.planner.plan(job.query, max_tasks=mode_config.max_tasks)
            job.plan = plan
            state.emit("plan_created", "Research plan created", subquestions=plan.subquestions)
            await self._save_checkpoint(state)

            pending_tasks = plan.tasks
            iteration = 0
            had_task_failure = False

            while pending_tasks and iteration < mode_config.max_iterations:
                iteration += 1
                job.iteration_count = iteration
                state.set_status(ResearchJobStatus.RESEARCHING if iteration == 1 else ResearchJobStatus.ITERATING)
                state.emit("research_iteration_started", f"Iteration {iteration}", task_count=len(pending_tasks))

                new_evidence = await self._research_tasks(state, pending_tasks, mode_config)
                had_task_failure = had_task_failure or any(t.status.value == "failed" for t in pending_tasks)
                state.evidence.extend(new_evidence)

                state.set_status(ResearchJobStatus.ANALYZING)
                collection = build_collection(state.evidence)
                state.evidence = collection.items
                state.emit(
                    "evidence_added",
                    "Evidence collected and scored",
                    count=len(collection.items),
                    unique_domains=collection.unique_domains,
                    duplicates_removed=collection.duplicate_count + collection.near_duplicate_count,
                )
                await self._save_checkpoint(state)

                new_claims = await self._verify_tasks(state, pending_tasks, mode_config)
                state.claims = _merge_claims(state.claims, new_claims)
                for c in new_claims:
                    state.emit("claim_extracted", c.text, claim_id=c.claim_id, status=c.status.value)
                    if c.status.value == "conflicting":
                        state.emit("research_gap_detected", f"Conflict found: {c.text}", claim_id=c.claim_id)

                gaps = unsupported_important_claims(state.claims)
                await self._save_checkpoint(state)

                if not gaps or iteration >= mode_config.max_iterations:
                    break

                state.emit("research_gap_detected", f"{len(gaps)} claim(s) need stronger evidence")
                pending_tasks = await self.planner.plan_followup(
                    job.query, [g.text for g in gaps], max_tasks=mode_config.max_tasks, iteration=iteration
                )

            failed_tasks = [t for t in pending_tasks if t.status.value == "failed"]
            if failed_tasks and not state.evidence:
                job.error = f"All research tasks failed ({len(failed_tasks)}/{len(pending_tasks)})"
                state.set_status(ResearchJobStatus.FAILED)
                state.emit("research_failed", job.error)
                await self._save_checkpoint(state)
                return state

            report = await self._synthesize(state, mode_config)
            state.report = report
            final_status = ResearchJobStatus.PARTIAL if had_task_failure else ResearchJobStatus.COMPLETED
            state.set_status(final_status)
            job.completed_at = report.generated_at
            event_type = "research_partial" if final_status == ResearchJobStatus.PARTIAL else "research_completed"
            message = "Research completed with partial task failures" if final_status == ResearchJobStatus.PARTIAL else "Research completed"
            state.emit(event_type, message, quality=report.quality.overall)
            await self._save_checkpoint(state)

        except Exception as exc:  # noqa: BLE001 - top-level guard: a failed job must not crash the process
            logger.error("research_job_failed", research_id=job.research_id, error=str(exc))
            job.error = str(exc)
            state.set_status(ResearchJobStatus.FAILED)
            state.emit("research_failed", str(exc))
            await self._save_checkpoint(state)

        return state

    async def _research_tasks(
        self, state: ResearchState, tasks: list[ResearchTask], mode_config
    ) -> list[Evidence]:
        from researchforge.models.research import TaskStatus

        items = []
        for task in tasks:
            task.status = TaskStatus.RUNNING
            state.emit("task_started", task.subquestion, task_id=task.task_id, domain=task.domain.value)
            agent = self._researcher_for(task.domain)
            items.append(
                (task.task_id, lambda t=task, a=agent: a.research(t.subquestion, task_id=t.task_id, min_results=mode_config.min_evidence_per_task))
            )

        outcomes = await run_tasks(
            items,
            max_parallelism=mode_config.max_parallelism,
            timeout_seconds=mode_config.task_timeout_seconds,
            max_retries=self.settings.provider_max_retries,
            backoff_seconds=self.settings.provider_retry_backoff_seconds,
        )

        evidence: list[Evidence] = []
        by_id = {t.task_id: t for t in tasks}
        for outcome in outcomes:
            task = by_id[outcome.task_id]
            if outcome.success and outcome.result:
                task.status = TaskStatus.COMPLETED
                evidence.extend(outcome.result)
                for e in outcome.result:
                    state.emit("source_found", e.title, task_id=task.task_id, url=str(e.url))
            else:
                task.status = TaskStatus.FAILED
                task.error = outcome.error
                state.emit("task_failed", f"Task failed: {outcome.error}", task_id=task.task_id)
                logger.warning("research_task_failed", task_id=task.task_id, error=outcome.error)
        return evidence

    async def _verify_tasks(self, state: ResearchState, tasks: list[ResearchTask], mode_config) -> list[Claim]:
        all_evidence = state.evidence
        results: list[Claim] = []
        for task in tasks:
            task_evidence = [e for e in all_evidence if e.research_task_id == task.task_id]
            if not task_evidence:
                continue
            claims = await self.fact_checker.extract_and_verify(
                question=task.subquestion, task_evidence=task_evidence, task_id=task.task_id, all_evidence=all_evidence
            )
            results.extend(claims)
        return results

    async def _synthesize(self, state: ResearchState, mode_config) -> ResearchReport:
        job = state.job
        state.set_status(ResearchJobStatus.SYNTHESIZING)
        state.emit("synthesis_started", "Synthesizing final report")

        top_evidence = diversify(state.evidence, max_per_domain=4)
        draft = await self.synthesizer.synthesize(query=job.query, claims=state.claims, evidence=top_evidence)

        for claim in state.claims:
            if not claim.citation_ids:
                claim.citation_ids = claim.supporting_evidence_ids

        state.set_status(ResearchJobStatus.VALIDATING)
        citation_validation = validate_citations(state.claims, state.evidence)
        state.emit("citation_validation", "Citations validated", coverage=citation_validation.coverage_percent)

        subquestions = job.plan.subquestions if job.plan else []
        quality = self.evaluator.score(
            claims=state.claims,
            evidence=state.evidence,
            citation_validation=citation_validation,
            subquestions=subquestions,
            mode_config=mode_config,
            iteration=job.iteration_count,
        )
        state.emit("quality_evaluation", "Quality scored", overall=quality.overall)

        return ResearchReport(
            research_id=job.research_id,
            query=job.query,
            executive_summary=draft.executive_summary,
            methodology=draft.methodology,
            key_findings=self.synthesizer.key_findings(state.claims),
            detailed_analysis=draft.detailed_analysis,
            limitations=self.synthesizer.limitations(state.claims, state.evidence),
            confidence_assessment=self.synthesizer.confidence_assessment(state.claims),
            claims=state.claims,
            evidence=state.evidence,
            citation_validation=citation_validation,
            quality=quality,
        )


def _merge_claims(existing: list[Claim], new: list[Claim]) -> list[Claim]:
    by_id = {c.claim_id: c for c in existing}
    for c in new:
        by_id[c.claim_id] = c
    return list(by_id.values())


def new_job(query: str, mode: ResearchMode = ResearchMode.DEEP) -> ResearchJob:
    return ResearchJob(query=query, mode=mode)
