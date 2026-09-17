"""The Evidence model: the atomic, normalized unit of everything ResearchForge learns."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field, HttpUrl

from researchforge.models.sources import ResearchDomain, SourceType


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CredibilityAssessment(BaseModel):
    """An explainable credibility score. Never expose a bare number without this."""

    score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    """A single normalized, retrieved piece of evidence.

    Every search hit is converted into one of these before it is allowed further
    into the pipeline (see evidence/manager.py). Nothing downstream should ever
    touch a raw provider response.
    """

    evidence_id: str = Field(default_factory=lambda: _new_id("ev"))
    title: str
    url: HttpUrl
    domain: str  # registrable domain, e.g. "arxiv.org" — used for diversity + credibility
    source_type: SourceType = SourceType.UNKNOWN
    research_domain: ResearchDomain = ResearchDomain.WEB

    extracted_content: str = Field(description="Cleaned text extracted from the source")
    summary: str = Field(default="", description="Short summary of what this source claims")

    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    credibility: CredibilityAssessment = Field(default_factory=lambda: CredibilityAssessment(score=50, reasons=["not yet scored"]))

    publication_date: datetime | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    research_task_id: str
    supporting_claim_ids: list[str] = Field(default_factory=list)

    metadata: dict[str, str] = Field(default_factory=dict)

    def content_fingerprint(self) -> str:
        """A cheap fingerprint used by exact-duplicate detection (see evidence/deduplication.py)."""
        return f"{self.domain}:{self.title.strip().lower()}"


class EvidenceCollection(BaseModel):
    """A scored, deduplicated set of evidence for a research job, plus diversity stats."""

    items: list[Evidence] = Field(default_factory=list)
    unique_domains: int = 0
    duplicate_count: int = 0
    near_duplicate_count: int = 0

    def domains(self) -> set[str]:
        return {e.domain for e in self.items}
