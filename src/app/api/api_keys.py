"""API key management router — create, list, revoke API keys."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models.auth import ApiKeyCreate, ApiKeyFullResponse, UserResponse
from app.services.api_key import create_api_key, list_api_keys, revoke_api_key

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyFullResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    request: ApiKeyCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> ApiKeyFullResponse:
    """Create a new API key for the authenticated user.

    The full key_value is returned only once. Store it securely.
    """
    result = create_api_key(
        user_id=current_user.user_id,
        name=request.name,
        scopes=request.scopes,
    )
    return ApiKeyFullResponse(**result)


@router.get("")
async def list_keys(
    current_user: UserResponse = Depends(get_current_user),
) -> list[dict]:
    """List all API keys for the authenticated user."""
    return list_api_keys(current_user.user_id)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    """Revoke (deactivate) an API key by its ID."""
    success = revoke_api_key(key_id=key_id, user_id=current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
