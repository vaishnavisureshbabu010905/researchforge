"""Standalone claim verification: POST /api/claims/verify.

Verifies an arbitrary claim either against a specific research job's existing
evidence pool (`research_id` provided) or by running a fresh, lightweight search
(shared logic with agents/researcher.py, kept here as a thin ad-hoc path rather
than routed through the full orchestrator/plan machinery).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from researchforge.api.dependencies import ResearchRegistry, get_registry
from researchforge.api.schemas import VerifyClaimRequest, VerifyClaimResponse
from researchforge.config.settings import Settings, get_settings
from researchforge.evidence.manager import build_collection, normalize
from researchforge.models.claims import Claim
from researchforge.observability.logging import get_logger
from researchforge.providers.factory import get_search_provider
from researchforge.storage.database import Database, get_database
from researchforge.storage.repositories import ResearchJobRepository
from researchforge.verification.conflicts import find_conflicts
from researchforge.verification.confidence import assess

logger = get_logger(__name__)
router = APIRouter(prefix="/api/claims", tags=["claims"])


@router.post("/verify", response_model=VerifyClaimResponse)
async def verify_claim(
    body: VerifyClaimRequest,
    registry: ResearchRegistry = Depends(get_registry),
    database: Database = Depends(get_database),
    settings: Settings = Depends(get_settings),
) -> VerifyClaimResponse:
    if body.research_id:
        live = registry.get_live_state(body.research_id)
        if live is not None:
            evidence = live.evidence
        else:
            async with database.session() as session:
                job = await ResearchJobRepository(session).get_job(body.research_id)
                if job is None:
                    raise HTTPException(status_code=404, detail=f"research job '{body.research_id}' not found")
                evidence = await ResearchJobRepository(session).get_evidence(body.research_id)
    else:
        # Ad-hoc verification: run a small fresh search scoped to the claim text.
        search = get_search_provider(settings)
        results = await search.search(body.claim_text, limit=5)
        raw_evidence = [
            normalize(result=r, page=None, research_task_id="ad_hoc", relevance_score=0.8) for r in results
        ]
        evidence = build_collection(raw_evidence).items

    claim = Claim(text=body.claim_text, research_task_id=None)
    conflicting_ids = find_conflicts(claim, evidence)

    # Link supporting evidence by the same lexical-overlap heuristic used during extraction.
    import re

    claim_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", body.claim_text)}
    supporting_ids = []
    for e in evidence:
        ev_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", f"{e.title} {e.summary}")}
        if len(claim_words & ev_words) >= 2 and e.evidence_id not in conflicting_ids:
            supporting_ids.append(e.evidence_id)

    claim = claim.model_copy(update={"supporting_evidence_ids": supporting_ids, "conflicting_evidence_ids": conflicting_ids})
    evidence_by_id = {e.evidence_id: e for e in evidence}
    result = assess(claim, evidence_by_id)

    logger.info("ad_hoc_claim_verified", status=result.status.value, evidence_considered=len(evidence))
    return VerifyClaimResponse(claim=result)
