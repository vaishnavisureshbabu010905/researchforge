"""ResearchForge MCP server.

Run with: `python -m researchforge.mcp.server` (or `make mcp`). Exposes six typed
tools — see docs/MCP.md for the full contract and an example client config.

Unlike the reference project's single opaque-string `research` tool, every tool
here returns a structured Pydantic model, and none of them can execute arbitrary
code or shell commands (security requirement: "do not expose dangerous arbitrary
code execution tools").
"""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Awaitable, Callable

from researchforge.config.settings import get_settings
from researchforge.mcp import tools
from researchforge.observability.logging import configure_logging, get_logger
from researchforge.storage.database import get_database

logger = get_logger(__name__)


def _safe(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Wraps a tool body so a bad input (e.g. unknown research_id) becomes a
    structured `{"error": ...}` result instead of an unhandled exception reaching
    the MCP transport (security/robustness requirement: safe error handling).
    """

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except ValueError as exc:
            logger.warning("mcp_tool_value_error", tool=fn.__name__, error=str(exc))
            return {"error": str(exc)}
        except Exception as exc:  # noqa: BLE001 - last-resort guard for an MCP tool call
            logger.error("mcp_tool_unexpected_error", tool=fn.__name__, error_type=type(exc).__name__)
            return {"error": "an unexpected error occurred processing this tool call"}

    return wrapper


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "The 'mcp' package is required to run the MCP server. Install it (`pip install mcp`)."
        ) from exc

    mcp = FastMCP("ResearchForge")

    @mcp.tool()
    @_safe
    async def research(query: str, mode: str = "deep") -> dict:
        """Run a deep research job on `query` and return the completed (or best-effort
        partial) result, including quality score, executive summary, and key findings.
        `mode` is one of: quick, deep, exhaustive.
        """
        result = await tools.tool_research(query, mode)
        return result.model_dump()

    @mcp.tool()
    @_safe
    async def research_status(research_id: str) -> dict:
        """Get the current status of a research job (planning/researching/synthesizing/etc.)."""
        result = await tools.tool_research_status(research_id)
        return result.model_dump()

    @mcp.tool()
    @_safe
    async def get_research(research_id: str) -> dict:
        """Get the full result of a research job, including its report if completed."""
        result = await tools.tool_get_research(research_id)
        return result.model_dump()

    @mcp.tool()
    @_safe
    async def get_sources(research_id: str) -> dict:
        """Get every source (piece of evidence) collected for a research job."""
        result = await tools.tool_get_sources(research_id)
        return result.model_dump(mode="json")

    @mcp.tool()
    @_safe
    async def verify_claim(claim_text: str, research_id: str | None = None) -> dict:
        """Verify a specific factual claim against evidence — either a research job's
        existing evidence pool, or a fresh lightweight search if no `research_id` is given.
        """
        result = await tools.tool_verify_claim(claim_text, research_id)
        return result.model_dump()

    @mcp.tool()
    @_safe
    async def get_research_history(limit: int = 20) -> list[dict]:
        """List past research jobs, most recent first, with their quality scores."""
        results = await tools.tool_get_research_history(limit)
        return [r.model_dump() for r in results]

    return mcp


def main() -> None:
    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)
    logger.info("mcp_server_starting", **settings.active_providers_summary())
    database = get_database(settings.database_url)
    asyncio.run(database.create_all())
    server = build_server()
    server.run()


if __name__ == "__main__":
    main()
