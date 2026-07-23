"""Formats API endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.content import FormatInfo

router = APIRouter(prefix="/api/v1", tags=["formats"])


@router.get("/formats", response_model=list[FormatInfo])
async def list_formats() -> list[FormatInfo]:
    """List all supported content formats."""
    raise NotImplementedError


@router.get("/formats/{format_id}", response_model=FormatInfo)
async def get_format(format_id: str) -> FormatInfo:
    """Get details for a specific format."""
    raise NotImplementedError
