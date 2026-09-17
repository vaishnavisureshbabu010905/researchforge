# Progress

Authoritative, continuously-updated status. Read this first when resuming work in a new
session. This is the final update for the initial build (session 3) — the project is feature
complete against the brief; what remains is execution/verification, not implementation.

## Sandbox constraints (apply to every session working on this repo)

The authoring sandbox has **no package-index access** (`pip install <anything>` fails — no
index reachable), **no Docker daemon**, and **no npm-registry access**. Concretely:

- Python code importing `pydantic`, `pydantic_settings`, `sqlalchemy`, `fastapi`, `mcp`,
  `anthropic`, `openai`, `httpx`, etc. is written against those libraries' real current APIs but
  has **never been run** — no `pytest`, no `uvicorn` boot, no MCP server boot.
- `frontend/` has never had `npm install` or `next build` run against it.
- `docker build` / `docker compose up` have never been run.
- `.github/workflows/ci.yml` has never been executed by an actual runner.

Every "done" below means **written, complete, and statically reviewed** (imports resolved
by AST analysis, names cross-checked, field-level type parity checked between Python/TypeScript
— see "Static audit results" below) — not "verified by running it." Commands to verify
yourself are at the bottom of this file.

## Completed components

### Backend (`src/researchforge/`)
- `config/` — env-driven settings, mock-safe fallbacks, domain reputation table
- `models/` — `sources`, `evidence`, `claims`, `research`, `reports` (the full typed contract layer)
- `providers/` — `base`, `mock`, `linkup`, `brightdata`, `factory` + `llm/{base,mock,anthropic,openai,ollama}`
- `evidence/` — `deduplication`, `credibility`, `ranking`, `manager`
- `verification/` — `confidence`, `conflicts`, `claims` (extraction), `fact_checker`
- `citations/` — `validator`, `formatter`
- `evaluation/evaluator.py` — live 8-dimension quality scorer
- `agents/` — `base`, `planner`, `researcher` (+ 3 domain subclasses), `fact_checker`, `synthesizer`, `evaluator`
- `orchestration/` — `modes`, `state`, `execution`, `orchestrator` (full plan → parallel research →
  evidence → claims → iteration loop → synthesis → citation validation → quality scoring)
- `storage/` — `models` (SQLAlchemy ORM), `database` (async engine/session, SQLite default,
  Postgres-ready via `DATABASE_URL`), `repositories` (`ResearchJobRepository`)
- `api/` — `app.py` (FastAPI factory: CORS, body-size-limit middleware, global exception
  handler, lifespan DB init), `schemas.py`, `dependencies.py` (`ResearchRegistry`),
  `routes/{health,research,claims}.py` — all endpoints from the spec implemented, including SSE
- `mcp/` — `tools.py` (6 typed tool bodies), `server.py` (FastMCP registration, all tools
  wrapped in a `_safe` error-handling decorator)
- `observability/` — structured JSON logging with secret redaction, in-process metrics registry

### Frontend (`frontend/`)
- Config: `package.json`, `tsconfig.json`, `next.config.mjs`, `tailwind.config.ts`,
  `postcss.config.mjs`, `.eslintrc.json`
- `lib/types.ts` (hand-mirrors backend Pydantic models — field parity checked, see audit below),
  `lib/api.ts` (REST client + SSE stream helper)
- Pages: `app/page.tsx` (dashboard: new-research form, mode selector, recent jobs + stats),
  `app/research/[id]/page.tsx` (live SSE workspace: overview/sources/claims/report tabs),
  `app/history/page.tsx` (filterable job history table), `app/loading.tsx`, `app/error.tsx`,
  `app/not-found.tsx`
- Components: `StatusBadge`, `QualityScore`, `EvidenceList`, `ClaimList`, `ModeSelector`,
  `AgentActivity`, `EventTimeline`, `ProgressSteps`, `ResearchPlanView`, `ReportView`,
  `ClaimVerifyBox`

### Tests (`tests/`)
- `conftest.py` — forces mock providers + in-memory SQLite for every test, resets singletons
- Unit: deduplication, credibility, claim confidence/status, citation validation, quality
  evaluator, research modes, mock search provider, planner, evidence manager
