"""Repositories: the only layer allowed to hold a DB session (CLAUDE.md rule 6).

Translates between the Pydantic domain models used everywhere else in the
codebase and the SQLAlchemy ORM records defined in storage/models.py. Callers
(api/, mcp/) never see a SQLAlchemy object.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchforge.models.claims import Claim
from researchforge.models.evidence import Evidence
from researchforge.models.reports import ResearchReport
from researchforge.models.research import ResearchEvent, ResearchJob, ResearchPlan
from researchforge.storage.models import (
    ClaimRecord,
    EvidenceRecord,
    ReportRecord,
    ResearchEventRecord,
    ResearchJobRecord,
)


class ResearchJobRepository:
    """CRUD for research jobs and everything that hangs off one: plan, evidence,
    claims, events, and the final report.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_job(self, job: ResearchJob) -> None:
        record = await self.session.get(ResearchJobRecord, job.research_id)
        plan_json = job.plan.model_dump(mode="json") if job.plan else None
        if record is None:
            record = ResearchJobRecord(
                research_id=job.research_id,
                query=job.query,
                mode=job.mode.value,
                status=job.status.value,
                iteration_count=job.iteration_count,
                error=job.error,
                plan_json=plan_json,
                created_at=job.created_at,
                updated_at=job.updated_at,
                completed_at=job.completed_at,
            )
            self.session.add(record)
        else:
            record.status = job.status.value
            record.iteration_count = job.iteration_count
            record.error = job.error
            record.plan_json = plan_json
            record.updated_at = job.updated_at
            record.completed_at = job.completed_at
        await self.session.commit()

    async def save_evidence(self, research_id: str, evidence: list[Evidence]) -> None:
        await self.session.execute(delete(EvidenceRecord).where(EvidenceRecord.research_id == research_id))
        for e in evidence:
            self.session.add(
                EvidenceRecord(
                    evidence_id=e.evidence_id,
                    research_id=research_id,
                    payload_json=e.model_dump(mode="json"),
                    domain=e.domain,
                    credibility_score=e.credibility.score,
                    relevance_score=e.relevance_score,
                    research_task_id=e.research_task_id,
                )
            )
        await self.session.commit()

    async def save_claims(self, research_id: str, claims: list[Claim]) -> None:
        await self.session.execute(delete(ClaimRecord).where(ClaimRecord.research_id == research_id))
        for c in claims:
            self.session.add(
                ClaimRecord(
                    claim_id=c.claim_id,
                    research_id=research_id,
                    payload_json=c.model_dump(mode="json"),
                    status=c.status.value,
                    text=c.text,
                )
            )
        await self.session.commit()

    async def save_report(self, report: ResearchReport) -> None:
        existing = await self.session.get(ReportRecord, report.report_id)
        if existing is None:
            self.session.add(
                ReportRecord(
                    report_id=report.report_id,
                    research_id=report.research_id,
                    payload_json=report.model_dump(mode="json"),
                    quality_overall=report.quality.overall,
                    generated_at=report.generated_at,
                )
            )
        else:
            existing.payload_json = report.model_dump(mode="json")
            existing.quality_overall = report.quality.overall
        await self.session.commit()

    async def append_event(self, event: ResearchEvent) -> None:
        self.session.add(
            ResearchEventRecord(
                event_id=event.event_id,
                research_id=event.research_id,
                event_type=event.event_type,
                message=event.message,
                data_json=event.data,
                timestamp=event.timestamp,
            )
        )
        await self.session.commit()

    async def get_job(self, research_id: str) -> ResearchJob | None:
        record = await self.session.get(ResearchJobRecord, research_id)
        if record is None:
            return None
        return _job_from_record(record)

    async def get_evidence(self, research_id: str) -> list[Evidence]:
        rows = await self.session.execute(select(EvidenceRecord).where(EvidenceRecord.research_id == research_id))
        return [Evidence.model_validate(r.payload_json) for r in rows.scalars().all()]

    async def get_claims(self, research_id: str) -> list[Claim]:
        rows = await self.session.execute(select(ClaimRecord).where(ClaimRecord.research_id == research_id))
        return [Claim.model_validate(r.payload_json) for r in rows.scalars().all()]

    async def get_report(self, research_id: str) -> ResearchReport | None:
        rows = await self.session.execute(select(ReportRecord).where(ReportRecord.research_id == research_id))
        record = rows.scalar_one_or_none()
        if record is None:
            return None
        return ResearchReport.model_validate(record.payload_json)

    async def get_events(self, research_id: str) -> list[ResearchEvent]:
        rows = await self.session.execute(
            select(ResearchEventRecord)
            .where(ResearchEventRecord.research_id == research_id)
            .order_by(ResearchEventRecord.timestamp)
        )
        return [
            ResearchEvent(
                event_id=r.event_id,
                research_id=r.research_id,
                event_type=r.event_type,
                message=r.message,
                data=r.data_json,
                timestamp=r.timestamp,
            )
            for r in rows.scalars().all()
        ]

    async def list_history(self, *, limit: int = 50) -> list[ResearchJob]:
        rows = await self.session.execute(
            select(ResearchJobRecord).order_by(ResearchJobRecord.created_at.desc()).limit(limit)
        )
        return [_job_from_record(r) for r in rows.scalars().all()]


def _job_from_record(record: ResearchJobRecord) -> ResearchJob:
    plan = ResearchPlan.model_validate(record.plan_json) if record.plan_json else None
    return ResearchJob(
        research_id=record.research_id,
        query=record.query,
        mode=record.mode,  # type: ignore[arg-type] - Pydantic coerces str -> enum
        status=record.status,  # type: ignore[arg-type]
        plan=plan,
        iteration_count=record.iteration_count,
        created_at=record.created_at,
        updated_at=record.updated_at,
        completed_at=record.completed_at,
        error=record.error,
    )
