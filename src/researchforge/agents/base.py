"""Base agent class.

An "agent" in ResearchForge is a thin, typed, testable unit: given injected
providers plus typed input, produce typed output. It has no orchestration
responsibility (no looping, no retries — that's orchestration/execution.py) and
no persistence responsibility (that's storage/).
"""

from __future__ import annotations

from abc import ABC

from researchforge.observability.logging import get_logger
from researchforge.providers.base import SearchProvider
from researchforge.providers.llm.base import LLMProvider


class BaseAgent(ABC):
    """Common constructor + logger for all agents."""

    role: str = "base_agent"

    def __init__(self, *, llm: LLMProvider, search: SearchProvider | None = None, model: str) -> None:
        self.llm = llm
        self.search = search
        self.model = model
        self.logger = get_logger(f"researchforge.agents.{self.role}")
