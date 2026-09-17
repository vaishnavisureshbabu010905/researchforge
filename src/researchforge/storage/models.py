"""SQLAlchemy ORM models.

These mirror the Pydantic domain models in `models/` but are the persistence
shape, not the API/business shape — repositories.py translates between the two.
Keeping them separate means a schema-driven migration doesn't ripple into every
layer that uses the Pydantic models (CLAUDE.md: typed contracts, one job per file).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ResearchJobRecord(Base):
    __tablename__ = "research_jobs"

    research_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    query: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    iteration_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    evidence: Mapped[list[EvidenceRecord]] = relationship(back_populates="job", cascade="all, delete-orphan")
    claims: Mapped[list[ClaimRecord]] = relationship(back_populates="job", cascade="all, delete-orphan")
    events: Mapped[list[ResearchEventRecord]] = relationship(back_populates="job", cascade="all, delete-orphan")
    report: Mapped[ReportRecord | None] = relationship(
        back_populates="job", uselist=False, cascade="all, delete-orphan"
    )


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    evidence_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    research_id: Mapped[str] = mapped_column(ForeignKey("research_jobs.research_id"))
    payload_json: Mapped[dict] = mapped_column(JSON)  # full Evidence.model_dump(mode="json")
    domain: Mapped[str] = mapped_column(String(255), index=True)
    credibility_score: Mapped[int] = mapped_column(Integer)
    relevance_score: Mapped[float] = mapped_column(Float)
    research_task_id: Mapped[str] = mapped_column(String(64), index=True)

    job: Mapped[ResearchJobRecord] = relationship(back_populates="evidence")


class ClaimRecord(Base):
    __tablename__ = "claims"

    claim_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    research_id: Mapped[str] = mapped_column(ForeignKey("research_jobs.research_id"))
    payload_json: Mapped[dict] = mapped_column(JSON)  # full Claim.model_dump(mode="json")
    status: Mapped[str] = mapped_column(String(32), index=True)
    text: Mapped[str] = mapped_column(Text)

    job: Mapped[ResearchJobRecord] = relationship(back_populates="claims")


class ReportRecord(Base):
    __tablename__ = "reports"

    report_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    research_id: Mapped[str] = mapped_column(ForeignKey("research_jobs.research_id"), unique=True)
    payload_json: Mapped[dict] = mapped_column(JSON)  # full ResearchReport.model_dump(mode="json")
    quality_overall: Mapped[int] = mapped_column(Integer)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    job: Mapped[ResearchJobRecord] = relationship(back_populates="report")


class ResearchEventRecord(Base):
    __tablename__ = "research_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    research_id: Mapped[str] = mapped_column(ForeignKey("research_jobs.research_id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    data_json: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    job: Mapped[ResearchJobRecord] = relationship(back_populates="events")


class MetricRecord(Base):
    """Optional durable metrics sink (in addition to the in-process registry in observability/)."""

    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    research_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    value: Mapped[float] = mapped_column(Float)
    labels_json: Mapped[dict] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
