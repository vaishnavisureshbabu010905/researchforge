"""Fact Checker agent: extracts claims per task, then verifies them against all evidence.

Thin orchestration over verification/claims.py + verification/fact_checker.py —
kept here so the orchestrator has one consistent "agent" surface (CLAUDE.md rule
"one responsibility per module" still holds: the real logic lives in verification/).
"""

from __future__ import annotations

from researchforge.agents.base import BaseAgent
from researchforge.models.claims import Claim
from researchforge.models.evidence import Evidence
from researchforge.verification.claims import extract_claims
from researchforge.verification.fact_checker import verify_claims


class FactCheckerAgent(BaseAgent):
    role = "fact_checker"

    async def extract_and_verify(
        self, *, question: str, task_evidence: list[Evidence], task_id: str, all_evidence: list[Evidence]
    ) -> list[Claim]:
        claims = await extract_claims(
            question=question, evidence=task_evidence, task_id=task_id, llm=self.llm, model=self.model
        )
        verified = verify_claims(claims, all_evidence)
        self.logger.info("claims_verified", task_id=task_id, count=len(verified))
        return verified
