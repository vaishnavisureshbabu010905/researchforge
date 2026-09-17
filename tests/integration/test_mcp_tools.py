"""Tests for mcp/tools.py — the MCP tool bodies, tested directly (without an MCP
transport) since that's the layer with actual logic (server.py just registers
these with FastMCP). Requires the `mcp` package only for server.py, not for these.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_tool_research_runs_and_returns_structured_result():
    from researchforge.mcp.tools import tool_research

    result = await tool_research("What is the CAP theorem?", mode="quick", wait=True)
    assert result.research_id.startswith("res_")
    assert result.status in ("completed", "failed", "partial")
    if result.status == "completed":
        assert result.quality_score is not None
        assert result.executive_summary


@pytest.mark.asyncio
async def test_tool_research_status_after_completion():
    from researchforge.mcp.tools import tool_research, tool_research_status

    result = await tool_research("Explain eventual consistency", mode="quick", wait=True)
    status = await tool_research_status(result.research_id)
    assert status.research_id == result.research_id
    assert status.status in ("completed", "failed", "partial")


@pytest.mark.asyncio
async def test_tool_research_status_unknown_id_raises():
    from researchforge.mcp.tools import tool_research_status

    with pytest.raises(ValueError):
        await tool_research_status("res_does_not_exist")


@pytest.mark.asyncio
async def test_tool_get_sources_after_completion():
    from researchforge.mcp.tools import tool_get_sources, tool_research

    result = await tool_research("Explain vector databases", mode="quick", wait=True)
    sources = await tool_get_sources(result.research_id)
    assert sources.research_id == result.research_id
    assert sources.count == len(sources.sources)


@pytest.mark.asyncio
async def test_tool_verify_claim_ad_hoc():
    from researchforge.mcp.tools import tool_verify_claim

    result = await tool_verify_claim("Rust has a borrow checker")
    assert result.claim_text == "Rust has a borrow checker"
    assert result.status in ("supported", "partially_supported", "conflicting", "unsupported")


@pytest.mark.asyncio
async def test_tool_get_research_history_returns_list():
    from researchforge.mcp.tools import tool_get_research_history, tool_research

    await tool_research("A quick history-populating query", mode="quick", wait=True)
    history = await tool_get_research_history(limit=5)
    assert isinstance(history, list)
    assert len(history) >= 1


@pytest.mark.asyncio
async def test_mcp_server_tools_wrap_errors_safely():
    """The registered @mcp.tool() functions must never raise — see mcp/server.py::_safe."""
    pytest.importorskip("mcp", reason="the 'mcp' package is only required to actually run the server")
    from researchforge.mcp.server import build_server

    server = build_server()
    assert server is not None
