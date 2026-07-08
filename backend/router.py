import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from backend import service
from backend.config import Settings
from backend.database import get_db
from backend.models import LinkCreate, LinkResponse

router = APIRouter(prefix="/api")
settings = Settings()


@router.post("/links", response_model=LinkResponse, status_code=201)
async def create_link(
    body: LinkCreate, db: aiosqlite.Connection = Depends(get_db)
) -> LinkResponse:
    try:
        return await service.create_link(
            db, str(body.url), settings.base_url, body.custom_code
        )
    except ValueError as e:
        if "code_taken" in str(e):
            raise HTTPException(status_code=400, detail="Custom code already taken")
        raise


@router.get("/links", response_model=list[LinkResponse])
async def list_links(db: aiosqlite.Connection = Depends(get_db)) -> list[LinkResponse]:
    return await service.list_links(db, settings.base_url)


@router.delete("/links/{code}", status_code=204)
async def delete_link(
    code: str, db: aiosqlite.Connection = Depends(get_db)
) -> Response:
    deleted = await service.delete_link(db, code)
    if not deleted:
        raise HTTPException(status_code=404, detail="Link not found")
    return Response(status_code=204)
