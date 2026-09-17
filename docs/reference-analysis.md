# Reference Project Analysis

> This document analyzes `Multi-Agent-deep-researcher-mcp-windows-linux` from the
> `ai-engineering-hub` repository, which was provided as inspiration for ResearchForge.
> ResearchForge is a from-scratch redesign; no code from the reference project is reused.
> All credit for the original demo belongs to its authors — see `README.md#attribution`.

## 1. What the reference project actually is

It is a ~260-line teaching demo, split across four files:

| File | Lines | Role |
|---|---|---|
| `agents.py` | 136 | Defines a 3-agent CrewAI crew and a LinkUp search tool |
| `app.py` | 83 | Streamlit chat UI that calls the crew synchronously |
| `server.py` | 42 | A FastMCP server exposing the crew as one MCP tool |
| `pyproject.toml` | — | `crewai`, `linkup-sdk`, `fastmcp`, `streamlit` |

### 1.1 Agent flow

Three CrewAI `Agent`s run in `Process.sequential`, each producing free text consumed by the next:

```
Web Searcher  --(raw text)-->  Research Analyst  --(raw text)-->  Technical Writer
   (LinkUp search tool)             (no tools)                     (no tools)
```

There is exactly one task per agent, and exactly one search call. The "Research Analyst" and
"Technical Writer" have `allow_delegation` flags but no independent tools — in practice they
only ever transform the text CrewAI hands them.

### 1.2 Search implementation

A single `LinkUpSearchTool` (a `crewai.tools.BaseTool` subclass) wraps `LinkupClient.search()`
and returns `str(search_response)` — the raw LinkUp response object stringified, with no
normalization, deduplication, or structure. The web searcher agent may call it zero, one, or
many times at the LLM's discretion; there is no scheduling, concurrency, or retry logic.

### 1.3 LLM

Hard-coded to a single local Ollama model (`deepseek-r1:7b`) via `crewai.LLM`. There is no
provider abstraction, no per-task model routing, and no way to use a hosted model without
editing source.

### 1.4 MCP implementation

`server.py` wraps `run_research()` as a single FastMCP tool called `research`. It takes a
query string and returns whatever text `crew.kickoff()` produced. There is no job model, no
status tool, no history, and no structured output — the MCP client receives an opaque string.

### 1.5 UI

`app.py` is a single Streamlit page: a text box, a "Research" button, and a blocking spinner.
Results appear once, at the end, as rendered markdown. There is no progress feedback, no
evidence view, no history, and no way to inspect what the agents actually retrieved.

## 2. Strengths worth preserving conceptually

- **Role specialization** — separating "find", "analyze", "write" is a sound decomposition,
  and ResearchForge keeps (and extends) that idea.
- **MCP-first thinking** — exposing research as an MCP tool, not just a chat UI, is the right
  instinct; ResearchForge keeps this but makes the tool surface structured and stateful.
- **Small, readable code** — a genuine virtue for a teaching demo; ResearchForge preserves
  readability while trading some of that minimalism for correctness at scale.

## 3. Weaknesses ResearchForge specifically addresses

| # | Weakness in reference | ResearchForge change |
|---|---|---|
| 1 | Free-text hand-off between agents (`str(search_response)` piped through prompts) | Typed Pydantic models (`Evidence`, `Claim`, `ResearchPlan`, `ResearchReport`) as the contract between every component |
| 2 | Single hard-coded LLM, single hard-coded search provider | `LLMProvider` and `SearchProvider` interfaces with swappable adapters (Anthropic/OpenAI/Ollama/mock; Bright Data/LinkUp/mock) |
| 3 | Strictly sequential execution (one search, one analysis pass) | `asyncio`-based parallel task execution with concurrency limits, timeouts, retries, and partial-failure tolerance |
| 4 | No evidence normalization or trust model — every search hit is treated as equally true | Evidence manager with deduplication, near-duplicate detection, and an explainable credibility score |
| 5 | No fact-checking — the "Technical Writer" just restates whatever the analyst wrote | Dedicated claim extraction + verification pipeline producing SUPPORTED / PARTIALLY_SUPPORTED / CONFLICTING / UNSUPPORTED statuses |
| 6 | No citation guarantee — URLs in the output are never checked against what was actually retrieved | Citation validator that checks every citation resolves to a real, retrieved `Evidence` record, with a coverage score |
| 7 | No iteration — one pass, no matter how thin the evidence | Research loop that detects gaps/conflicts and issues follow-up tasks up to a mode-specific iteration cap |
| 8 | No persistence — results vanish when the Streamlit session ends | SQLite-backed repositories for jobs, plans, evidence, claims, and reports (swappable for Postgres) |
| 9 | No observability — `verbose=True` console logging only | Structured JSON logging + duration/token/cost metrics per agent call |
| 10 | No tests — the project cannot be verified without live API keys | `MockSearchProvider` + `MockLLMProvider` make the entire pipeline deterministically testable offline |
| 11 | One MCP tool, unstructured output | Six MCP tools (`research`, `research_status`, `get_research`, `get_sources`, `verify_claim`, `get_research_history`) with typed schemas |
| 12 | Blocking UI, no progress | SSE event stream (`research_started` → … → `research_completed`) driving a live workspace UI |

## 4. Why the new architecture is better, concretely

The reference project answers "what did the agents say?" ResearchForge is built to answer a
different, harder question: **"why should I believe this, and where exactly did it come
from?"** That requires the evidence/claim/citation layer to be first-class data, not prose —
which is why the single biggest architectural change is replacing "agents talking to each
other in natural language" with "agents producing and consuming typed records that a
verification pipeline can act on." Everything else (parallelism, iteration, persistence,
observability) follows from having that structured substrate to build on.

## 5. What ResearchForge deliberately does *not* change

The core idea of specialized roles feeding a synthesis step is kept, because it is sound. This
is a redesign of the *plumbing and guarantees* around that idea, not a rejection of it.
