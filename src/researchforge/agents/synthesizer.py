"""Synthesis Agent: produces the final narrative report sections from verified claims + evidence."""

from __future__ import annotations

from pydantic import BaseModel

from researchforge.agents.base import BaseAgent
from researchforge.models.claims import Claim, ClaimStatus
from researchforge.models.evidence import Evidence

_SYNTHESIS_PROMPT = """You are the Synthesis Agent for a deep-research system.

Research question: {query}

Verified claims (with status):
{claims_block}

Write an executive summary (2-4 sentences), a methodology paragraph describing how the
research was conducted, and a detailed analysis (3-6 sentences) that integrates the claims
above, explicitly noting where evidence conflicts or is thin. Do not invent facts beyond what
the claims and evidence support.
"""


class SynthesisDraft(BaseModel):
    executive_summary: str
    methodology: str
    detailed_analysis: str


class SynthesizerAgent(BaseAgent):
    role = "synthesizer"

    async def synthesize(self, *, query: str, claims: list[Claim], evidence: list[Evidence]) -> SynthesisDraft:
        claims_block = "\n".join(f"- [{c.status.value}] {c.text}" for c in claims) or "(no claims extracted)"
        prompt = _SYNTHESIS_PROMPT.format(query=query, claims_block=claims_block)
        draft, usage = await self.llm.generate_structured(
            prompt, model=self.model, output_model=SynthesisDraft, system="Write clearly, cite nothing you cannot support."
        )
        self.logger.info("synthesis_completed", tokens=usage.output_tokens, claim_count=len(claims))
        return draft

    def key_findings(self, claims: list[Claim], *, limit: int = 6) -> list[str]:
        supported = [c for c in claims if c.status == ClaimStatus.SUPPORTED]
        supported.sort(key=lambda c: c.confidence, reverse=True)
        return [c.text for c in supported[:limit]]

    def limitations(self, claims: list[Claim], evidence: list[Evidence]) -> list[str]:
        notes: list[str] = []
        unsupported = [c for c in claims if c.status == ClaimStatus.UNSUPPORTED]
        conflicting = [c for c in claims if c.status == ClaimStatus.CONFLICTING]
        if unsupported:
            notes.append(f"{len(unsupported)} claim(s) could not be substantiated with the evidence gathered.")
        if conflicting:
            notes.append(f"{len(conflicting)} claim(s) have directly conflicting evidence; see the Claims section.")
        domains = {e.domain for e in evidence}
        if len(domains) < 3:
            notes.append(f"Evidence draws from only {len(domains)} distinct domain(s), limiting source diversity.")
        return notes

    def confidence_assessment(self, claims: list[Claim]) -> str:
        if not claims:
            return "No claims were extracted, so confidence in this report is low."
        supported_ratio = sum(1 for c in claims if c.status == ClaimStatus.SUPPORTED) / len(claims)
        if supported_ratio >= 0.7:
            return f"High confidence: {supported_ratio:.0%} of extracted claims are well-supported by independent evidence."
        if supported_ratio >= 0.4:
            return f"Moderate confidence: {supported_ratio:.0%} of claims are well-supported; treat remaining claims cautiously."
        return f"Low confidence: only {supported_ratio:.0%} of claims are well-supported. Treat findings as preliminary."
