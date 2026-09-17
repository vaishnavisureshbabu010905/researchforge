"""Deterministic mock LLM provider.

Like MockSearchProvider, this is a first-class provider (CLAUDE.md rule 3), not a
test stub. It does not "pretend" to reason — it produces structurally valid,
content-plausible output derived from the prompt/query text, deterministically,
so the whole pipeline (planning -> research -> claims -> synthesis -> quality)
runs end-to-end and is assertable in tests without any API key.

Agents ask for a *typed* output_model; this provider special-cases the handful of
models actually used by agents/ (see the `_BUILDERS` dispatch below) rather than
attempting generic free-form JSON synthesis, which would be unreliable without a
real model.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, TypeVar

from pydantic import BaseModel

from researchforge.providers.llm.base import LLMProvider, LLMResponse, LLMUsage

T = TypeVar("T", bound=BaseModel)


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)


class MockLLMProvider(LLMProvider):
    name = "mock"

    async def generate(self, prompt: str, *, model: str, system: str = "", max_tokens: int = 1500) -> LLMResponse:
        seed = _seed(prompt)
        text = (
            f"[mock:{model}] Based on the available evidence, here is a synthesized response "
            f"({seed % 1000}). This mock generation exists so ResearchForge runs deterministically "
            f"without a live LLM API key — see providers/llm/mock.py."
        )
        usage = LLMUsage(input_tokens=len(prompt.split()), output_tokens=len(text.split()), model=model)
        return LLMResponse(text=text, usage=usage)

    async def generate_structured(
        self, prompt: str, *, model: str, output_model: type[T], system: str = ""
    ) -> tuple[T, LLMUsage]:
        builder = _BUILDERS.get(output_model.__name__)
        if builder is None:
            raise NotImplementedError(
                f"MockLLMProvider has no structured builder for {output_model.__name__}. "
                f"Add one to providers/llm/mock.py::_BUILDERS."
            )
        instance = builder(prompt, output_model)
        usage = LLMUsage(input_tokens=len(prompt.split()), output_tokens=64, model=model)
        return instance, usage


def _extract_query(prompt: str) -> str:
    match = re.search(r"(?:research question|query|objective)[:\s]+(.+)", prompt, re.IGNORECASE)
    if match:
        return match.group(1).strip().strip('"').split("\n")[0][:200]
    return prompt.strip().split("\n")[0][:200] or "the research topic"


def _build_plan_fields(prompt: str) -> dict[str, Any]:
    query = _extract_query(prompt)
    seed = _seed(query)
    angles = [
        "core definitions and current state",
        "leading approaches and how they compare",
        "practical trade-offs and limitations",
        "recent developments and evidence of adoption",
    ]
    n = 2 + (seed % 3)  # 2..4 subquestions, deterministic per query
    subquestions = [f"What does the evidence say about {query} — {angle}?" for angle in angles[:n]]
    return {"objective": f"Investigate: {query}", "subquestions": subquestions}


def _build_claim_text(prompt: str, index: int) -> str:
    query = _extract_query(prompt)
    seed = _seed(f"{query}:{index}")
    templates = [
        "{q} shows measurable trade-offs between performance and simplicity across sources.",
        "Multiple sources indicate {q} has evolved significantly in recent development cycles.",
        "Evidence on {q} is mixed, with sources disagreeing on the primary driver of outcomes.",
        "{q} is generally documented with primary sources providing the strongest support.",
    ]
    return templates[seed % len(templates)].format(q=query)


def _build_research_plan(prompt: str, model: type[T]) -> T:
    fields = _build_plan_fields(prompt)
    return model(**fields)  # type: ignore[call-arg]


def _build_extracted_claims(prompt: str, model: type[T]) -> T:
    # model here is a small wrapper: ExtractedClaimsDraft(claims: list[str])
    query = _extract_query(prompt)
    seed = _seed(query)
    n = 2 + (seed % 3)
    claims = [_build_claim_text(prompt, i) for i in range(n)]
    return model(claims=claims)  # type: ignore[call-arg]


def _build_synthesis(prompt: str, model: type[T]) -> T:
    query = _extract_query(prompt)
    summary = (
        f"This report synthesizes the available evidence on '{query}'. Multiple independent "
        f"sources were reviewed; findings below are grouped by theme and cross-referenced "
        f"against the collected evidence set."
    )
    analysis = (
        f"Across the collected sources, {query} presents recurring themes around trade-offs "
        f"between correctness, complexity, and maintainability. Primary sources were weighted "
        f"more heavily than secondary commentary. Where sources disagreed, both positions are "
        f"presented rather than silently resolved in favor of one."
    )
    return model(  # type: ignore[call-arg]
        executive_summary=summary,
        detailed_analysis=analysis,
        methodology=(
            "Research was decomposed into subquestions by domain (web, technical, academic), "
            "executed in parallel, deduplicated, credibility-scored, and cross-checked for "
            "conflicts before synthesis."
        ),
    )


_BUILDERS = {
    "ResearchPlan": _build_research_plan,
    "ExtractedClaimsDraft": _build_extracted_claims,
    "SynthesisDraft": _build_synthesis,
}
