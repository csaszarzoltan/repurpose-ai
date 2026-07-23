"""Repurpose API endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.content import (
    RepurposeRequest,
    RepurposeResponse,
)
from app.services.repurpose import RepurposeService

router = APIRouter(prefix="/api/v1", tags=["repurpose"])


@router.post("/repurpose", response_model=RepurposeResponse)
async def repurpose_content(request: RepurposeRequest) -> RepurposeResponse:
    """Repurpose content into one or more target formats."""
    svc = RepurposeService()
    result = await svc.repurpose(
        content=request.content,
        target_formats=request.target_formats,
        brand_voice=request.brand_voice,
        custom_instructions=request.custom_instructions,
    )
    return result
