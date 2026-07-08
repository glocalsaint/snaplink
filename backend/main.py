from contextlib import asynccontextmanager

import aiosqlite
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from backend import service
from backend.config import Settings
from backend.database import get_db, init_db
from backend.router import router

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.db_path)
    yield


app = FastAPI(title="SnapLink", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("frontend/index.html")


@app.get("/r/{code}")
async def redirect_link(
    code: str, db: aiosqlite.Connection = Depends(get_db)
) -> Response:
    link = await service.get_link(db, code)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    await service.increment_visit(db, code)
    return RedirectResponse(url=link.url, status_code=302)
