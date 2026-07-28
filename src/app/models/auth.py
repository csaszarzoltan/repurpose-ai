"""Auth models for JWT-based user authentication and multi-tenant support."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class UserRole(StrEnum):
    """User role for RBAC support."""

    ADMIN = "admin"
    USER = "user"


class UserCreate(BaseModel):
    """Request model for user registration."""

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    """Request model for user login."""

    email: str
    password: str


class UserResponse(BaseModel):
    """Response model for user data (no password/sensitive fields)."""

    user_id: str
    email: str
    name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime | None = None


class TokenResponse(BaseModel):
    """Response model for JWT token authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour


class TokenRefresh(BaseModel):
    """Request model for refreshing an access token."""

    refresh_token: str


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # user_id
    email: str
    exp: int
    type: str = "access"  # "access" or "refresh"


class PasswordChange(BaseModel):
    """Request model for password change."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ApiKeyCreate(BaseModel):
    """Request model for creating a new API key."""

    name: str = Field(min_length=1, max_length=100)
    scopes: list[str] = Field(default_factory=lambda: ["repurpose:write"])


class ApiKeyResponse(BaseModel):
    """Response model for API key (key_value only shown on creation)."""

    key_id: str
    name: str
    scopes: list[str]
    is_active: bool = True
    created_at: datetime
    last_used_at: datetime | None = None
    key_prefix: str  # First 8 chars of the key (for identification)


class ApiKeyFullResponse(ApiKeyResponse):
    """Response model including the full key value (only on creation)."""

    key_value: str


class BrandVoiceConfigPerUser(BaseModel):
    """Per-user brand voice configuration overrides."""

    user_id: str
    brand_voice: str = "professional"
    config_overrides: dict[str, str] = Field(default_factory=dict)
    custom_instructions: str | None = None
    updated_at: datetime | None = None
