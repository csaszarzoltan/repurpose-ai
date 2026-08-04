"""Languages API endpoint — multi-language repurposing support.

Exposes the supported-language registry so the frontend language
multi-select dropdown can render ``id``, ``name`` and ``native_name``
for every language the backend can translate into.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.services.languages import SUPPORTED_LANGUAGES

router = APIRouter(prefix="/api/v1", tags=["languages"])


@router.get("/languages", response_model=list[dict[str, str]])
async def list_languages() -> list[dict[str, str]]:
    """List supported target languages (id, name, native_name).

    Used by the frontend language multi-select dropdown.
    """
    return list(SUPPORTED_LANGUAGES.values())
