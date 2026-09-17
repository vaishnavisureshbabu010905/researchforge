from __future__ import annotations

from researchforge.evidence.deduplication import deduplicate
from researchforge.models.evidence import Evidence


def _ev(title: str, url: str, domain: str, task_id: str = "t1", summary: str = "") -> Evidence:
    return Evidence(
        title=title,
        url=url,
        domain=domain,
        extracted_content=summary or title,
        summary=summary or title,
        research_task_id=task_id,
    )


def test_deduplicate_removes_exact_duplicates():
    items = [
        _ev("Same Title", "https://a.com/1", "a.com"),
        _ev("Same Title", "https://a.com/1-mirror", "a.com"),  # same domain + title -> exact dup
        _ev("Different Title", "https://b.com/1", "b.com"),
    ]
    kept, exact, near = deduplicate(items)
    assert len(kept) == 2
    assert exact == 1
    assert near == 0


def test_deduplicate_detects_near_duplicates():
    shared_summary = "The quick brown fox jumps over the lazy dog near the riverbank at dawn"
    items = [
        _ev("Article One", "https://a.com/1", "a.com", summary=shared_summary),
        _ev("Article One Mirror", "https://mirror.com/1", "mirror.com", summary=shared_summary),
    ]
    kept, exact, near = deduplicate(items)
    assert len(kept) == 1
    assert exact == 0
    assert near == 1


def test_deduplicate_keeps_genuinely_different_evidence():
    items = [
        _ev("Topic A analysis", "https://a.com/1", "a.com", summary="A detailed analysis of topic A trade-offs"),
        _ev("Topic B analysis", "https://b.com/1", "b.com", summary="A detailed analysis of topic B benchmarks"),
    ]
    kept, exact, near = deduplicate(items)
    assert len(kept) == 2
    assert exact == 0


def test_deduplicate_empty_input():
    kept, exact, near = deduplicate([])
    assert kept == []
    assert exact == 0 and near == 0
