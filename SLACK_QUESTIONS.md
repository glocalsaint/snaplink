# Slack Questions — #team channel

No questions — proceeding with reasonable defaults.

## Decisions made without input

- **Language:** Python 3.11. Both engineers are expected to be comfortable with it.
- **Framework:** FastAPI. Auto-generates OpenAPI docs, clean async model.
- **Database:** SQLite via aiosqlite. Zero setup, file on disk, easy to inspect.
- **Frontend:** Vanilla HTML/CSS/JS. No Node, no build step, works out of the box.
- **Short code length:** 6 alphanumeric characters (~56 billion combinations — plenty for local use).
- **Port:** 8000 (uvicorn default).
- **No authentication:** This is a local-only tool; no login/user accounts.
- **No custom domain:** Short URLs use `http://localhost:8000/r/{code}`.
- **Visit count:** Tracked per link, displayed in the UI table.
- **No link expiry:** Links persist until manually deleted.

If any of these defaults need to change, update `backend/config.py` — the base URL
and DB path are the only env-tunable settings.
