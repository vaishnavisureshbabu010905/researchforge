"""Evidence ranking: combine relevance and credibility, and enforce diversity."""

from __future__ import annotations

from researchforge.models.evidence import Evidence

_RELEVANCE_WEIGHT = 0.6
_CREDIBILITY_WEIGHT = 0.4


def score(evidence: Evidence) -> float:
    return _RELEVANCE_WEIGHT * evidence.relevance_score + _CREDIBILITY_WEIGHT * (evidence.credibility.score / 100)


def rank(evidence: list[Evidence]) -> list[Evidence]:
    return sorted(evidence, key=score, reverse=True)


def diversify(evidence: list[Evidence], *, max_per_domain: int = 3) -> list[Evidence]:
    """Cap how many items from a single domain survive into the "top" set, so a
    report doesn't lean entirely on one prolific domain even if it's highly ranked.
    """
    counts: dict[str, int] = {}
    result: list[Evidence] = []
    for item in rank(evidence):
        counts.setdefault(item.domain, 0)
        if counts[item.domain] >= max_per_domain:
            continue
        counts[item.domain] += 1
        result.append(item)
    return result
