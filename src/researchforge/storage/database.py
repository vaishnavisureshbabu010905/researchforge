"""Database engine + session management.

SQLite by default (`sqlite+aiosqlite:///...`); swapping to Postgres is a
`DATABASE_URL` change to something like
`postgresql+asyncpg://user:pass@host/db` — no code here is SQLite-specific
except the `connect_args` guard below, which SQLAlchemy requires only for
SQLite's single-thread-connection quirk.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from researchforge.storage.models import Base


class Database:
    def __init__(self, database_url: str) -> None:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine: AsyncEngine = create_async_engine(database_url, connect_args=connect_args)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def create_all(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session


_db_instance: Database | None = None


def get_database(database_url: str | None = None) -> Database:
    """Process-wide database singleton, created lazily from settings on first use."""
    global _db_instance
    if _db_instance is None:
        if database_url is None:
            from researchforge.config.settings import get_settings

            database_url = get_settings().database_url
        _db_instance = Database(database_url)
    return _db_instance


def reset_database_singleton() -> None:
    """Test-only helper: force the next get_database() call to build a fresh instance."""
    global _db_instance
    _db_instance = None
