"""Anthropic LLM provider adapter.

Uses tool-use (forced tool choice) to get schema-constrained structured output,
which is more reliable than asking the model to "return JSON" in prose.
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from researchforge.providers.llm.base import LLMProvider, LLMResponse, LLMUsage

T = TypeVar("T", bound=BaseModel)

# Rough per-1K-token pricing for cost estimation; not authoritative, purely for
# the optional cost_tracking feature. Update as pricing changes.
_PRICE_PER_1K_INPUT = 0.003
_PRICE_PER_1K_OUTPUT = 0.015


class AnthropicLLMProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str) -> None:
        try:
            import anthropic  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "The 'anthropic' package is required for AnthropicLLMProvider. "
                "Install it (`pip install anthropic`) or use the mock provider."
            ) from exc
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    def _usage(self, response: object, model: str) -> LLMUsage:
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        cost = (input_tokens / 1000) * _PRICE_PER_1K_INPUT + (output_tokens / 1000) * _PRICE_PER_1K_OUTPUT
        return LLMUsage(input_tokens=input_tokens, output_tokens=output_tokens, estimated_cost_usd=cost, model=model)

    async def generate(self, prompt: str, *, model: str, system: str = "", max_tokens: int = 1500) -> LLMResponse:
        response = await self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system or "You are a precise, evidence-driven research assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        return LLMResponse(text=text, usage=self._usage(response, model))

    async def generate_structured(
        self, prompt: str, *, model: str, output_model: type[T], system: str = ""
    ) -> tuple[T, LLMUsage]:
        schema = output_model.model_json_schema()
        tool = {
            "name": "emit_result",
            "description": f"Emit the result as {output_model.__name__}.",
            "input_schema": schema,
        }
        response = await self._client.messages.create(
            model=model,
            max_tokens=2000,
            system=system or "You are a precise, evidence-driven research assistant. Always call emit_result.",
            tools=[tool],
            tool_choice={"type": "tool", "name": "emit_result"},
            messages=[{"role": "user", "content": prompt}],
        )
        tool_use = next(b for b in response.content if getattr(b, "type", "") == "tool_use")
        instance = output_model.model_validate(tool_use.input)
        return instance, self._usage(response, model)
