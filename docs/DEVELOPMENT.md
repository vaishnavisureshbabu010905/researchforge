# Development Guide

## Prerequisites

- Python 3.11+
- Node.js 20+ (frontend only)
- `uv` (recommended) or `pip`

## Setup

```bash
git clone <this-repo>
cd researchforge
cp .env.example .env          # defaults run entirely in mock mode, no keys needed
make install                  # installs backend (uv/pip) + frontend (npm) deps
```

## Running

```bash
make run          # FastAPI on http://localhost:8000 (docs at /docs)
make mcp          # MCP server over stdio
make frontend     # Next.js dev server on http://localhost:3000
```

With no API keys set, `RESEARCHFORGE_SEARCH_PROVIDER` and `RESEARCHFORGE_LLM_PROVIDER` default
to `mock`, and the app logs which provider is active on startup — it never silently pretends to
hit the live web.

## Tests

```bash
make test          # pytest -q  (unit + integration, mocks only, no network)
make test-cov       # with coverage report
```

## Lint / type-check

```bash
make lint      # ruff check + ruff format --check
make format     # ruff format
make typecheck  # mypy src
```

## Adding a new provider

1. Implement `SearchProvider` (see `providers/base.py`) or `LLMProvider`
   (`providers/llm/base.py`).
2. Register it in `config/settings.py::get_search_provider` /
   `get_llm_provider` behind an env-var switch.
3. Add a unit test using it against `providers/mock.py`-style fixtures — never against the live
   API in CI.

## Adding a new agent

Agents live in `agents/`, subclass `agents.base.BaseAgent`, declare a typed input/output pair,
and are pure with respect to everything except the injected `LLMProvider` / `SearchProvider`.
Wire the agent into `orchestration/orchestrator.py`'s task dispatch and add it to the relevant
`ResearchModeConfig` if it should only run in some modes.

## Database migrations

The project uses SQLAlchemy models directly (`storage/models.py`) with `Base.metadata.create_all`
on startup for simplicity; there is no Alembic migration chain yet (see roadmap in README). For
schema changes during development, delete the local `researchforge.db` file and restart.
