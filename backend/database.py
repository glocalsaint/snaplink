from collections.abc import AsyncGenerator

import aiosqlite

from backend.config import Settings

_settings = Settings()


async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS links (
                code TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                visit_count INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.commit()


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with aiosqlite.connect(_settings.db_path) as db:
        yield db
