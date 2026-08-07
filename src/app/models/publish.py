"""Publish models for multi-platform auto-publishing."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PublishPlatform(StrEnum):
    """Supported publishing platforms."""

    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    MEDIUM = "medium"
    INSTAGRAM = "instagram"
    WORDPRESS = "wordpress"
    GHOST = "ghost"


class PlatformCredentials(BaseModel):
    """OAuth2 credentials for a publishing platform."""

    platform: PublishPlatform
    access_token: str
    refresh_token: str | None = None
    token_expiry: datetime | None = None
    platform_user_id: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PublishRequest(BaseModel):
    """Request to publish content to a platform."""

    platform: PublishPlatform
    content: str
    title: str | None = None
    media_urls: list[str] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)


class PublishResponse(BaseModel):
    """Response from a publish operation."""

    job_id: str
    platform: PublishPlatform
    status: str
    platform_post_id: str | None = None
    errors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
