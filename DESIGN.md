# SnapLink — URL Shortener

## Project Description

SnapLink is a self-hosted URL shortener. Users submit a long URL and receive a short
code (e.g. `http://localhost:8000/r/abc123`). Visiting the short URL redirects the
browser to the original destination. A simple web UI lets users create and list their
shortened links.

**Why this project?**
- Clean split: Engineer 1 owns the FastAPI backend; Engineer 2 owns the HTML/JS frontend.
- Small scope: ~15 files, completable in a focused sprint.
- 100% open-source stack, no paid APIs, SQLite on disk.

---

## Tech Stack

| Layer       | Technology          | Reason                                  |
|-------------|---------------------|-----------------------------------------|
| Language    | Python 3.11+        | Typed, readable, rich ecosystem         |
| API         | FastAPI 0.111       | Async, auto-docs, Pydantic validation   |
| Server      | Uvicorn             | ASGI server bundled with FastAPI        |
| Database    | SQLite via aiosqlite| Zero-config, file-based                 |
| ORM/Query   | raw SQL (aiosqlite) | Minimal deps, easy to understand        |
| Frontend    | HTML + Vanilla JS   | No build step, no Node required         |
| Testing     | pytest + httpx      | pytest-asyncio for async route tests    |
| Linting     | ruff                | Fast, opinionated, single tool          |

All packages are installable from PyPI with no cost.

---

## Architecture

```
Browser
  │
  │  GET /          → serves index.html (static)
  │  POST /api/links → create short link
  │  GET  /api/links → list all links
  │  DELETE /api/links/{code} → delete a link
  │  GET  /r/{code} → redirect to original URL
  │
  ▼
┌──────────────────────────────────┐
│          FastAPI App             │
│  ┌──────────┐  ┌──────────────┐ │
│  │  Router  │  │ Static files │ │
│  │ /api/*   │  │  /static/*   │ │
│  └────┬─────┘  └──────────────┘ │
│       │                          │
│  ┌────▼─────────────────────┐   │
│  │       Service Layer      │   │
│  │  (link creation, lookup, │   │
│  │   code generation)       │   │
│  └────┬─────────────────────┘   │
│       │                          │
│  ┌────▼─────┐                   │
│  │  SQLite  │  (snaplink.db)    │
│  └──────────┘                   │
└──────────────────────────────────┘
```

---

## API Endpoints

### `POST /api/links`
Create a short link.

**Request body:**
```json
{
  "url": "https://example.com/some/long/path",
  "custom_code": "myalias"   // optional; auto-generated if omitted
}
```

**Response `201`:**
```json
{
  "code": "abc123",
  "url": "https://example.com/some/long/path",
  "short_url": "http://localhost:8000/r/abc123",
  "created_at": "2026-07-08T10:00:00Z",
  "visit_count": 0
}
```

**Errors:**
- `400` — invalid URL or custom code already taken
- `422` — validation error

---

### `GET /api/links`
List all shortened links (newest first).

**Response `200`:**
```json
[
  {
    "code": "abc123",
    "url": "https://example.com/...",
    "short_url": "http://localhost:8000/r/abc123",
    "created_at": "2026-07-08T10:00:00Z",
    "visit_count": 5
  }
]
```

---

### `DELETE /api/links/{code}`
Delete a link by its short code.

**Response `204`** — no body.  
**Error `404`** — code not found.

---

### `GET /r/{code}`
Redirect to original URL. Increments `visit_count`.

**Response `302`** — `Location` header set to original URL.  
**Error `404`** — code not found.

---

## Data Models

### `links` table (SQLite)

| Column       | Type     | Constraints              |
|--------------|----------|--------------------------|
| `code`       | TEXT     | PRIMARY KEY              |
| `url`        | TEXT     | NOT NULL                 |
| `created_at` | TEXT     | NOT NULL (ISO-8601 UTC)  |
| `visit_count`| INTEGER  | NOT NULL DEFAULT 0       |

### Pydantic Schemas (Python)

```python
class LinkCreate(BaseModel):
    url: HttpUrl
    custom_code: str | None = None

class LinkResponse(BaseModel):
    code: str
    url: str
    short_url: str
    created_at: str
    visit_count: int
```

---

## Project Layout

```
snaplink/
├── backend/
│   ├── main.py            # FastAPI app + static mount
│   ├── database.py        # DB init, connection pool
│   ├── models.py          # Pydantic schemas
│   ├── service.py         # Business logic (create, lookup, delete)
│   ├── router.py          # API route handlers
│   └── config.py          # Settings (DB path, base URL)
├── frontend/
│   ├── index.html         # Single-page UI
│   ├── style.css          # Minimal CSS
│   └── app.js             # Fetch calls to /api/links
├── tests/
│   ├── conftest.py        # pytest fixtures (test DB, test client)
│   ├── test_api.py        # Integration tests for all endpoints
│   └── test_service.py    # Unit tests for service layer
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Testing Strategy

### Unit tests (`tests/test_service.py`)
- Test `generate_code()` produces 6-char alphanumeric strings.
- Test `create_link()` rejects invalid URLs.
- Test `create_link()` rejects duplicate custom codes.
- Test `get_link()` returns `None` for unknown codes.

### Integration tests (`tests/test_api.py`)
- `POST /api/links` happy path → 201 + body fields present.
- `POST /api/links` duplicate code → 400.
- `GET /api/links` returns list including created link.
- `GET /r/{code}` returns 302 with correct `Location`.
- `GET /r/unknown` returns 404.
- `DELETE /api/links/{code}` returns 204.
- `DELETE /api/links/unknown` returns 404.
- Visit count increments on each redirect.

### Test tooling
- `pytest` with `pytest-asyncio` and `httpx` (async test client).
- In-memory SQLite (`:memory:`) for isolation — each test gets a fresh DB.
- `ruff` runs as a lint check in CI (manual for now).

---

## Local Setup

```bash
# Clone the repo
git clone https://github.com/glocalsaint/snaplink.git
cd snaplink

# Create virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn backend.main:app --reload

# Open browser
open http://localhost:8000

# Run tests
pytest tests/ -v
```
