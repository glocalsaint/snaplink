import random
import string
from datetime import datetime, timezone

import aiosqlite

from backend.models import LinkResponse


def generate_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


async def create_link(
    db: aiosqlite.Connection,
    url: str,
    base_url: str,
    custom_code: str | None = None,
) -> LinkResponse:
    code = custom_code or generate_code()
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        await db.execute(
            "INSERT INTO links (code, url, created_at, visit_count) VALUES (?, ?, ?, 0)",
            (code, url, created_at),
        )
        await db.commit()
    except aiosqlite.IntegrityError:
        if custom_code:
            raise ValueError("code_taken")
        for _ in range(4):
            code = generate_code()
            try:
                await db.execute(
                    "INSERT INTO links (code, url, created_at, visit_count) VALUES (?, ?, ?, 0)",
                    (code, url, created_at),
                )
                await db.commit()
                break
            except aiosqlite.IntegrityError:
                continue
        else:
            raise RuntimeError("Failed to generate unique code after 5 attempts")
    return LinkResponse(
        code=code,
        url=url,
        short_url=f"{base_url}/r/{code}",
        created_at=created_at,
        visit_count=0,
    )


async def get_link(
    db: aiosqlite.Connection, code: str, base_url: str = "http://localhost:8000"
) -> LinkResponse | None:
    async with db.execute(
        "SELECT code, url, created_at, visit_count FROM links WHERE code = ?", (code,)
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        return None
    return LinkResponse(
        code=row[0],
        url=row[1],
        short_url=f"{base_url}/r/{row[0]}",
        created_at=row[2],
        visit_count=row[3],
    )


async def list_links(db: aiosqlite.Connection, base_url: str) -> list[LinkResponse]:
    async with db.execute(
        "SELECT code, url, created_at, visit_count FROM links ORDER BY created_at DESC"
    ) as cursor:
        rows = await cursor.fetchall()
    return [
        LinkResponse(
            code=r[0],
            url=r[1],
            short_url=f"{base_url}/r/{r[0]}",
            created_at=r[2],
            visit_count=r[3],
        )
        for r in rows
    ]


async def delete_link(db: aiosqlite.Connection, code: str) -> bool:
    cursor = await db.execute("DELETE FROM links WHERE code = ?", (code,))
    await db.commit()
    return cursor.rowcount > 0


async def increment_visit(db: aiosqlite.Connection, code: str) -> None:
    await db.execute(
        "UPDATE links SET visit_count = visit_count + 1 WHERE code = ?", (code,)
    )
    await db.commit()
