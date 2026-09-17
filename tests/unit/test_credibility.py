from __future__ import annotations

from datetime import datetime, timedelta, timezone

from researchforge.evidence.credibility import score_credibility
from researchforge.models.evidence import Evidence
from researchforge.models.sources import SourceType


def _ev(**overrides) -> Evidence:
    defaults = dict(
        title="Title",
        url="https://example.com/1",
        domain="example.com",
        extracted_content="content",
        summary="summary",
        research_task_id="t1",
    )
    defaults.update(overrides)
    return Evidence(**defaults)


def test_primary_documentation_scores_higher_than_forum():
    doc = _ev(domain="docs.python.org", source_type=SourceType.PRIMARY_DOCUMENTATION)
    forum = _ev(domain="news.ycombinator.com", source_type=SourceType.FORUM_DISCUSSION)

    doc_score = score_credibility(doc, is_primary_source=True)
    forum_score = score_credibility(forum, is_primary_source=False)

    assert doc_score.score > forum_score.score
    assert doc_score.reasons  # always explainable
    assert forum_score.reasons


def test_recency_improves_score():
    old = _ev(publication_date=datetime.now(timezone.utc) - timedelta(days=3000))
    recent = _ev(publication_date=datetime.now(timezone.utc) - timedelta(days=10))

    old_score = score_credibility(old)
    recent_score = score_credibility(recent)

    assert recent_score.score >= old_score.score


def test_corroboration_increases_score_up_to_cap():
    ev = _ev()
    none = score_credibility(ev, corroborating_domain_count=0)
    some = score_credibility(ev, corroborating_domain_count=3)
    lots = score_credibility(ev, corroborating_domain_count=100)

    assert some.score > none.score
    assert lots.score <= 100


def test_score_is_always_in_bounds():
    ev = _ev(source_type=SourceType.PRIMARY_DOCUMENTATION, domain="arxiv.org")
    result = score_credibility(ev, corroborating_domain_count=10, is_primary_source=True)
    assert 0 <= result.score <= 100
