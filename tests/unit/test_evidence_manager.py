from __future__ import annotations

from researchforge.evidence.manager import build_collection, classify_research_domain, classify_source_type, normalize
from researchforge.models.sources import ResearchDomain, SourceType
from researchforge.providers.base import SearchResultItem


def test_classify_source_type_known_domains():
    assert classify_source_type("docs.python.org") == SourceType.PRIMARY_DOCUMENTATION
    assert classify_source_type("arxiv.org") == SourceType.ACADEMIC_PAPER
    assert classify_source_type("github.com") == SourceType.CODE_REPOSITORY
    assert classify_source_type("some-random-blog.net") == SourceType.GENERAL_WEB


def test_classify_research_domain():
    assert classify_research_domain("github.com") == ResearchDomain.TECHNICAL
    assert classify_research_domain("arxiv.org") == ResearchDomain.ACADEMIC
    assert classify_research_domain("news.ycombinator.com") == ResearchDomain.WEB


def test_normalize_produces_valid_evidence():
    result = SearchResultItem(title="A Title", url="https://arxiv.org/abs/1234", snippet="A snippet")
    evidence = normalize(result=result, page=None, research_task_id="t1", relevance_score=0.9)
    assert evidence.domain == "arxiv.org"
    assert evidence.source_type == SourceType.ACADEMIC_PAPER
    assert evidence.research_task_id == "t1"


def test_build_collection_scores_and_dedupes():
    results = [
        SearchResultItem(title="Same", url="https://a.com/1", snippet="s"),
        SearchResultItem(title="Same", url="https://a.com/1-dup", snippet="s"),
    ]
    evidence = [normalize(result=r, page=None, research_task_id="t1", relevance_score=0.5) for r in results]
    collection = build_collection(evidence)
    assert len(collection.items) == 1
    assert all(0 <= e.credibility.score <= 100 for e in collection.items)
    assert collection.duplicate_count == 1


def test_build_collection_empty_input():
    collection = build_collection([])
    assert collection.items == []
    assert collection.unique_domains == 0
