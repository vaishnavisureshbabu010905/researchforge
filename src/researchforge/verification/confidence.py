"""Claim confidence + status calculation from supporting/conflicting evidence."""

from __future__ import annotations

from researchforge.models.claims import Claim, ClaimStatus
from researchforge.models.evidence import Evidence


def assess(claim: Claim, evidence_by_id: dict[str, Evidence]) -> Claim:
    """Return a copy of `claim` with `status` and `confidence` set from its evidence links."""
    supporting = [evidence_by_id[eid] for eid in claim.supporting_evidence_ids if eid in evidence_by_id]
    conflicting = [evidence_by_id[eid] for eid in claim.conflicting_evidence_ids if eid in evidence_by_id]

    if not supporting and not conflicting:
        return claim.model_copy(update={"status": ClaimStatus.UNSUPPORTED, "confidence": 0.0})

    support_weight = sum(e.credibility.score for e in supporting) / 100
    conflict_weight = sum(e.credibility.score for e in conflicting) / 100

    independent_support_domains = {e.domain for e in supporting}

    if conflicting and support_weight <= conflict_weight * 1.5:
        # Meaningful conflict that isn't heavily outweighed by stronger supporting evidence.
        status = ClaimStatus.CONFLICTING
        confidence = support_weight / (support_weight + conflict_weight + 1e-9)
    elif supporting and len(independent_support_domains) >= 2:
        status = ClaimStatus.SUPPORTED
        confidence = min(1.0, support_weight / max(1, len(supporting)))
    elif supporting:
        status = ClaimStatus.PARTIALLY_SUPPORTED
        confidence = min(0.7, support_weight / max(1, len(supporting)))
    else:
        status = ClaimStatus.UNSUPPORTED
        confidence = 0.0

    return claim.model_copy(update={"status": status, "confidence": round(confidence, 2)})
