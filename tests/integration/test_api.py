"""API integration tests using httpx's ASGITransport against the real FastAPI app,
with mock providers and an in-memory SQLite DB (see conftest.py)."""

from __future__ import annotations

import asyncio

import pytest


@pytest.mark.asyncio
async def test_health_endpoint_reports_mock_providers(lifespan_client):
    client = lifespan_client
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "mock" in body["search_provider"]
    assert "mock" in body["llm_provider"]


@pytest.mark.asyncio
async def test_create_and_poll_research_job(lifespan_client):
    client = lifespan_client
    create_resp = await client.post("/api/research", json={"query": "What is retrieval-augmented generation?", "mode": "quick"})
    assert create_resp.status_code == 202
    research_id = create_resp.json()["research_id"]

    status = "pending"
    for _ in range(60):
        status_resp = await client.get(f"/api/research/{research_id}/status")
        assert status_resp.status_code == 200
        status = status_resp.json()["status"]
        if status in ("completed", "failed", "partial"):
            break
        await asyncio.sleep(0.25)

    assert status in ("completed", "failed", "partial")

    report_resp = await client.get(f"/api/research/{research_id}/report")
    if status == "completed":
        assert report_resp.status_code == 200
        assert "report" in report_resp.json()


@pytest.mark.asyncio
async def test_unknown_research_id_returns_404(lifespan_client):
    client = lifespan_client
    resp = await client.get("/api/research/res_doesnotexist/status")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_request_body_returns_422(lifespan_client):
    client = lifespan_client
    resp = await client.post("/api/research", json={"query": "short"})  # below min_length=8
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_verify_claim_ad_hoc(lifespan_client):
    client = lifespan_client
    resp = await client.post("/api/claims/verify", json={"claim_text": "Python is a programming language"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["claim"]["text"] == "Python is a programming language"
    assert body["claim"]["status"] in ("supported", "partially_supported", "conflicting", "unsupported")


@pytest.mark.asyncio
async def test_history_endpoint_returns_list(lifespan_client):
    client = lifespan_client
    resp = await client.get("/api/research/history")
    assert resp.status_code == 200
    assert "items" in resp.json()
