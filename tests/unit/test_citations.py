from __future__ import annotations

from researchforge.citations.validator import validate_citations
from researchforge.models.claims import Claim, ClaimStatus
from researchforge.models.evidence import Evidence


def _ev(evidence_id: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        title="t",
        url="https://example.com/1",
        domain="example.com",
        extracted_content="c",
        summary="s",
        research_task_id="t1",
    )


def test_valid_citations_score_100():
    ev = _ev("e1")
    claim = Claim(text="x", status=ClaimStatus.SUPPORTED, supporting_evidence_ids=["e1"], citation_ids=["e1"])
    result = validate_citations([claim], [ev])
    assert result.coverage_percent == 100.0
    assert result.invalid_citation_refs == []


def test_fabricated_citation_is_flagged():
    ev = _ev("e1")
    claim = Claim(text="x", status=ClaimStatus.SUPPORTED, citation_ids=["e_does_not_exist"])
    result = validate_citations([claim], [ev])
    assert result.coverage_percent < 100.0
    assert result.invalid_citation_refs


def test_unsupported_claims_are_not_required_to_have_citations():
    claim = Claim(text="x", status=ClaimStatus.UNSUPPORTED)
    result = validate_citations([claim], [])
    assert result.total_citations == 0
    assert result.coverage_percent == 100.0  # nothing to validate, not a false claim of full coverage


def test_supported_claim_with_no_citation_is_invalid():
    claim = Claim(text="x", status=ClaimStatus.SUPPORTED, citation_ids=[])
    result = validate_citations([claim], [])
    assert result.invalid_citation_refs
    assert result.coverage_percent == 0.0
