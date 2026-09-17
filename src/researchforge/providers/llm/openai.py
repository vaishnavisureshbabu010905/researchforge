"""OpenAI-compatible LLM provider adapter (works for OpenAI and OpenAI-compatible endpoints)."""

from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel

from researchforge.providers.llm.base import LLMProvider, LLMResponse, LLMUsage

T = TypeVar("T", bound=BaseModel)

_PRICE_PER_1K_INPUT = 0.0025
_PRICE_PER_1K_OUTPUT = 0.01


class OpenAILLMProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        try:
            import openai  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "The 'openai' package is required for OpenAILLMProvider. "
                "Install it (`pip install openai`) or use the mock provider."
            ) from exc
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    def _usage(self, response: object, model: str) -> LLMUsage:
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
        cost = (input_tokens / 1000) * _PRICE_PER_1K_INPUT + (output_tokens / 1000) * _PRICE_PER_1K_OUTPUT
        return LLMUsage(input_tokens=input_tokens, output_tokens=output_tokens, estimated_cost_usd=cost, model=model)

    async def generate(self, prompt: str, *, model: str, system: str = "", max_tokens: int = 1500) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system or "You are a precise, evidence-driven research assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        text = response.choices[0].message.content or ""
        return LLMResponse(text=text, usage=self._usage(response, model))

    async def generate_structured(
        self, prompt: str, *, model: str, output_model: type[T], system: str = ""
    ) -> tuple[T, LLMUsage]:
        schema = output_model.model_json_schema()
        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (system or "You are a precise research assistant.")
                    + " Respond ONLY with JSON matching this schema: "
                    + json.dumps(schema),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        instance = output_model.model_validate_json(raw)
        return instance, self._usage(response, model)
