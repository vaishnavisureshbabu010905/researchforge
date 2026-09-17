# MCP Server

ResearchForge exposes six typed MCP tools, built with FastMCP
(`src/researchforge/mcp/server.py`), sharing the same orchestration and
persistence path as the HTTP API (`api/dependencies.py::ResearchRegistry`) —
behavior is identical across both surfaces.

This replaces the reference project's single `research(query)` tool, which
returned an opaque string, with six structured tools that return typed,
JSON-serializable results (see `mcp/tools.py`).

## Running the server

```bash
pip install -e .        # installs the `mcp` package as a core dependency
python -m researchforge.mcp.server
# or:
make mcp
```

The server communicates over stdio (FastMCP's default transport), which is
what most MCP clients (Claude Desktop, Claude Code, etc.) expect for a locally
launched server.

## Example client configuration

For a client that reads a JSON config of MCP servers (e.g. Claude Desktop's
`claude_desktop_config.json` or an equivalent):

```json
{
  "mcpServers": {
    "researchforge": {
      "command": "python",
      "args": ["-m", "researchforge.mcp.server"],
      "cwd": "/absolute/path/to/researchforge",
      "env": {
        "RESEARCHFORGE_SEARCH_PROVIDER": "mock",
        "RESEARCHFORGE_LLM_PROVIDER": "mock"
      }
    }
  }
}
```

Swap the `env` block for real provider credentials once you've configured them
(see README.md#provider-architecture); the server logs which providers are
actually active on startup either way.

## Tools

### `research(query: str, mode: str = "deep") -> dict`

Starts a research job and **waits** (bounded — see `mcp/tools.py::_MAX_WAIT_SECONDS`,
currently 180s) for it to reach a terminal state, then returns a summary:
`research_id`, `status`, `quality_score`, `executive_summary`, `key_findings`,
`citation_coverage_percent`. `mode` is one of `quick` / `deep` / `exhaustive`.
If the job is still running when the wait bound is hit, the current
(in-progress) status is returned — poll `research_status` or `get_research`
for the final result.

### `research_status(research_id: str) -> dict`

Current lifecycle status (`pending` → … → `completed`/`failed`/`partial`),
iteration count, and the plan's subquestions if planning has completed.

### `get_research(research_id: str) -> dict`

Same shape as `research()`'s return value — full result including quality
score and findings — without starting a new job or waiting.

### `get_sources(research_id: str) -> dict`

Every piece of evidence collected for the job: title, URL, domain, source
type, credibility score + reasons, relevance score.

### `verify_claim(claim_text: str, research_id: str | None = None) -> dict`

Verifies an arbitrary claim. If `research_id` is given, checks it against that
job's existing evidence pool; otherwise runs a small fresh search scoped to
the claim text. Returns status (`supported` / `partially_supported` /
`conflicting` / `unsupported`), confidence, and evidence counts.

### `get_research_history(limit: int = 20) -> list[dict]`

Past research jobs, most recent first, each with its quality score if one was
computed.

## Error handling

Every tool is wrapped in `mcp/server.py::_safe`, which catches exceptions and
returns `{"error": "..."}` instead of letting an unhandled exception reach the
MCP transport — a malformed `research_id` or bad `mode` value produces a
structured error result, not a crashed tool call (security/robustness
requirement: safe, predictable error handling).

## What this MCP server deliberately does not expose

No tool accepts or executes arbitrary code, shell commands, or file paths —
every tool's inputs are a query string, a research ID, or a mode enum value.
This is a explicit security requirement (see CLAUDE.md and README.md#security):
an MCP tool surface is an attack surface, and ResearchForge's is intentionally
narrow.

## Status

Written and statically reviewed. **Not executed** in the authoring sandbox (no
`mcp` package install available there) — `tests/integration/test_mcp_tools.py`
exercises the tool *bodies* directly (which don't require the `mcp` package)
and is written to run under `pytest`; the one test that actually builds the
FastMCP server (`test_mcp_server_tools_wrap_errors_safely`) uses
`pytest.importorskip("mcp")` so it skips cleanly in an environment without the
package rather than failing. See docs/PROGRESS.md for exactly what has and
hasn't been run.
