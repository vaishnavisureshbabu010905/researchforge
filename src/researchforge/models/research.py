"""Research plan, task, mode, and job-state models.

These are the orchestrator's typed vocabulary — see CLAUDE.md rule 1 ("typed
contracts only"). Nothing here contains business logic beyond simple derived
properties; the logic lives in orchestration/ and agents/.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from researchforge.models.sources import ResearchDomain


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ResearchMode(StrEnum):
    QUICK = "quick"
    DEEP = "deep"
    EXHAUSTIVE = "exhaustive"


class ResearchJobStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    ITERATING = "iterating"
    SYNTHESIZING = "synthesizing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class ResearchTask(BaseModel):
    """One unit of work assigned to a specialized research agent."""

    task_id: str = Field(default_factory=lambda: _new_id("task"))
    subquestion: str
    domain: ResearchDomain
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    depends_on: list[str] = Field(default_factory=list)
    expected_evidence_types: list[str] = Field(default_factory=list)
    verification_required: bool = True

    status: TaskStatus = TaskStatus.PENDING
    iteration: int = 0
    error: str | None = None


class ResearchPlan(BaseModel):
    """The structured output of the Research Planner agent."""

    plan_id: str = Field(default_factory=lambda: _new_id("plan"))
    objective: str
    subquestions: list[str] = Field(default_factory=list)
    required_domains: list[ResearchDomain] = Field(default_factory=list)
    tasks: list[ResearchTask] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    iteration: int = 0


class ResearchModeConfig(BaseModel):
    """Tunables for a research mode. See orchestration/modes.py for the concrete instances."""

    mode: ResearchMode
    max_tasks: int
    max_parallelism: int
    max_iterations: int
    min_evidence_per_task: int
    verification_depth: str  # "light" | "standard" | "thorough"
    quality_threshold: int = Field(ge=0, le=100)
    task_timeout_seconds: int


class ResearchEvent(BaseModel):
    """One entry in a research job's streamed event log (see orchestration + api/routes)."""

    event_id: str = Field(default_factory=lambda: _new_id("evt"))
    research_id: str
    event_type: str
    message: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResearchJob(BaseModel):
    """The full state of a research job."""

    research_id: str = Field(default_factory=lambda: _new_id("res"))
    query: str
    mode: ResearchMode = ResearchMode.DEEP
    status: ResearchJobStatus = ResearchJobStatus.PENDING

    plan: ResearchPlan | None = None
    iteration_count: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    error: str | None = None
