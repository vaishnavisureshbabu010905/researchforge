from __future__ import annotations

from researchforge.evaluation.evaluator import evaluate
from researchforge.models.claims import Claim, ClaimStatus
from researchforge.models.evidence import CredibilityAssessment, Evidence
from researchforge.models.reports import CitationValidation
from researchforge.orchestration.modes import get_mode_config
from researchforge.models.research import ResearchMode


def _ev(domain: str, score: int = 80) -> Evidence:
    return Evidence(
        title="t",
        url=f"https://{domain}/1",
        domain=domain,
        extracted_content="c",
        summary="s",
        research_task_id="t1",
        credibility=CredibilityAssessment(score=score, reasons=["x"]),
    )


def test_empty_research_scores_zero():
    mode_config = get_mode_config(ResearchMode.DEEP)
    citation = CitationValidation(total_citations=0, valid_citations=0, coverage_percent=100.0)
    result = evaluate(claims=[], evidence=[], citation_validation=citation, subquestions=[], mode_config=mode_config, iteration=1)
    assert result.overall == 0
    assert result.claim_support == 0


def test_well_supported_research_scores_highly():
    evidence = [_ev("a.com"), _ev("b.com"), _ev("c.com"), _ev("d.com")]
    claims = [
        Claim(
            text="x",
            status=ClaimStatus.SUPPORTED,
            confidence=0.9,
            supporting_evidence_ids=["e1"],
            citation_ids=["e1"],
            research_task_id="t1",
        )
    ]
    citation = CitationValidation(total_citations=1, valid_citations=1, coverage_percent=100.0)
    mode_config = get_mode_config(ResearchMode.DEEP)
    result = evaluate(
        claims=claims,
        evidence=evidence,
        citation_validation=citation,
        subquestions=["q1"],
        mode_config=mode_config,
        iteration=1,
    )
    assert result.overall > 60
    assert result.citation_coverage == 100


def test_low_quality_recommends_another_iteration_when_budget_remains():
    mode_config = get_mode_config(ResearchMode.DEEP)
    citation = CitationValidation(total_citations=0, valid_citations=0, coverage_percent=0.0)
    result = evaluate(claims=[], evidence=[], citation_validation=citation, subquestions=["q1"], mode_config=mode_config, iteration=1)
    assert result.recommend_another_iteration is True


def test_low_quality_does_not_recommend_iteration_past_max():
    mode_config = get_mode_config(ResearchMode.DEEP)
    citation = CitationValidation(total_citations=0, valid_citations=0, coverage_percent=0.0)
    result = evaluate(
        claims=[],
        evidence=[],
        citation_validation=citation,
        subquestions=["q1"],
        mode_config=mode_config,
        iteration=mode_config.max_iterations,
    )
    assert result.recommend_another_iteration is False
