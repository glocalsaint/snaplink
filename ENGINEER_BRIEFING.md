# Engineer Briefing — SnapLink

## Project overview

We are building **SnapLink**, a self-hosted URL shortener.

- **Repo:** https://github.com/glocalsaint/snaplink
- **Design doc:** `DESIGN.md` (read it before starting)
- **Task list:** `TASKS.md` (your tasks are copied below)

---

## Local setup (both engineers)

```bash
git clone https://github.com/glocalsaint/snaplink.git
cd snaplink
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
# Server at http://localhost:8000
```

Run tests at any time with:

```bash
pytest tests/ -v
```

---

## Code style expectations

- Python 3.11+. Use type annotations everywhere — function signatures, variables, return types.
- No inline comments unless the logic is genuinely non-obvious.
- Keep functions short (under 30 lines each as a guideline).
- No `print()` in production code — use Python's `logging` module if needed.
- Docstrings only on public functions/classes that aren't self-explanatory.
- `ruff check .` must pass before opening a PR. Run it locally: `pip install ruff && ruff check backend/ tests/`.
- Format with `ruff format .` before committing.

---

## PR process

1. Branch off `main` with a descriptive name:
   - Engineer-1: `feat/backend-scaffold`, `feat/api-routes`
   - Engineer-2: `feat/frontend-ui`, `feat/test-suite`
2. Make commits as you go. Commit messages: imperative mood, present tense (`add database init`, not `added db`).
3. When a task is done, open a PR against `main`.
4. The **other engineer** reviews your PR:
   - Check that acceptance criteria in `TASKS.md` are met.
   - Leave at least one substantive comment (not just "LGTM").
   - Approve and merge when satisfied.
5. Delete the branch after merge.

---

---

# Engineer-1 Briefing

You own the **backend**: FastAPI app, SQLite database, service logic, and API routes.

## Your tasks

### TASK-001 — Backend: Project scaffold and database layer

**Branch:** `feat/backend-scaffold`  
**Depends on:** nothing

**What to build:**

- `requirements.txt` with these packages:
  ```
  fastapi==0.111.*
  uvicorn[standard]==0.30.*
  aiosqlite==0.20.*
  pydantic[email]==2.*
  httpx==0.27.*
  pytest==8.*
  pytest-asyncio==0.23.*
  anyio==4.*
  ruff==0.4.*
  ```

- `backend/config.py` — a `Settings` dataclass. `db_path` defaults to `"snaplink.db"`, `base_url` to `"http://localhost:8000"`. Read from env vars `SNAPLINK_DB_PATH` and `SNAPLINK_BASE_URL`.

- `backend/database.py`:
  ```python
  async def init_db(db_path: str) -> None:
      # creates the links table if not exists
  
  # async context manager
  async def get_db(db_path: str) -> AsyncGenerator[aiosqlite.Connection, None]:
      ...
  ```
  Table DDL:
  ```sql
  CREATE TABLE IF NOT EXISTS links (
      code TEXT PRIMARY KEY,
      url TEXT NOT NULL,
      created_at TEXT NOT NULL,
      visit_count INTEGER NOT NULL DEFAULT 0
  )
  ```

- `backend/main.py` — FastAPI app with:
  - `lifespan` that calls `init_db` on startup.
  - `StaticFiles` mounted at `/static` serving `frontend/`.
  - `GET /` serves `frontend/index.html`.
  - `GET /health` returns `{"status": "ok"}`.
  - Router included at `/api` (stub the router import if TASK-002 is not done yet).

**Acceptance criteria:**
- `uvicorn backend.main:app --reload` starts cleanly.
- `curl http://localhost:8000/health` → `{"status":"ok"}`.
- `snaplink.db` appears on disk with the correct schema after first run.
- `ruff check backend/` passes.

**Files to create:** `requirements.txt`, `backend/__init__.py`, `backend/config.py`, `backend/database.py`, `backend/main.py`

---

### TASK-002 — Backend: Service layer and API routes

**Branch:** `feat/api-routes`  
**Depends on:** TASK-001 merged to `main`

**What to build:**

- `backend/models.py` — Pydantic v2:
  ```python
  class LinkCreate(BaseModel):
      url: HttpUrl
      custom_code: str | None = None
      # validate custom_code: alphanumeric, 3-20 chars
  
  class LinkResponse(BaseModel):
      code: str
      url: str
      short_url: str
      created_at: str
      visit_count: int
  ```

- `backend/service.py` — all functions are `async`, accept `db: aiosqlite.Connection`:
  - `generate_code(length: int = 6) -> str` — random alphanumeric.
  - `create_link(db, url, base_url, custom_code=None) -> LinkResponse` — raises `ValueError("code_taken")` on duplicate.
  - `get_link(db, code) -> LinkResponse | None`
  - `list_links(db, base_url) -> list[LinkResponse]` — newest first.
  - `delete_link(db, code) -> bool`
  - `increment_visit(db, code) -> None`

- `backend/router.py` — `APIRouter(prefix="/api")`:
  - `POST /links` → 201 `LinkResponse` or 400.
  - `GET /links` → 200 `list[LinkResponse]`.
  - `DELETE /links/{code}` → 204 or 404.

- Update `backend/main.py` to add:
  - `GET /r/{code}` — `RedirectResponse(url=link.url, status_code=302)` or 404.
  - Include router.

