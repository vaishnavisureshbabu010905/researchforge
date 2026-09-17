# Implementation Plan

Executed in the phases below (mirrors the execution strategy given in the original brief).
Check `docs/PROGRESS.md` for real-time status; this file is the plan, not the status.

| Phase | Scope | Key modules |
|---|---|---|
| 1 | Docs: reference analysis, architecture, this plan | `docs/*` |
| 2 | Config, models, provider interfaces + mocks, persistence layer | `config/`, `models/`, `providers/`, `storage/` |
| 3 | Planner, agents, orchestration, parallel execution, modes | `agents/`, `orchestration/` |
| 4 | Evidence manager, dedup, credibility, claims, fact-checking, conflicts, iteration | `evidence/`, `verification/` |
| 5 | Synthesis, citations, quality evaluation, reports | `agents/synthesizer.py`, `citations/`, `evaluation/` |
| 6 | FastAPI app + SSE streaming, MCP server | `api/`, `mcp/` |
| 7 | Frontend: dashboard, research flow, workspace, report, history | `frontend/` |
| 8 | Tests, evaluation harness, observability, cost tracking, Docker, CI | `tests/`, `evaluation/` (root), `observability/`, `Dockerfile`, `.github/` |
| 9 | Full audit against the validation checklist | this session, see PROGRESS.md final entry |

## Scope decisions made during implementation

To keep the system coherent rather than a pile of stub files, a few deliberate scope choices
were made (all reversible/extensible later — see `docs/PROGRESS.md` → "Known gaps / next
steps"):

- **Three research agents** (web, technical, academic) plus planner, fact-checker, synthesizer,
  evaluator — matches the spec's 8-agent list without adding a 9th "evidence analyst" agent as a
  separate LLM role; evidence extraction is deterministic code in `evidence/manager.py` fed by
  the three research agents, since "extract evidence from sources" doesn't need its own LLM
  persona on top of the research agents that already read the sources.
- **Frontend covers dashboard, new-research, live workspace (SSE-driven), report view, and
  history** as server-rendered/client Next.js pages against the FastAPI SSE + REST API. Source
  explorer / claim explorer are implemented as sections within the workspace/report pages
  rather than fully separate routes, to keep the shipped frontend real and working rather than
  spread thin across many partially-implemented pages.
- **PDF report export** is not implemented (Markdown/JSON/HTML are); flagged as a roadmap item.
- **Bright Data adapter** implements the documented REST/MCP-proxy shape but, like every
  external provider, defers to `MockSearchProvider` unless `BRIGHTDATA_API_KEY` is set —
  documented precisely in `README.md#provider-architecture`.
