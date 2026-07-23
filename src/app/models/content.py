"""Content models for RepurposeAI."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ContentFormat(str, Enum):
    """Supported content formats."""
    BLOG_POST = "blog_post"
    TWITTER_THREAD = "twitter_thread"
    LINKEDIN_POST = "linkedin_post"
    NEWSLETTER = "newsletter"
    VIDEO_SCRIPT = "video_script"
    PODCAST_OUTLINE = "podcast_outline"
    EMAIL_SEQUENCE = "email_sequence"
    SOCIAL_MEDIA = "social_media"


class BrandVoice(str, Enum):
    """Brand voice presets."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    HUMOROUS = "humorous"
    AUTHORITATIVE = "authoritative"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"


class ContentItem(BaseModel):
    """A piece of content to be repurposed."""
    id: Optional[str] = None
    title: str
    body: str
    source_format: ContentFormat
    tags: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class RepurposeRequest(BaseModel):
    """Request to repurpose content."""
    content: ContentItem
    target_formats: list[ContentFormat]
    brand_voice: BrandVoice = BrandVoice.PROFESSIONAL
    custom_instructions: Optional[str] = None


class RepurposeResponse(BaseModel):
    """Response containing repurposed content."""
    original_id: str
    repurposed: dict[ContentFormat, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FormatInfo(BaseModel):
    """Information about a supported format."""
    format_id: ContentFormat
    name: str
    description: str
    max_length: int
    supports_images: bool
    supports_links: bool
