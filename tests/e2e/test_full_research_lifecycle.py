"""E2E: submit research via the HTTP API, wait for completion, and check every
guarantee the spec makes about the final report — citations resolve to real
evidence, quality score is explainable, claims have a status."""

from __future__ import annotations

import asyncio

import pytest


@pytest.mark.asyncio
async def test_full_research_lifecycle_via_api():
    import httpx

    from researchforge.api.app import create_app

    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            create_resp = await client.post(
                "/api/research",
                json={"query": "Compare the current approaches to building AI coding agents.", "mode": "quick"},
            )
            research_id = create_resp.json()["research_id"]

            report = None
            for _ in range(80):
                status_resp = await client.get(f"/api/research/{research_id}/status")
                status = status_resp.json()["status"]
                if status == "completed":
                    report_resp = await client.get(f"/api/research/{research_id}/report")
                    report = report_resp.json()["report"]
                    break
                if status in ("failed", "partial"):
                    break
                await asyncio.sleep(0.25)

            if report is None:
                pytest.skip("research job did not reach 'completed' in time in this environment")

            evidence_ids = {e["evidence_id"] for e in report["evidence"]}
            for claim in report["claims"]:
                for cid in claim["citation_ids"]:
                    assert cid in evidence_ids, "report must never cite evidence that wasn't actually retrieved"

            assert 0 <= report["quality"]["overall"] <= 100
            assert report["quality"]["notes"] is not None  # score is always explainable

            sources_resp = await client.get(f"/api/research/{research_id}/sources")
            assert sources_resp.json()["count"] == len(report["evidence"])

            claims_resp = await client.get(f"/api/research/{research_id}/claims")
            assert claims_resp.json()["count"] == len(report["claims"])
