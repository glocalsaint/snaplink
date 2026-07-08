from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import Settings
from backend.database import init_db

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.db_path)
    yield


app = FastAPI(title="SnapLink", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("frontend/index.html")
