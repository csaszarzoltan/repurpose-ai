"""Languages API endpoint — multi-language repurposing support.

Pre-dev stub: the route exists (interface contract) but the handler raises
``NotImplementedError`` until the feature is implemented.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["languages"])


@router.get("/languages", response_model=list[dict[str, str]])
async def list_languages() -> list[dict[str, str]]:
    """List supported target languages (id, name, native_name).

    Used by the frontend language multi-select dropdown.
    """
    raise NotImplementedError("GET /api/v1/languages is not implemented yet")
