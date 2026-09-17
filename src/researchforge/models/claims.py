"""Claim models: extracted assertions and their verification status."""

from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import BaseModel, Field


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ClaimStatus(StrEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONFLICTING = "conflicting"
    UNSUPPORTED = "unsupported"


class ClaimKind(StrEnum):
    """Distinguishes factual claims from inference/opinion/recommendation.

    Only FACT claims go through verification against evidence; the others are
    tagged so the report can render them distinctly (see report_generation spec).
    """

    FACT = "fact"
    INFERENCE = "inference"
    OPINION = "opinion"
    RECOMMENDATION = "recommendation"


class Claim(BaseModel):
    claim_id: str = Field(default_factory=lambda: _new_id("cl"))
    text: str
    kind: ClaimKind = ClaimKind.FACT
    importance: float = Field(default=0.5, ge=0.0, le=1.0)

    status: ClaimStatus = ClaimStatus.UNSUPPORTED
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    supporting_evidence_ids: list[str] = Field(default_factory=list)
    conflicting_evidence_ids: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)

    research_task_id: str | None = None

    def independent_supporting_domains(self, evidence_by_id: dict[str, object]) -> set[str]:
        """Domains of supporting evidence, for source-diversity / corroboration checks.

        `evidence_by_id` maps evidence_id -> Evidence; typed loosely here to avoid a
        models/evidence.py <-> models/claims.py import cycle.
        """
        domains: set[str] = set()
        for eid in self.supporting_evidence_ids:
            item = evidence_by_id.get(eid)
            if item is not None:
                domains.add(item.domain)
        return domains
