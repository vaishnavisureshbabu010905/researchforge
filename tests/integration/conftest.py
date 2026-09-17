"""Integration-test fixtures for the real async database and application surfaces."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
async def integration_database():
    """Initialize the test database for integration tests that call tools directly."""
    from researchforge.storage.database import get_database

    database = get_database()
    await database.create_all()
    try:
        yield
    finally:
        await database.dispose()
