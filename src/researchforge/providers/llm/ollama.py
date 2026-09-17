"""Ollama (local model) LLM provider adapter — replaces the reference project's
hard-coded `crewai.LLM(model="ollama/deepseek-r1:7b")` with a swappable adapter.
"""

from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel

from researchforge.providers.llm.base import LLMProvider, LLMResponse, LLMUsage

T = TypeVar("T", bound=BaseModel)


class OllamaLLMProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")

    async def generate(self, prompt: str, *, model: str, system: str = "", max_tokens: int = 1500) -> LLMResponse:
        import httpx

        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self._base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()

        text = data.get("response", "")
        usage = LLMUsage(
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            estimated_cost_usd=0.0,  # local inference — no per-token API cost
            model=model,
        )
        return LLMResponse(text=text, usage=usage)

    async def generate_structured(
        self, prompt: str, *, model: str, output_model: type[T], system: str = ""
    ) -> tuple[T, LLMUsage]:
        schema = output_model.model_json_schema()
        full_prompt = (
            f"{prompt}\n\nRespond ONLY with a single JSON object matching this schema, "
            f"no prose, no markdown fences:\n{json.dumps(schema)}"
        )
        response = await self.generate(full_prompt, model=model, system=system, max_tokens=2000)
        cleaned = response.text.strip().strip("`").removeprefix("json").strip()
        instance = output_model.model_validate_json(cleaned)
        return instance, response.usage
