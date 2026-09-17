"""Citation validation.

A "citation" in a synthesized report is a reference to an `Evidence.evidence_id`.
This module checks that every citation actually resolves to evidence that was
retrieved for this job, and that each claim marked SUPPORTED/PARTIALLY_SUPPORTED
carries at least one such citation — see report_generation spec: "never fabricate
citations."
"""

from __future__ import annotations

from researchforge.models.claims import Claim, ClaimStatus
from researchforge.models.evidence import Evidence
from researchforge.models.reports import CitationValidation


def validate_citations(claims: list[Claim], evidence: list[Evidence]) -> CitationValidation:
    known_ids = {e.evidence_id for e in evidence}

    total = 0
    valid = 0
    invalid_refs: list[str] = []

    claims_needing_citations = [
        c for c in claims if c.status in (ClaimStatus.SUPPORTED, ClaimStatus.PARTIALLY_SUPPORTED)
    ]

    for claim in claims_needing_citations:
        cited_ids = claim.citation_ids or claim.supporting_evidence_ids
        if not cited_ids:
            total += 1
            invalid_refs.append(f"{claim.claim_id}: no citation for a supported claim")
            continue
        for cid in cited_ids:
            total += 1
            if cid in known_ids:
                valid += 1
            else:
                invalid_refs.append(f"{claim.claim_id}: citation '{cid}' does not match any retrieved evidence")

    coverage = 100.0 if total == 0 else round(100 * valid / total, 1)
    return CitationValidation(
        total_citations=total, valid_citations=valid, invalid_citation_refs=invalid_refs, coverage_percent=coverage
    )
