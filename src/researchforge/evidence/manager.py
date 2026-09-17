"""Evidence manager: normalization entry point + full pipeline (dedup -> score -> rank).

This is the module agents call to turn raw provider output into the trusted,
scored `Evidence` records everything downstream operates on.
"""

from __future__ import annotations

from urllib.parse import urlparse

from researchforge.evidence.credibility import score_credibility
from researchforge.evidence.deduplication import deduplicate
from researchforge.models.evidence import Evidence, EvidenceCollection
from researchforge.models.sources import ResearchDomain, SourceType
from researchforge.observability.logging import get_logger
from researchforge.providers.base import ScrapedPage, SearchResultItem

logger = get_logger(__name__)

_TECHNICAL_DOMAINS = {"github.com", "docs.python.org", "developer.mozilla.org", "stackoverflow.com"}
_ACADEMIC_DOMAINS = {"arxiv.org", "acm.org", "ieee.org", "nature.com", "*.edu"}
_PRIMARY_SOURCE_TYPES = {SourceType.PRIMARY_DOCUMENTATION, SourceType.ACADEMIC_PAPER, SourceType.CODE_REPOSITORY}


def classify_source_type(domain: str) -> SourceType:
    if domain in {"docs.python.org", "developer.mozilla.org"} or domain.endswith(".gov"):
        return SourceType.PRIMARY_DOCUMENTATION
    if domain == "arxiv.org" or domain.endswith(".edu") or domain in {"acm.org", "ieee.org", "nature.com"}:
        return SourceType.ACADEMIC_PAPER
    if domain == "github.com":
        return SourceType.CODE_REPOSITORY
    if domain in {"reuters.com", "techcrunch.com", "bbc.com"}:
        return SourceType.NEWS_ARTICLE
    if domain in {"medium.com"} or domain.startswith("engineering."):
        return SourceType.ENGINEERING_BLOG
    if domain in {"news.ycombinator.com", "reddit.com"} or "forum" in domain:
        return SourceType.FORUM_DISCUSSION
    return SourceType.GENERAL_WEB


def classify_research_domain(domain: str) -> ResearchDomain:
    if domain in _TECHNICAL_DOMAINS:
        return ResearchDomain.TECHNICAL
    if domain in _ACADEMIC_DOMAINS or domain.endswith(".edu"):
        return ResearchDomain.ACADEMIC
    return ResearchDomain.WEB


def normalize(
    *,
    result: SearchResultItem,
    page: ScrapedPage | None,
    research_task_id: str,
    relevance_score: float,
) -> Evidence:
    """Turn a raw search result (+ optional scraped page) into a normalized Evidence record."""
    domain = urlparse(str(result.url)).netloc.removeprefix("www.")
    source_type = classify_source_type(domain)
    content = page.content if page else result.snippet

    return Evidence(
        title=result.title,
        url=result.url,
        domain=domain,
        source_type=source_type,
        research_domain=classify_research_domain(domain),
        extracted_content=content,
        summary=result.snippet or content[:300],
        relevance_score=relevance_score,
        publication_date=result.published_at or (page.published_at if page else None),
        research_task_id=research_task_id,
    )


def build_collection(evidence: list[Evidence]) -> EvidenceCollection:
    """Run the full pipeline: dedup -> corroboration-aware credibility scoring -> collection stats."""
    deduped, exact_dupes, near_dupes = deduplicate(evidence)

    # Corroboration signal: for each item, count *other* items from a different
    # domain whose summaries are lexically similar (cheap proxy for "says the same
    # thing"), which feeds back into credibility scoring.
    from researchforge.evidence.deduplication import _jaccard, _shingles  # local import: internal helper reuse

    shingle_cache = {item.evidence_id: _shingles(item.summary) for item in deduped}
    for item in deduped:
        corroborators = 0
        for other in deduped:
            if other.evidence_id == item.evidence_id or other.domain == item.domain:
                continue
            if _jaccard(shingle_cache[item.evidence_id], shingle_cache[other.evidence_id]) > 0.2:
                corroborators += 1
        item.credibility = score_credibility(
            item,
            corroborating_domain_count=corroborators,
            is_primary_source=item.source_type in _PRIMARY_SOURCE_TYPES,
        )

    logger.info(
        "evidence_pipeline_completed",
        total_in=len(evidence),
        kept=len(deduped),
        exact_duplicates=exact_dupes,
        near_duplicates=near_dupes,
    )

    return EvidenceCollection(
        items=deduped,
        unique_domains=len({e.domain for e in deduped}),
        duplicate_count=exact_dupes,
        near_duplicate_count=near_dupes,
    )
