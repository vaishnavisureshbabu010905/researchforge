"""Research quality evaluator: the live 0-100 scorer used by the orchestrator to
decide whether another research iteration is warranted.

Not to be confused with `evaluation/` at the repository root, which benchmarks
ResearchForge itself offline against a labeled dataset (see evaluation/README.md).
"""

from __future__ import annotations

from datetime import UTC

from researchforge.models.claims import Claim, ClaimStatus
from researchforge.models.evidence import Evidence
from researchforge.models.reports import CitationValidation, QualityBreakdown
from researchforge.models.research import ResearchModeConfig


def _evidence_coverage(claims: list[Claim]) -> int:
    if not claims:
        return 0
    with_support = sum(1 for c in claims if c.supporting_evidence_ids)
    return round(100 * with_support / len(claims))


def _source_quality(evidence: list[Evidence]) -> int:
    if not evidence:
        return 0
    return round(sum(e.credibility.score for e in evidence) / len(evidence))


def _source_diversity(evidence: list[Evidence]) -> int:
    if not evidence:
        return 0
    domains = {e.domain for e in evidence}
    # diminishing returns curve: 1 domain -> low score, 6+ distinct domains -> full score
    ratio = min(1.0, len(domains) / 6)
    return round(100 * ratio)


def _claim_support(claims: list[Claim]) -> int:
    if not claims:
        return 0
    weights = {
        ClaimStatus.SUPPORTED: 1.0,
        ClaimStatus.PARTIALLY_SUPPORTED: 0.6,
        ClaimStatus.CONFLICTING: 0.3,
        ClaimStatus.UNSUPPORTED: 0.0,
    }
    return round(100 * sum(weights[c.status] for c in claims) / len(claims))


def _contradiction_handling(claims: list[Claim]) -> int:
    conflicting = [c for c in claims if c.status == ClaimStatus.CONFLICTING]
    if not conflicting:
        return 100  # nothing to handle badly
    # Credit for *detecting* conflicts rather than hiding them; penalize only if
    # a conflicting claim has zero conflicting evidence attached (i.e. mislabeled).
    well_documented = sum(1 for c in conflicting if c.conflicting_evidence_ids)
    return round(100 * well_documented / len(conflicting))


def _completeness(claims: list[Claim], subquestions: list[str]) -> int:
    if not subquestions:
        return 100 if claims else 0
    covered_tasks = {c.research_task_id for c in claims if c.research_task_id}
    ratio = min(1.0, len(covered_tasks) / max(1, len(subquestions)))
    return round(100 * ratio)


def _freshness(evidence: list[Evidence]) -> int:
    if not evidence:
        return 0
    from datetime import datetime

    now = datetime.now(UTC)
    scores = []
    for e in evidence:
        if e.publication_date is None:
            scores.append(50)
            continue
        age_days = (now - e.publication_date.replace(tzinfo=UTC)).days
        scores.append(100 if age_days <= 365 else max(10, 100 - age_days // 20))
    return round(sum(scores) / len(scores))


def evaluate(
    *,
    claims: list[Claim],
    evidence: list[Evidence],
    citation_validation: CitationValidation,
    subquestions: list[str],
    mode_config: ResearchModeConfig,
    iteration: int,
) -> QualityBreakdown:
    if not evidence and not claims:
        return QualityBreakdown(
            overall=0,
            evidence_coverage=0,
            source_quality=0,
            source_diversity=0,
            claim_support=0,
            citation_coverage=0
            if citation_validation.total_citations == 0
            else round(citation_validation.coverage_percent),
            contradiction_handling=0,
            completeness=0,
            freshness=0,
            recommend_another_iteration=bool(subquestions) and iteration < mode_config.max_iterations,
            notes=["No evidence or claims were produced; quality metrics are not applicable."],
        )

    evidence_coverage = _evidence_coverage(claims)
    source_quality = _source_quality(evidence)
    source_diversity = _source_diversity(evidence)
    claim_support = _claim_support(claims)
    citation_coverage = round(citation_validation.coverage_percent)
    contradiction_handling = _contradiction_handling(claims)
    completeness = _completeness(claims, subquestions)
    freshness = _freshness(evidence)

    weights = {
        "evidence_coverage": 0.15,
        "source_quality": 0.15,
        "source_diversity": 0.10,
        "claim_support": 0.25,
        "citation_coverage": 0.15,
        "contradiction_handling": 0.10,
        "completeness": 0.05,
        "freshness": 0.05,
    }
    values = {
        "evidence_coverage": evidence_coverage,
        "source_quality": source_quality,
        "source_diversity": source_diversity,
        "claim_support": claim_support,
        "citation_coverage": citation_coverage,
        "contradiction_handling": contradiction_handling,
        "completeness": completeness,
        "freshness": freshness,
    }
    overall = round(sum(values[k] * weights[k] for k in weights))

    notes: list[str] = []
    recommend_more = False
    if overall < mode_config.quality_threshold and iteration < mode_config.max_iterations:
        recommend_more = True
        notes.append(
            f"Overall score {overall} is below the {mode_config.mode.value} mode threshold "
            f"of {mode_config.quality_threshold}; iteration {iteration}/{mode_config.max_iterations} used."
        )
    elif overall < mode_config.quality_threshold:
        notes.append(
            f"Overall score {overall} is below threshold but the maximum of "
            f"{mode_config.max_iterations} iterations has been reached."
        )
    if source_diversity < 50:
        notes.append("Source diversity is low — findings rely heavily on a small number of domains.")
    if claim_support < 50:
        notes.append("Many claims lack strong evidentiary support.")

    return QualityBreakdown(
        overall=overall,
        evidence_coverage=evidence_coverage,
        source_quality=source_quality,
        source_diversity=source_diversity,
        claim_support=claim_support,
        citation_coverage=citation_coverage,
        contradiction_handling=contradiction_handling,
        completeness=completeness,
        freshness=freshness,
        recommend_another_iteration=recommend_more,
        notes=notes,
    )
