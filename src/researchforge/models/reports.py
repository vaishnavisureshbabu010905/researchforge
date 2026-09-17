"""Final research report models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from researchforge.models.claims import Claim
from researchforge.models.evidence import Evidence


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class QualityBreakdown(BaseModel):
    """Explainable quality score — see evaluation/evaluator.py."""

    overall: int = Field(ge=0, le=100)
    evidence_coverage: int = Field(ge=0, le=100)
    source_quality: int = Field(ge=0, le=100)
    source_diversity: int = Field(ge=0, le=100)
    claim_support: int = Field(ge=0, le=100)
    citation_coverage: int = Field(ge=0, le=100)
    contradiction_handling: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)
    freshness: int = Field(ge=0, le=100)
    recommend_another_iteration: bool = False
    notes: list[str] = Field(default_factory=list)


class CitationValidation(BaseModel):
    """Result of validating citations in a report — see citations/validator.py."""

    total_citations: int
    valid_citations: int
    invalid_citation_refs: list[str] = Field(default_factory=list)
    coverage_percent: float = Field(ge=0.0, le=100.0)


class ResearchReport(BaseModel):
    """The final synthesized, cited, scored research report."""

    report_id: str = Field(default_factory=lambda: _new_id("rep"))
    research_id: str
    query: str

    executive_summary: str
    methodology: str
    key_findings: list[str] = Field(default_factory=list)
    detailed_analysis: str
    limitations: list[str] = Field(default_factory=list)
    confidence_assessment: str

    claims: list[Claim] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    citation_validation: CitationValidation
    quality: QualityBreakdown

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_markdown(self) -> str:
        """Render the report as Markdown. See citations/formatter.py for citation-list formatting."""
        from researchforge.citations.formatter import format_sources_section

        lines: list[str] = [
            f"# Research Report: {self.query}",
            "",
            "## Executive Summary",
            self.executive_summary,
            "",
            "## Methodology",
            self.methodology,
            "",
            "## Key Findings",
        ]
        lines += [f"- {f}" for f in self.key_findings] or ["- (none)"]
        lines += ["", "## Detailed Analysis", self.detailed_analysis, "", "## Claims"]

        for claim in self.claims:
            lines.append(
                f"- **[{claim.status.value.upper()}]** ({claim.kind.value}) {claim.text} "
                f"— confidence {claim.confidence:.0%}"
            )

        lines += ["", "## Limitations"]
        lines += [f"- {limitation}" for limitation in self.limitations] or ["- (none identified)"]

        lines += [
            "",
            "## Confidence Assessment",
            self.confidence_assessment,
            "",
            f"## Quality: {self.quality.overall}/100",
            f"- Evidence coverage: {self.quality.evidence_coverage}",
            f"- Source quality: {self.quality.source_quality}",
            f"- Source diversity: {self.quality.source_diversity}",
            f"- Claim support: {self.quality.claim_support}",
            f"- Citation coverage: {self.quality.citation_coverage}",
            f"- Contradiction handling: {self.quality.contradiction_handling}",
            "",
            f"## Citation Coverage: {self.citation_validation.coverage_percent:.0f}%",
            "",
            format_sources_section(self.evidence),
        ]
        return "\n".join(lines)