- Integration: full orchestrator run (quick + deep modes, event ordering), FastAPI app via
  `httpx.ASGITransport` (health, create/poll job, 404, 422 validation, ad hoc claim verify,
  history), MCP tool bodies (all 6 tools + server construction guarded by
  `pytest.importorskip("mcp")`)
- E2E: full lifecycle through the real API, asserting every citation resolves to real retrieved
  evidence (the core "no fabricated citations" guarantee, checked mechanically)

### Evaluation (`evaluation/` at repo root)
- `datasets/benchmark.json` — 6 questions across technology/product/scientific/historical/
  architecture/current-events categories, each with `expected_domains` + `min_quality`
- `metrics.py` — `BenchmarkResult`, lexical relevance score, domain coverage, `summarize()`
- `benchmark.py` — runner (mock by default, `--live` for real providers, `--output` for JSON dump)
- `README.md` — quick-reference usage doc

### DevOps
- `pyproject.toml` (hatchling build, ruff + mypy + pytest config, optional provider extras)
- `.env.example` (every `Settings` field has a matching entry — verified, see audit below)
- `.gitignore`, `Makefile` (`install/test/test-cov/lint/format/typecheck/run/mcp/frontend/
  evaluate/docker-up/docker-down/clean`)
- `Dockerfile` (backend, non-root user, healthcheck), `frontend/Dockerfile` (multi-stage),
  `docker-compose.yml` (backend + frontend + named SQLite volume)
- `.github/workflows/ci.yml` (backend: ruff + mypy + pytest+coverage + pip-audit; frontend:
  lint + typecheck + build — all mock-only, zero secrets required)

### Documentation
- `README.md` (root — full spec coverage: architecture, features, agents, workflow, evidence/
  claim/citation/quality systems, modes, providers, MCP, API, streaming, frontend, setup, env
  vars, Docker, tests, evaluation, example query, project structure, observability, security,
  status, limitations, roadmap, attribution, license)
- `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/DEVELOPMENT.md`,
  `docs/reference-analysis.md`, `docs/MCP.md`, `docs/EVALUATION.md`, this file
- `LICENSE` (MIT)

## Static audit results (this session)

Ran the following static checks across the whole repository (results, not claims):

1. **Syntax**: every `.py` file under `src/`, `tests/`, `evaluation/` compiles cleanly via
   `py_compile` (no exceptions).
2. **Module resolution**: every `from researchforge.X import Y` / `import researchforge.X`
   resolves to a real file on disk (AST-walked, checked programmatically) — zero unresolved.
3. **Name resolution**: every imported name was checked against top-level definitions in its
   source module; the only "misses" were legitimate submodule imports (e.g.
   `from researchforge.api.routes import claims`, where `claims` is a submodule file, not a
   name in `__init__.py`) — confirmed those target files exist. Zero real mismatches.
4. **Circular imports**: built the module dependency graph from all `researchforge.*` imports
   (including inside functions) and ran cycle detection — **no cycles found**.
5. **`__init__.py` coverage**: every package directory under `src/researchforge/` has one; `src/`
   itself and `evaluation/datasets/` correctly do not (not packages).
6. **Env var parity**: every field in `config/settings.py::Settings` has a matching
   `RESEARCHFORGE_*` entry in `.env.example`, and vice versa (programmatic diff, zero mismatches).
7. **Backend/frontend type parity**: field-by-field diff of `Claim`, `Evidence`,
   `QualityBreakdown`, `CitationValidation`, `ResearchEvent`, `ResearchReport` between the
   Pydantic models and `frontend/src/lib/types.ts`. Found and fixed one gap: `Evidence.metadata`
   and `Evidence.supporting_claim_ids` were missing from the TS interface — added.
8. **SSE event contract**: every event type the orchestrator actually emits
   (`research_started`, `plan_created`, `research_iteration_started`, `evidence_added`,
   `claim_extracted`, `research_gap_detected`, `research_completed`, `research_failed`,
   `task_started`, `source_found`, `task_failed`, `synthesis_started`, `citation_validation`,
   `quality_evaluation`) is registered in the frontend's `lib/api.ts` listener list. The
   frontend also listens for a few events from the original spec's full list
   (`claim_verified`, `source_processed`, `search_started`) that the orchestrator doesn't
   currently emit — harmless (unused `EventSource` listeners are inert), documented here rather
   than silently left.
