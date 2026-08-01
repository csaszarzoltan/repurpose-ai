"""Static user workspace entry point."""
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(include_in_schema=False)
WEB = Path(__file__).resolve().parent.parent / "web"


@router.get("/")
async def workspace() -> FileResponse:
    return FileResponse(WEB / "index.html", media_type="text/html")
