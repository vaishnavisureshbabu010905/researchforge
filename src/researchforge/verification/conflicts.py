"""Conflicting-evidence detection.

Links evidence that appears to disagree to the claims they relate to. This is a
lexical heuristic (negation + shared-subject overlap), not semantic entailment —
documented here rather than hidden, since it's a meaningful limitation (see
README.md#limitations).
"""

from __future__ import annotations

import re

from researchforge.models.claims import Claim
from researchforge.models.evidence import Evidence

_NEGATION_MARKERS = re.compile(
    r"\b(not|no|never|cannot|can't|isn't|doesn't|unlike|contrary|however|despite|fails? to)\b",
    re.IGNORECASE,
)


def _shares_subject(claim_text: str, evidence_text: str, *, min_overlap: int = 2) -> bool:
    claim_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", claim_text)}
    evidence_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", evidence_text)}
    return len(claim_words & evidence_words) >= min_overlap


def find_conflicts(claim: Claim, candidate_evidence: list[Evidence]) -> list[str]:
    """Return evidence_ids of candidate evidence that plausibly conflicts with `claim`."""
    conflicting: list[str] = []
    for ev in candidate_evidence:
        text = f"{ev.summary} {ev.extracted_content[:500]}"
        if not _shares_subject(claim.text, text):
            continue
        # A shared subject plus a negation marker in the evidence is our conflict
        # heuristic; refine with a real NLI model in a future iteration.
        if _NEGATION_MARKERS.search(text) and ev.evidence_id not in claim.supporting_evidence_ids:
            conflicting.append(ev.evidence_id)
    return conflicting
