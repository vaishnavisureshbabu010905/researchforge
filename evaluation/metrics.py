"""Benchmark-level metrics, distinct from (but built on top of) the live
`researchforge.evaluation.evaluator` quality score used during a real research run.

These add a couple of metrics that only make sense in a benchmark context, where
we have a labeled expectation to check against (e.g. "did research actually touch
the expected domains?").
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    question_id: str
    category: str
    query: str
    mode: str
    status: str
    quality_overall: int
    evidence_coverage: int
    source_quality: int
    source_diversity: int
    claim_support: int
    citation_coverage: int
    contradiction_handling: int
    completeness: int
    relevance: int
    passed_min_quality: bool
    domain_coverage: float  # fraction of expected_domains actually touched
    duration_seconds: float
    error: str | None = None


def relevance_score(query: str, evidence_summaries: list[str]) -> int:
    """Cheap lexical-overlap proxy for 'is the collected evidence actually about
    the query'. Not a substitute for human judgment — see docs/EVALUATION.md
    limitations section.
    """
    import re

    query_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", query)}
    if not query_words or not evidence_summaries:
        return 0
    hits = 0
    for summary in evidence_summaries:
        summary_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", summary)}
        if query_words & summary_words:
            hits += 1
    return round(100 * hits / len(evidence_summaries))


def domain_coverage(expected_domains: list[str], touched_domains: set[str]) -> float:
    if not expected_domains:
        return 1.0
    covered = sum(1 for d in expected_domains if d in touched_domains)
    return round(covered / len(expected_domains), 2)


def summarize(results: list[BenchmarkResult]) -> dict:
    if not results:
        return {}
    n = len(results)

    def avg(key: str) -> float:
        return round(sum(getattr(r, key) for r in results) / n, 1)

    return {
        "count": n,
        "pass_rate": round(sum(1 for r in results if r.passed_min_quality) / n, 2),
        "avg_quality_overall": avg("quality_overall"),
        "avg_evidence_coverage": avg("evidence_coverage"),
        "avg_source_quality": avg("source_quality"),
        "avg_source_diversity": avg("source_diversity"),
        "avg_claim_support": avg("claim_support"),
        "avg_citation_coverage": avg("citation_coverage"),
        "avg_contradiction_handling": avg("contradiction_handling"),
        "avg_completeness": avg("completeness"),
        "avg_relevance": avg("relevance"),
        "avg_domain_coverage": avg("domain_coverage"),
        "errors": [r.question_id for r in results if r.error],
    }
