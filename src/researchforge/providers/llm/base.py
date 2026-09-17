"""LLMProvider interface, with structured (JSON-schema-guided) generation support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float | None = None
    model: str = ""


class LLMResponse(BaseModel):
    text: str
    usage: LLMUsage


class LLMProvider(ABC):
    """Interface every LLM backend must implement.

    Agents (agents/*.py) depend only on this interface and never import a vendor
    SDK directly (CLAUDE.md rule 2).
    """

    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, *, model: str, system: str = "", max_tokens: int = 1500) -> LLMResponse:
        """Generate free-text completion."""

    @abstractmethod
    async def generate_structured(
        self, prompt: str, *, model: str, output_model: type[T], system: str = ""
    ) -> tuple[T, LLMUsage]:
        """Generate output constrained to `output_model`'s schema.

        Real adapters use native structured-output / tool-use support where
        available; the mock adapter constructs plausible instances directly.
        """
