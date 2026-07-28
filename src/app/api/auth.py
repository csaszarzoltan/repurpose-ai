"""Auth API router — registration, login, token refresh, profile."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models.auth import (
    PasswordChange,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    change_password,
    create_user,
    get_user_brand_voice,
    refresh_access_token,
    set_user_brand_voice,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserCreate) -> UserResponse:
    """Register a new user account."""
    try:
        user = create_user(
            email=request.email,
            password=request.password,
            name=request.name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLogin) -> TokenResponse:
    """Authenticate a user and return JWT tokens."""
    try:
        user = authenticate_user(email=request.email, password=request.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    from app.services.auth import create_access_token, create_refresh_token

    access_token = create_access_token(user.user_id, user.email)
    refresh_token = create_refresh_token(user.user_id, user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: TokenRefresh) -> TokenResponse:
    """Refresh an expired access token using a valid refresh token."""
    try:
        new_access, new_refresh = refresh_access_token(request.refresh_token)
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get the current authenticated user's profile."""
    return current_user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
    request: PasswordChange,
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    """Change the current user's password."""
    try:
        change_password(
            user_id=current_user.user_id,
            current_password=request.current_password,
            new_password=request.new_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me/brand-voice")
async def get_my_brand_voice(
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    """Get the current user's brand voice configuration."""
    config = get_user_brand_voice(current_user.user_id)
    if config is None:
        return {
            "brand_voice": "professional",
            "config_overrides": {},
            "custom_instructions": None,
        }
    return config


@router.put("/me/brand-voice")
async def update_my_brand_voice(
    body: dict,
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    """Update the current user's brand voice configuration."""
    return set_user_brand_voice(
        user_id=current_user.user_id,
        brand_voice=body.get("brand_voice", "professional"),
        config_overrides=body.get("config_overrides"),
        custom_instructions=body.get("custom_instructions"),
    )
