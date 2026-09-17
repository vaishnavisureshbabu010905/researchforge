"""Fact-checking pipeline: assemble supporting/conflicting evidence and assess each claim.

This is the module that makes ResearchForge's "fact checker" agent (agents/fact_checker.py)
more than a prompt — the actual status/confidence assignment is deterministic code
(verification/confidence.py), not an LLM's opinion of itself.
"""

from __future__ import annotations

from researchforge.models.claims import Claim
from researchforge.models.evidence import Evidence
from researchforge.observability.logging import get_logger
from researchforge.verification.confidence import assess
from researchforge.verification.conflicts import find_conflicts

logger = get_logger(__name__)


def verify_claims(claims: list[Claim], evidence: list[Evidence]) -> list[Claim]:
    """Run the full verification pass over a batch of claims against the full evidence pool
    (not just the evidence gathered for the claim's originating task) so corroboration and
    conflicts can be found across the entire research job.
    """
    evidence_by_id = {e.evidence_id: e for e in evidence}
    verified: list[Claim] = []

    for claim in claims:
        conflicting_ids = find_conflicts(claim, evidence)
        working = claim.model_copy(update={"conflicting_evidence_ids": conflicting_ids})
        result = assess(working, evidence_by_id)
        verified.append(result)

        if result.status.value == "conflicting":
            logger.warning(
                "claim_conflict_detected",
                claim_id=result.claim_id,
                supporting=len(result.supporting_evidence_ids),
                conflicting=len(result.conflicting_evidence_ids),
            )

    return verified


def unsupported_important_claims(claims: list[Claim], *, importance_threshold: float = 0.5) -> list[Claim]:
    """Claims worth flagging as research gaps: important but not well supported."""
    return [
        c
        for c in claims
        if c.importance >= importance_threshold and c.status.value in {"unsupported", "partially_supported"}
    ]
