"""Claim extraction: turn a set of Evidence for a task into candidate Claim records."""

from __future__ import annotations

from pydantic import BaseModel

from researchforge.models.claims import Claim, ClaimKind
from researchforge.models.evidence import Evidence
from researchforge.observability.logging import get_logger
from researchforge.providers.llm.base import LLMProvider

logger = get_logger(__name__)


class ExtractedClaimsDraft(BaseModel):
    """Internal LLM I/O contract for claim extraction (not part of the public domain model)."""

    claims: list[str]


_EXTRACTION_PROMPT = """You are extracting the most important, checkable factual claims from
research evidence about the following research task.

Research question: {question}

Evidence:
{evidence_block}

List the 2-5 most important, specific, checkable factual claims that can be assessed against
this evidence. Avoid vague statements. One claim per line of the `claims` field.
"""


def _evidence_block(evidence: list[Evidence]) -> str:
    lines = []
    for e in evidence[:8]:  # cap prompt size
        lines.append(f"- [{e.domain}] {e.title}: {e.summary}")
    return "\n".join(lines)


async def extract_claims(
    *,
    question: str,
    evidence: list[Evidence],
    task_id: str,
    llm: LLMProvider,
    model: str,
) -> list[Claim]:
    """Extract candidate claims for a research task and link them to supporting evidence
    by simple lexical relevance (see verification/conflicts.py for the conflict side).
    """
    if not evidence:
        return []

    prompt = _EXTRACTION_PROMPT.format(question=question, evidence_block=_evidence_block(evidence))
    draft, usage = await llm.generate_structured(
        prompt, model=model, output_model=ExtractedClaimsDraft, system="Extract only checkable factual claims."
    )
    logger.info("claims_extracted", task_id=task_id, count=len(draft.claims), tokens=usage.output_tokens)

    claims: list[Claim] = []
    for text in draft.claims:
        supporting = _link_supporting_evidence(text, evidence)
        claims.append(
            Claim(
                text=text,
                kind=ClaimKind.FACT,
                importance=0.5,
                supporting_evidence_ids=[e.evidence_id for e in supporting],
                research_task_id=task_id,
            )
        )
    return claims


def _link_supporting_evidence(claim_text: str, evidence: list[Evidence], *, min_overlap: int = 2) -> list[Evidence]:
    import re

    claim_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", claim_text)}
    linked = []
    for e in evidence:
        ev_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", f"{e.title} {e.summary}")}
        if len(claim_words & ev_words) >= min_overlap:
            linked.append(e)
    return linked
