import pytest
import aiosqlite
from httpx import AsyncClient, ASGITransport
from backend.database import get_db
from backend.main import app

DDL = """
    CREATE TABLE IF NOT EXISTS links (
        code TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        created_at TEXT NOT NULL,
        visit_count INTEGER NOT NULL DEFAULT 0
    )
"""

@pytest.fixture
async def db():
    async with aiosqlite.connect(":memory:") as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(DDL)
        await conn.commit()
        yield conn

@pytest.fixture
async def client(db):
    async def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
