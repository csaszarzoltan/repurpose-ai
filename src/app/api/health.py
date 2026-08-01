"""Health check endpoint — returns status and version info."""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.constants import APP_VERSION

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Return health status with version info for deployment monitoring."""
    return {
        "status": "ok",
        "version": APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "capabilities": {
            "content_workspace": "available",
            "project_persistence": "available",
            "pdf_export": "scaffold",
            "analytics_data": "scaffold",
        },
    }