**Acceptance criteria (verify with curl):**
```bash
# Create
curl -X POST http://localhost:8000/api/links \
  -H "Content-Type: application/json" \
  -d '{"url":"https://python.org"}' -i
# → 201, body has code/url/short_url/created_at/visit_count

# Redirect
curl -L http://localhost:8000/r/<code>
# → lands on python.org

# List
curl http://localhost:8000/api/links
# → JSON array

# Delete
curl -X DELETE http://localhost:8000/api/links/<code> -i
# → 204

# Unknown redirect
curl http://localhost:8000/r/doesnotexist -i
# → 404
```

**Files to create/modify:** `backend/models.py`, `backend/service.py`, `backend/router.py`, `backend/main.py`

---

## Coordination note for Engineer-1

Engineer-2 will write tests against your API. Agree on the dependency injection
pattern for `get_db` before TASK-004 starts — the test client needs to override it.
A simple approach: expose `get_db` as a FastAPI dependency in `router.py` so it can
be overridden in tests via `app.dependency_overrides`.

---

---

# Engineer-2 Briefing

You own the **frontend** and the **test suite**.

## Your tasks

### TASK-003 — Frontend: Web UI

**Branch:** `feat/frontend-ui`  
**Depends on:** TASK-001 (server running for manual testing; you can build UI against the API spec first)

**What to build:**

- `frontend/index.html` — single page, no JS framework:
  - Form: long URL input (required), optional custom alias input, Submit button.
  - Result area: shows the short URL as a clickable `<a>` tag after creation.
  - Table: columns = Short URL | Original URL | Visits | Created | Delete.
  - On `DOMContentLoaded`, fetch all existing links and render the table.

- `frontend/style.css` — plain CSS only (no Tailwind, no Bootstrap):
  - `body`: white background, `font-family: sans-serif`, `max-width: 800px`, centered with `margin: 0 auto`.
  - Form inputs full-width, `padding: 8px`, `border: 1px solid #ccc`, `border-radius: 4px`.
  - Button: dark background, white text, `padding: 8px 16px`, pointer cursor.
  - Table: `border-collapse: collapse`, `width: 100%`. `th/td`: `padding: 8px 12px`, `border: 1px solid #ddd`.
  - `tr:hover` background: `#f5f5f5`.
  - Success message: green background `#d4edda`. Error message: red background `#f8d7da`. Both have `padding: 8px`, `border-radius: 4px`.

- `frontend/app.js` — no `import`/`export` (plain script tag):
  ```js
  async function createLink(url, customCode) { ... }  // POST /api/links
  async function listLinks() { ... }                   // GET /api/links
  async function deleteLink(code) { ... }              // DELETE /api/links/{code}
  function renderTable(links) { ... }                  // builds tbody rows
  async function handleSubmit(event) { ... }           // form submit handler
  ```
  - `handleSubmit` prevents default form submit.
  - Validates URL field non-empty client-side (no `alert()` — use the result area).
  - On success: renders short URL in result area, refreshes table.
  - On error: shows API error message in result area.
  - Delete button in each table row calls `deleteLink`, then refreshes table.

**Acceptance criteria:**
- `http://localhost:8000` loads without console errors.
- Submitting `https://python.org` creates a link, short URL appears, table row added.
- Clicking Delete removes the row without page reload.
- Empty URL submit shows inline error.
- Duplicate custom alias shows error from API.

**Files to create:** `frontend/index.html`, `frontend/style.css`, `frontend/app.js`

---

### TASK-004 — Tests: pytest suite (unit + integration)

**Branch:** `feat/test-suite`  
**Depends on:** TASK-002 merged to `main`

**What to build:**

- `tests/__init__.py` — empty file.

- `tests/conftest.py`:
  ```python
  import pytest
  import pytest_asyncio
  import aiosqlite
  from httpx import AsyncClient, ASGITransport
  from backend.main import app
  from backend.database import init_db, get_db

  @pytest_asyncio.fixture
  async def db():
      async with aiosqlite.connect(":memory:") as conn:
          await init_db_on_conn(conn)  # initialise schema on the in-memory conn
          yield conn

  @pytest_asyncio.fixture
  async def client(db):
      async def override_get_db():
          yield db
      app.dependency_overrides[get_db] = override_get_db
      async with AsyncClient(
          transport=ASGITransport(app=app), base_url="http://test"
      ) as ac:
          yield ac
      app.dependency_overrides.clear()
  ```
  Note: you may need to refactor `init_db` slightly so it can accept a connection
  object (for in-memory use) vs a path (for production use). Coordinate with Engineer-1.

- `tests/test_service.py` — 11 tests listed in TASK-004 of TASKS.md.

- `tests/test_api.py` — 9 tests listed in TASK-004 of TASKS.md.

**Acceptance criteria:**
- `pytest tests/ -v` shows 20 tests, all passing.
- No test touches disk or makes real HTTP calls.
- `pytest tests/ -q` exit code 0.

**Files to create:** `tests/__init__.py`, `tests/conftest.py`, `tests/test_service.py`, `tests/test_api.py`

---

## Coordination note for Engineer-2

Talk to Engineer-1 before TASK-004 about the `get_db` dependency injection pattern.
The shape of the override in `conftest.py` must match how `get_db` is declared and
used in `router.py`. If `get_db` is a generator dependency (`yield`), the override
must also be a generator.
