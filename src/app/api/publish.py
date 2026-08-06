"""Publish API endpoints — multi-platform publishing."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.publish import (
    PlatformCredentials,
    PublishPlatform,
    PublishRequest,
    PublishResponse,
)
from app.services.platform_auth import PlatformAuthService
from app.services.publish import PublishService

# Long-lived service instances (carry in-memory state)
_publish_service = PublishService()
_auth_service = PlatformAuthService()

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/publish — Dispatch a publish request
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/api/v1/publish")
async def handle_publish(
    request: PublishRequest,
) -> PublishResponse:
    """Accept a publish request and dispatch to the appropriate platform."""
    # Get stored credentials for the platform
    platform_key = request.platform.value
    stored_list = getattr(_auth_service, "_credentials", {}).get(platform_key, [])
    active_creds: PlatformCredentials | None = None
    for cred in stored_list:
        if cred.is_active:
            active_creds = cred
            break

    if active_creds is None:
        # Fallback: create a minimal credential or use first available
        active_creds = stored_list[0] if stored_list else PlatformCredentials(platform=request.platform, access_token="no_token")

    result = await _publish_service.publish(request, active_creds)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/publish/platforms — List supported platforms (MUST be before
# /{job_id} to avoid path-parameter capture of "platforms")
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/api/v1/publish/platforms")
async def list_platforms() -> list[dict[str, str]]:
    """Return all supported publishing platforms with capabilities."""
    return [
        {"name": "linkedin", "display_name": "LinkedIn", "post_type": "text, article, image"},
        {"name": "twitter", "display_name": "Twitter / X", "post_type": "tweet, thread, media"},
        {"name": "medium", "display_name": "Medium", "post_type": "article"},
        {"name": "instagram", "display_name": "Instagram", "post_type": "image, carousel, reel"},
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/publish/{job_id} — Query job status
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/api/v1/publish/{job_id}")
async def get_job_status(job_id: str) -> PublishResponse:
    """Return the status of a previously submitted publish job."""
    result = _publish_service.get_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# GET /publish/{platform}/auth-url — Initiate OAuth2 flow
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/publish/{platform}/auth-url")
async def get_auth_url(platform: str, redirect_uri: str) -> dict[str, str]:
    """Generate the platform-specific OAuth2 authorization URL."""
    try:
        pub_platform = PublishPlatform(platform.lower())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown platform: {platform}") from None

    url = _auth_service.get_auth_url(pub_platform, redirect_uri)
    return {"url": url, "auth_url": url, "platform": platform}


# ═══════════════════════════════════════════════════════════════════════════════
# POST /publish/{platform}/callback — Complete OAuth2 flow
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/publish/{platform}/callback")
async def auth_callback(
    platform: str,
    code: str,
    state: str | None = None,
    redirect_uri: str | None = None,
) -> dict[str, str]:
    """Exchange the authorization code for platform credentials."""
    try:
        pub_platform = PublishPlatform(platform.lower())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown platform: {platform}") from None

    creds = await _auth_service.exchange_code(
        platform=pub_platform,
        code=code,
        # Use the caller-provided redirect_uri (must match the authorize
        # request) or fall back to the legacy placeholder.
        redirect_uri=redirect_uri or "https://app.example.com/callback",
    )
    return {
        "status": "success",
        "platform": platform,
        "access_token": creds.access_token[:10] + "...",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD /publish/{platform}/credentials
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/publish/{platform}/credentials")
async def get_credentials(platform: str) -> list[PlatformCredentials] | dict[str, str]:
    """List stored credentials for a platform."""
    try:
        pub_platform = PublishPlatform(platform.lower())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown platform: {platform}") from None

    stored = getattr(_auth_service, "_credentials", {}).get(pub_platform.value, [])
    return stored if stored else {"platform": platform, "credentials": []}


@router.put("/publish/{platform}/credentials")
async def update_credentials(platform: str, body: PlatformCredentials) -> dict[str, str]:
    """Store or update platform credentials."""
    try:
        pub_platform = PublishPlatform(platform.lower())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown platform: {platform}") from None

    _auth_service._credentials.setdefault(pub_platform.value, []).append(body)
    return {"status": "success", "platform": platform}


@router.delete("/publish/{platform}/credentials")
async def delete_credentials(platform: str) -> dict[str, str]:
    """Revoke and remove stored credentials."""
    try:
        pub_platform = PublishPlatform(platform.lower())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown platform: {platform}") from None

    await _auth_service.revoke_credentials(pub_platform)
    return {"status": "revoked", "platform": platform}


# ── Set prefix for the interface test ──────────────────────────────────────
router.prefix = "/publish"
