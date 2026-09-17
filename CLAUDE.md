# CLAUDE.md — ResearchForge Project Guide

This file orients any future Claude (or human) session working on this repository.
Read `docs/PROGRESS.md` next for exact current status.

## Purpose

ResearchForge is a multi-agent deep-research platform: given a research question, it plans
subtasks, runs specialized research agents in parallel, collects and scores evidence,
extracts and verifies claims, detects conflicts, iterates until quality thresholds are met,
and produces a cited, quality-scored report. It is exposed via a FastAPI HTTP API, an MCP
server, and a web UI.

It is a redesign of the reference demo in `docs/reference-analysis.md` — see that file before
assuming any behavior carries over from the original.

## Architecture rules

1. **Typed contracts only.** Every boundary between components (agent → evidence manager,
   planner → orchestrator, orchestrator → API) passes Pydantic models defined in
   `src/researchforge/models/`. No free-text hand-offs between pipeline stages.
2. **Providers are interfaces.** Nothing outside `providers/` may import a vendor SDK
   (`anthropic`, `openai`, `linkup`, Bright Data client, etc.) directly. Code depends on
   `SearchProvider` / `LLMProvider` ABCs and gets an instance via `config/settings.py` +
   dependency injection.
3. **Mock providers are first-class**, not test-only afterthoughts. `MockSearchProvider` and
   `MockLLMProvider` must produce realistic, deterministic output so the whole pipeline runs
   end-to-end with zero API keys.
4. **One responsibility per module.** If a file starts doing orchestration *and* scoring *and*
   persistence, split it. No file should need a "part 2".
5. **Partial failure is normal.** A single failed source/task must not fail the research job.
   Orchestration always returns partial results with the failure recorded.
6. **No hidden state.** Research job state lives in `orchestration/state.py` +
   `storage/repositories.py`, not in module-level globals.

## Coding standards

- Python 3.11+, full type hints, Pydantic v2 models for all cross-boundary data.
- `ruff` for lint/format, `mypy` for type checking (see `pyproject.toml`).
- Docstrings on every public class/function that isn't self-evident from its signature.
- No bare `except Exception: pass`. Catch specific exceptions, log, and degrade gracefully.
- No magic numbers for thresholds — everything mode-dependent lives in
  `orchestration/modes.py` / `config/settings.py`.

## Testing requirements

- Unit tests must not require network access or API keys — use the mock providers.
- Any new pipeline stage (evidence, claims, citations, quality) needs unit tests for at least
  the happy path, an edge case (empty input), and a failure case.
- Integration tests exercise the orchestrator and API with mocks wired in via
  `RESEARCHFORGE_ENV=test`.

## Security requirements

- Secrets only via environment variables (`config/settings.py` reads `os.environ`); never
  hard-code keys, never log them.
- `.env` is git-ignored; `.env.example` contains placeholder values only.
- All external URLs fetched by providers go through basic scheme/host validation before use.
- User-supplied research questions and any scraped content are treated as untrusted text —
  never interpolated into shell commands, SQL, or `eval`/`exec`.
- API request bodies are size-limited and validated by Pydantic before touching business logic.

## Development workflow

```
make install     # install backend deps (uv/pip) + frontend deps
make test         # run pytest (unit + integration), mock providers only
make lint          # ruff + mypy
make run            # start FastAPI backend on :8000
make frontend        # start Next.js dev server on :3000
make mcp               # start the MCP server (stdio)
make docker-up           # docker compose up (backend + frontend + sqlite volume)
```

## Important design decisions

- **SQLite by default, Postgres-ready.** `storage/database.py` uses SQLAlchemy Core/ORM
  against a `DATABASE_URL`; swapping to Postgres is a config change, not a code change.
- **SSE, not WebSockets**, for streaming research progress — the event flow is one-directional
  (server → client), which is exactly what SSE is for, with far less infrastructure.
- **Modes are configuration, not code branches.** `QUICK` / `DEEP` / `EXHAUSTIVE` are
  `ResearchModeConfig` instances (task count, parallelism, max iterations, quality threshold);
  the orchestrator reads config, it doesn't `if mode == "deep"` all over the place.
- **Credibility and quality scores are explainable.** Every score is accompanied by the list of
  factors that produced it — never a bare number.

## Current implementation status

See `docs/PROGRESS.md` for the authoritative, continuously-updated status. As of the last
update in this session: core models, providers (mock + real adapters), evidence pipeline,
claim verification, citation validation, quality evaluation, orchestration, FastAPI app, MCP
server, a minimal Next.js frontend, unit/integration tests, Docker, and CI config are all
implemented as real code in this repository. **This code was written and reviewed but could
not be executed inside the authoring sandbox** (no package-index or Docker access there) — see
`docs/PROGRESS.md` §"Known gaps" for exactly what has and hasn't been run.
