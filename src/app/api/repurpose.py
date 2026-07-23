"""Repurpose API endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.content import RepurposeRequest, RepurposeResponse

router = APIRouter(prefix="/api/v1", tags=["repurpose"])


@router.post("/repurpose", response_model=RepurposeResponse)
async def repurpose_content(request: RepurposeRequest) -> RepurposeResponse:
    """Repurpose content into one or more target formats."""
    raise NotImplementedError
