"""FastAPI dependency injection for JWT auth and API key auth."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.auth import UserResponse
from app.services.analytics.db.repository import (
    MetricsRepository,
    ScoreRepository,
    ValidationRepository,
)
from app.services.api_key import has_scope, validate_api_key
from app.services.auth import decode_token, get_user_by_id

# ── Bearer token scheme ──────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserResponse:
    """Dependency: require a valid JWT access token.

    Extracts the user from the JWT Bearer token and returns their profile.
    Raises 401 if the token is missing, invalid, or expired.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: expected access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(payload.sub)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserResponse | None:
    """Dependency: optionally authenticate via JWT.

    Returns the user profile if a valid access token is provided,
    or None if no token is present. Does NOT raise on missing token.
    """
    if credentials is None:
        return None

    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        return None

    if payload.type != "access":
        return None

    return get_user_by_id(payload.sub)


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
) -> dict:
    """Dependency: require a valid API key via X-API-Key header or Bearer token.

    API keys are used for programmatic access (vs. JWT for user sessions).
    Returns the key record on success.
    """
    # Try X-API-Key header first
    api_key = x_api_key

    # Fall back to Bearer token (for API key in Bearer format)
    if api_key is None and authorization and authorization.startswith("Bearer "):
        api_key = authorization[7:]

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide via X-API-Key header.",
        )

    key_record = validate_api_key(api_key)
    if key_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )

    return key_record


async def require_scope(required_scope: str) -> callable:
    """Dependency factory: require a specific API key scope.

    Usage:
        @router.post("/repurpose")
        async def endpoint(key: dict = Depends(require_scope("repurpose:write"))):
            ...
    """

    async def _scope_checker(key_record: dict = Depends(require_api_key)) -> dict:
        if not has_scope(key_record, required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key missing required scope: {required_scope}",
            )
        return key_record

    return _scope_checker


# ── Analytics repository providers ────────────────────────────
# Module-level singletons so data persisted through the API (e.g. by
# MetricsCollector) stays visible across requests. Tests override these
# providers with seeded repository instances via dependency_overrides.
_metrics_repository = MetricsRepository()
_score_repository = ScoreRepository()
_validation_repository = ValidationRepository()


def get_metrics_repository() -> MetricsRepository:
    """Dependency: the shared analytics metrics repository."""
    return _metrics_repository


def get_score_repository() -> ScoreRepository:
    """Dependency: the shared analytics optimization-score repository."""
    return _score_repository


def get_validation_repository() -> ValidationRepository:
    """Dependency: the shared analytics validation-report repository."""
    return _validation_repository
