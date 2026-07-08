# SnapLink — Task Breakdown

## Engineer Assignments

| Engineer    | Focus                        |
|-------------|------------------------------|
| Engineer-1  | Backend (FastAPI + SQLite)   |
| Engineer-2  | Frontend (HTML/JS) + Tests   |

---

## TASK-001 — Backend: Project scaffold and database layer

**Assigned to:** Engineer-1  
**Depends on:** nothing (start immediately)

### Description
Set up the project structure, install dependencies, initialise the SQLite database, and
expose a health-check endpoint to confirm the server is running.

### What to build
- `requirements.txt` listing all dependencies.
- `backend/config.py` — `Settings` dataclass with `db_path` (default `snaplink.db`) and `base_url` (default `http://localhost:8000`). Read values from environment variables with those defaults.
- `backend/database.py` — async SQLite connection using `aiosqlite`. Expose:
  - `init_db(db_path)` — creates the `links` table if not exists.
  - `get_db(db_path)` — async context manager returning an open connection.
- `backend/main.py` — FastAPI app that:
  - Calls `init_db` on startup via `lifespan`.
  - Mounts `frontend/` directory as static files at `/static`.
  - Serves `frontend/index.html` at `GET /`.
  - Includes a `GET /health` route returning `{"status": "ok"}`.
  - Includes the API router (stub is fine; Engineer-2's tests will exercise it).

### Acceptance criteria
- `uvicorn backend.main:app --reload` starts without errors.
- `GET /health` returns `{"status": "ok"}` with HTTP 200.
- `snaplink.db` is created on disk after first startup.
- The `links` table has columns: `code TEXT PRIMARY KEY`, `url TEXT NOT NULL`, `created_at TEXT NOT NULL`, `visit_count INTEGER NOT NULL DEFAULT 0`.
- `ruff check backend/` passes with no errors.

### Files to create
- `requirements.txt`
- `backend/__init__.py` (empty)
- `backend/config.py`
- `backend/database.py`
- `backend/main.py`

---

## TASK-002 — Backend: Service layer and API routes

**Assigned to:** Engineer-1  
**Depends on:** TASK-001

### Description
Implement the core business logic and all REST endpoints described in DESIGN.md.

### What to build

**`backend/models.py`** — Pydantic v2 schemas:
- `LinkCreate`: `url: HttpUrl`, `custom_code: str | None = None`. Validate `custom_code` is alphanumeric and 3–20 chars if provided.
- `LinkResponse`: `code: str`, `url: str`, `short_url: str`, `created_at: str`, `visit_count: int`.

**`backend/service.py`** — async functions (all accept a db connection as first arg):
- `generate_code(length=6) -> str` — returns a random alphanumeric string.
- `create_link(db, url: str, base_url: str, custom_code=None) -> LinkResponse` — inserts a row; raises `ValueError("code_taken")` if custom code already exists; auto-generates code if none provided (retry up to 5 times on collision).
- `get_link(db, code: str) -> LinkResponse | None` — returns link or None.
- `list_links(db, base_url: str) -> list[LinkResponse]` — returns all links newest first.
- `delete_link(db, code: str) -> bool` — deletes and returns True; returns False if not found.
- `increment_visit(db, code: str)` — increments `visit_count` by 1.

**`backend/router.py`** — `APIRouter` with prefix `/api`:
- `POST /links` — call `create_link`; return 201; return 400 if `ValueError("code_taken")`.
- `GET /links` — call `list_links`; return 200.
- `DELETE /links/{code}` — call `delete_link`; return 204 or 404.

**`backend/main.py`** (update) — add redirect route at app level (not under `/api`):
- `GET /r/{code}` — call `get_link` + `increment_visit`; return `RedirectResponse(url, 302)` or 404.

### Acceptance criteria
- All 6 API scenarios from DESIGN.md testing section pass manually via `curl` or `httpx`.
- `POST /api/links` with `{"url":"https://python.org"}` returns 201 with a `code` field.
- `GET /r/{code}` issues a 302 redirect.
- `GET /r/doesnotexist` returns 404.
- `DELETE /api/links/{code}` returns 204; second call returns 404.
- `ruff check backend/` passes.

### Files to create/modify
- `backend/models.py` (create)
- `backend/service.py` (create)
- `backend/router.py` (create)
- `backend/main.py` (modify — add router + redirect route)

---

## TASK-003 — Frontend: Web UI

**Assigned to:** Engineer-2  
**Depends on:** TASK-001 (server must be running to manually test; can develop with a mock)

### Description
Build a clean single-page UI in plain HTML, CSS, and vanilla JavaScript. No build
tools, no frameworks.

### What to build

**`frontend/index.html`**
- Title: "SnapLink".
- Form with: text input for the long URL, optional text input for a custom alias, Submit button.
- A result area showing the generated short URL as a clickable link after submission.
- A table listing all existing links: columns are Short URL, Original URL, Visits, Created, Delete.
- On page load, call `GET /api/links` and populate the table.

**`frontend/style.css`**
- Clean, minimal style. White background, sans-serif font, max-width 800px centered.
- Table with borders and hover highlight.
- Input and button styling (no frameworks — plain CSS only).
- Success/error message area styled with green/red backgrounds.

**`frontend/app.js`**
- `createLink(url, customCode)` — `POST /api/links`, returns parsed JSON.
- `listLinks()` — `GET /api/links`, returns array.
- `deleteLink(code)` — `DELETE /api/links/{code}`.
- `renderTable(links)` — builds and inserts table rows into the DOM; each row has a Delete button wired to `deleteLink`.
- `handleSubmit(event)` — validates URL field is non-empty, calls `createLink`, shows result, refreshes table.
- All fetch errors display a user-friendly error message in the result area.

### Acceptance criteria
- Opening `http://localhost:8000` shows the form and empty links table.
- Submitting a valid URL creates a short link and displays it immediately.
- The short URL appears in the table without a page refresh.
- Clicking Delete removes the row from the table.
- Submitting an empty URL shows an inline error (no alert()).
- Submitting a duplicate custom alias shows an error message.
- Works in the latest version of Chrome and Firefox.

### Files to create
- `frontend/index.html`
- `frontend/style.css`
- `frontend/app.js`

---

## TASK-004 — Tests: pytest suite (unit + integration)

**Assigned to:** Engineer-2  
**Depends on:** TASK-002 (all backend routes must exist)

### Description
Write the full test suite covering all service-layer functions and all API endpoints.

### What to build

**`tests/conftest.py`**
- `@pytest.fixture async def db()` — creates an in-memory SQLite DB, calls `init_db(":memory:")`, yields the connection, closes it.
- `@pytest.fixture async def client(db)` — creates an `httpx.AsyncClient` pointed at the FastAPI app with the test DB injected via dependency override.
  - Override `get_db` dependency to return the in-memory connection.

**`tests/test_service.py`** — pure unit tests (use the `db` fixture):
- `test_generate_code_length` — default 6 chars.
- `test_generate_code_alphanumeric` — only `[A-Za-z0-9]` chars.
- `test_create_link_returns_response` — returns `LinkResponse` with correct `url`.
- `test_create_link_auto_generates_code` — code is 6 chars if no custom code.
- `test_create_link_custom_code` — respects provided custom code.
- `test_create_link_duplicate_raises` — raises `ValueError` for duplicate code.
- `test_get_link_found` — returns link after creation.
- `test_get_link_not_found` — returns `None`.
- `test_delete_link_returns_true` — True on success.
- `test_delete_link_not_found_returns_false` — False for unknown code.
- `test_increment_visit` — `visit_count` goes from 0 to 1.

**`tests/test_api.py`** — integration tests (use the `client` fixture):
- `test_health_check` — `GET /health` → 200 `{"status":"ok"}`.
- `test_create_link_201` — `POST /api/links` happy path.
- `test_create_link_duplicate_code_400` — second POST with same custom code → 400.
- `test_list_links_200` — `GET /api/links` returns list.
- `test_redirect_302` — `GET /r/{code}` → 302, correct `Location`.
- `test_redirect_unknown_404` — `GET /r/bad` → 404.
- `test_delete_link_204` — `DELETE /api/links/{code}` → 204.
- `test_delete_unknown_404` — `DELETE /api/links/bad` → 404.
- `test_visit_count_increments` — call redirect twice, list shows `visit_count == 2`.

### Acceptance criteria
- `pytest tests/ -v` runs all 20 tests.
- All tests pass with exit code 0.
- No test writes to disk or makes real network calls.
- `pytest tests/ --tb=short` output is clean (no warnings from our code).

### Files to create
- `tests/__init__.py` (empty)
- `tests/conftest.py`
- `tests/test_service.py`
- `tests/test_api.py`
