from __future__ import annotations

from researchforge.models.claims import Claim, ClaimStatus
from researchforge.models.evidence import CredibilityAssessment, Evidence
from researchforge.verification.confidence import assess


def _ev(evidence_id: str, domain: str, score: int) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        title="t",
        url=f"https://{domain}/1",
        domain=domain,
        extracted_content="c",
        summary="s",
        research_task_id="t1",
        credibility=CredibilityAssessment(score=score, reasons=["test"]),
    )


def test_claim_with_no_evidence_is_unsupported():
    claim = Claim(text="Some claim")
    result = assess(claim, {})
    assert result.status == ClaimStatus.UNSUPPORTED
    assert result.confidence == 0.0


def test_claim_supported_by_two_independent_domains():
    ev1 = _ev("e1", "a.com", 80)
    ev2 = _ev("e2", "b.com", 80)
    claim = Claim(text="claim", supporting_evidence_ids=["e1", "e2"])
    result = assess(claim, {"e1": ev1, "e2": ev2})
    assert result.status == ClaimStatus.SUPPORTED
    assert result.confidence > 0


def test_claim_with_single_source_is_partially_supported():
    ev1 = _ev("e1", "a.com", 80)
    claim = Claim(text="claim", supporting_evidence_ids=["e1"])
    result = assess(claim, {"e1": ev1})
    assert result.status == ClaimStatus.PARTIALLY_SUPPORTED


def test_claim_with_strong_conflict_is_conflicting():
    support = _ev("e1", "a.com", 40)
    conflict = _ev("e2", "b.com", 60)
    claim = Claim(text="claim", supporting_evidence_ids=["e1"], conflicting_evidence_ids=["e2"])
    result = assess(claim, {"e1": support, "e2": conflict})
    assert result.status == ClaimStatus.CONFLICTING


def test_claim_confidence_always_bounded():
    ev1 = _ev("e1", "a.com", 100)
    claim = Claim(text="claim", supporting_evidence_ids=["e1", "e1", "e1"])
    result = assess(claim, {"e1": ev1})
    assert 0.0 <= result.confidence <= 1.0