9. **Security scan**: no `eval(`/`exec(` anywhere in `src/`; no hardcoded API-key-shaped strings
   in `src/`, `frontend/`, `.env.example`, or `docker-compose.yml`; `.env` confirmed present in
   `.gitignore`.
10. **TODO/placeholder scan**: zero `TODO`/`FIXME`/`XXX` markers in `src/` or `frontend/src/`;
    the one `NotImplementedError` in the codebase (`providers/llm/mock.py`) is an intentional
    guard for an unrecognized structured-output type, not an unfinished feature.
11. Also fixed, while reviewing `orchestration/orchestrator.py` during this audit: a leftover
    awkward `task.status.RUNNING if hasattr(...) else ...` expression, replaced with a clean
    `TaskStatus.RUNNING` import + assignment (functionally identical, just clearer — not a
    behavior change).

What this audit **cannot** catch: runtime type errors, logic bugs that only manifest with real
data flowing through the system, dependency version incompatibilities, or anything that only a
real interpreter/test run would surface. See "What to run locally" below.

## Provider architecture check

Confirmed present and isolated behind the `SearchProvider`/`LLMProvider` interfaces (no vendor
SDK imported outside `providers/`):

| Provider | Implemented | Notes |
|---|---|---|
| Mock search | ✅ | default, always available |
| LinkUp | ✅ | `providers/linkup.py`, deferred SDK import |
| Bright Data | ✅ | `providers/brightdata.py`, REST SERP + Unlocker APIs |
| Mock LLM | ✅ | default, always available |
| Anthropic | ✅ | `providers/llm/anthropic.py`, tool-use for structured output |
| OpenAI (+ compatible) | ✅ | `providers/llm/openai.py`, JSON-mode for structured output |
| Ollama | ✅ | `providers/llm/ollama.py`, local, zero cost |
| Gemini | ❌ not implemented | interface + `LLMProviderName.GEMINI` exist; no adapter written — README roadmap item |

## Testing status — be precise about this

- **Written**: yes, comprehensively (unit/integration/e2e, ~756 lines).
- **Statically inspected**: yes — every test file compiles, imports resolve, and test bodies
  were re-read against the actual implementation they exercise (e.g. `test_confidence.py`
  assertions match `verification/confidence.py::assess`'s actual branching logic; `test_api.py`
  paths match `api/routes/research.py`'s actual route table).
- **Actually executed**: **no.** `pytest` is not installable in this sandbox. No test in this
  repository has been run. Any claim of "N tests passing" would be fabricated — none is made
  here or in the README.

## Known limitations

See `README.md#limitations` for the full, user-facing list (lexical conflict detection, lexical
claim-evidence linking, no PDF export, no Alembic migrations, no Gemini adapter, hand-mirrored
frontend types). The most important one for anyone picking this up: **nothing in this repository
has been executed**. Treat it as thoroughly-written, statically-reviewed, unverified code.

## What to run locally to verify everything

```bash
# 1. Backend install + tests
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,anthropic,openai,linkup]"
pytest -q --cov=researchforge --cov-report=term-missing
ruff check src tests
mypy src

# 2. Backend boot
cp .env.example .env
uvicorn researchforge.api.app:app --reload
curl http://localhost:8000/api/health

# 3. MCP server boot
python -m researchforge.mcp.server   # Ctrl+C to stop; or point an MCP client at it, see docs/MCP.md

# 4. Frontend
cd frontend && npm install && npm run lint && npm run typecheck && npm run build && npm run dev

# 5. Evaluation harness
python evaluation/benchmark.py

# 6. Docker
docker compose up --build
curl http://localhost:8000/api/health

# 7. CI (already configured; runs automatically on push/PR to `main` via .github/workflows/ci.yml)
```

If any of these fail, that's real signal this static-review process couldn't catch — please
open an issue / fix forward rather than assuming the write-up above is ground truth over your
own terminal output.

## File/line count snapshot (this session)

- Backend Python (`src/` + `evaluation/`): ~4,300 lines across ~70 files
- Tests: ~760 lines across 15 test files
- Frontend TypeScript/TSX: ~1,290 lines across 20 files
- Total tracked files in the repository: ~140
