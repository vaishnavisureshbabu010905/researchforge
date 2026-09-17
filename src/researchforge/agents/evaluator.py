"""Quality Evaluator agent: thin wrapper over evaluation/evaluator.py.

Deliberately does not call an LLM — quality scoring must be deterministic and
reproducible (CLAUDE.md: "never expose a bare, unexplained number"), so this is
code, not a model's self-assessment of its own work.
"""

from __future__ import annotations

from researchforge.evaluation.evaluator import evaluate
from researchforge.models.claims import Claim
from researchforge.models.evidence import Evidence
from researchforge.models.reports import CitationValidation, QualityBreakdown
from researchforge.models.research import ResearchModeConfig
from researchforge.observability.logging import get_logger

logger = get_logger("researchforge.agents.evaluator")


class QualityEvaluatorAgent:
    role = "quality_evaluator"

    def score(
        self,
        *,
        claims: list[Claim],
        evidence: list[Evidence],
        citation_validation: CitationValidation,
        subquestions: list[str],
        mode_config: ResearchModeConfig,
        iteration: int,
    ) -> QualityBreakdown:
        result = evaluate(
            claims=claims,
            evidence=evidence,
            citation_validation=citation_validation,
            subquestions=subquestions,
            mode_config=mode_config,
            iteration=iteration,
        )
        logger.info("quality_scored", overall=result.overall, recommend_more=result.recommend_another_iteration)
        return result
