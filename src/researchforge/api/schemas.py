"""API request/response schemas.

Kept separate from `models/` (the internal domain models) so the HTTP contract
can evolve independently of internal representations — though today they are
thin wrappers, this seam matters once the API needs to version independently.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from researchforge.models.claims import Claim
from researchforge.models.evidence import Evidence
from researchforge.models.reports import ResearchReport
from researchforge.models.research import ResearchEvent, ResearchMode, ResearchPlan


class CreateResearchRequest(BaseModel):
    query: str = Field(min_length=8, max_length=2000)
    mode: ResearchMode = ResearchMode.DEEP


class CreateResearchResponse(BaseModel):
    research_id: str
    status: str
    mode: ResearchMode


class ResearchStatusResponse(BaseModel):
    research_id: str
    query: str
    mode: ResearchMode
    status: str
    iteration_count: int
    plan: ResearchPlan | None
    error: str | None


class SourcesResponse(BaseModel):
    research_id: str
    count: int
    sources: list[Evidence]


class ClaimsResponse(BaseModel):
    research_id: str
    count: int
    claims: list[Claim]


class HistoryItem(BaseModel):
    research_id: str
    query: str
    mode: ResearchMode
    status: str
    quality: int | None = None


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


class VerifyClaimRequest(BaseModel):
    claim_text: str = Field(min_length=3, max_length=2000)
    research_id: str | None = Field(
        default=None, description="If provided, verify against that job's evidence pool; otherwise search fresh."
    )


class VerifyClaimResponse(BaseModel):
    claim: Claim


class ReportResponse(BaseModel):
    report: ResearchReport


class HealthResponse(BaseModel):
    status: str
    environment: str
    search_provider: str
    llm_provider: str
    version: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class EventsResponse(BaseModel):
    research_id: str
    events: list[ResearchEvent]
