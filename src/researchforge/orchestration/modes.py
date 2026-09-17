"""Concrete ResearchModeConfig instances for QUICK / DEEP / EXHAUSTIVE.

CLAUDE.md rule: modes are configuration, not `if mode == "deep"` branches
scattered through the orchestrator. Add/tune a mode here only.
"""

from __future__ import annotations

from researchforge.models.research import ResearchMode, ResearchModeConfig

MODE_CONFIGS: dict[ResearchMode, ResearchModeConfig] = {
    ResearchMode.QUICK: ResearchModeConfig(
        mode=ResearchMode.QUICK,
        max_tasks=2,
        max_parallelism=2,
        max_iterations=1,
        min_evidence_per_task=2,
        verification_depth="light",
        quality_threshold=55,
        task_timeout_seconds=30,
    ),
    ResearchMode.DEEP: ResearchModeConfig(
        mode=ResearchMode.DEEP,
        max_tasks=4,
        max_parallelism=4,
        max_iterations=2,
        min_evidence_per_task=3,
        verification_depth="standard",
        quality_threshold=70,
        task_timeout_seconds=60,
    ),
    ResearchMode.EXHAUSTIVE: ResearchModeConfig(
        mode=ResearchMode.EXHAUSTIVE,
        max_tasks=7,
        max_parallelism=5,
        max_iterations=4,
        min_evidence_per_task=4,
        verification_depth="thorough",
        quality_threshold=82,
        task_timeout_seconds=90,
    ),
}


def get_mode_config(mode: ResearchMode) -> ResearchModeConfig:
    return MODE_CONFIGS[mode]
