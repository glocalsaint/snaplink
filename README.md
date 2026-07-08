# SnapLink

A self-hosted URL shortener built with FastAPI and vanilla JavaScript.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
open http://localhost:8000
```

## Run tests

```bash
pytest tests/ -v
```

## Stack

- **Backend:** Python 3.11 + FastAPI + SQLite (aiosqlite)
- **Frontend:** HTML + CSS + Vanilla JS (no build step)
- **Tests:** pytest + httpx

See [DESIGN.md](DESIGN.md) for full architecture and API docs.
