"""Explainable source credibility scoring.

See docs/ARCHITECTURE.md#credibility for the signal table this implements.
Every call returns both a score and the reasons behind it — CLAUDE.md forbids
exposing a bare, unexplained number.
"""

from __future__ import annotations

from datetime import UTC, datetime
from fnmatch import fnmatch

from researchforge.config.settings import DOMAIN_REPUTATION
from researchforge.models.evidence import CredibilityAssessment, Evidence
from researchforge.models.sources import SourceType

_SOURCE_TYPE_SCORE = {
    SourceType.PRIMARY_DOCUMENTATION: 30,
    SourceType.ACADEMIC_PAPER: 28,
    SourceType.CODE_REPOSITORY: 24,
    SourceType.NEWS_ARTICLE: 18,
    SourceType.ENGINEERING_BLOG: 16,
    SourceType.FORUM_DISCUSSION: 8,
    SourceType.GENERAL_WEB: 10,
    SourceType.UNKNOWN: 5,
}

_DOMAIN_TIER_SCORE = {3: 20, 2: 14, 1: 8, 0: 5}  # tier -> points; 0 = unlisted/neutral


def _domain_tier(domain: str) -> int:
    if domain in DOMAIN_REPUTATION:
        return DOMAIN_REPUTATION[domain]
    for pattern, tier in DOMAIN_REPUTATION.items():
        if "*" in pattern and fnmatch(domain, pattern):
            return tier
    return 0


def _recency_score(published_at: datetime | None) -> tuple[int, str]:
    if published_at is None:
        return 5, "no publication date available (partial recency credit)"
    age_days = (datetime.now(UTC) - published_at.replace(tzinfo=UTC)).days
    if age_days < 0:
        age_days = 0
    if age_days <= 180:
        return 15, "published within the last 6 months"
    if age_days <= 730:
        return 10, "published within the last 2 years"
    if age_days <= 1825:
        return 5, "published within the last 5 years"
    return 2, "published more than 5 years ago"


def score_credibility(
    evidence: Evidence,
    *,
    corroborating_domain_count: int = 0,
    is_primary_source: bool | None = None,
) -> CredibilityAssessment:
    """Compute an explainable 0-100 credibility score for one piece of evidence.

    `corroborating_domain_count` is the number of *other, distinct-domain* pieces
    of evidence making a similar claim — supplied by the evidence manager after
    it has assembled the full collection (a single piece of evidence cannot know
    its own corroboration in isolation).
    """
    reasons: list[str] = []

    type_score = _SOURCE_TYPE_SCORE.get(evidence.source_type, 5)
    reasons.append(f"source type '{evidence.source_type.value}' ({type_score}/30)")

    tier = _domain_tier(evidence.domain)
    domain_score = _DOMAIN_TIER_SCORE[tier]
    reasons.append(
        f"domain reputation tier {tier} for '{evidence.domain}' ({domain_score}/20)"
        if tier
        else f"domain '{evidence.domain}' not in reputation list, neutral ({domain_score}/20)"
    )

    recency_score, recency_reason = _recency_score(evidence.publication_date)
    reasons.append(f"{recency_reason} ({recency_score}/15)")

    corroboration_score = min(20, corroborating_domain_count * 7)
    if corroborating_domain_count:
        reasons.append(f"corroborated by {corroborating_domain_count} independent domain(s) ({corroboration_score}/20)")
    else:
        reasons.append("no independent corroboration found yet (0/20)")

    if is_primary_source is None:
        directness_score = 8
        reasons.append("directness not assessed, default partial credit (8/15)")
    elif is_primary_source:
        directness_score = 15
        reasons.append("appears to be a primary source (15/15)")
    else:
        directness_score = 5
        reasons.append("appears to be reporting about a source rather than the source itself (5/15)")

    total = type_score + domain_score + recency_score + corroboration_score + directness_score
    return CredibilityAssessment(score=min(100, total), reasons=reasons)
