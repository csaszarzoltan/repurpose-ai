"""Formats API endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.content import ContentFormat, FormatInfo

router = APIRouter(prefix="/api/v1", tags=["formats"])

# Static format definitions
FORMAT_INFO_MAP: dict[ContentFormat, FormatInfo] = {
    ContentFormat.BLOG_POST: FormatInfo(
        format_id=ContentFormat.BLOG_POST,
        name="Blog Post",
        description="Long-form content for blogs",
        max_length=5000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.TWITTER_THREAD: FormatInfo(
        format_id=ContentFormat.TWITTER_THREAD,
        name="Twitter Thread",
        description="Multi-tweet thread for Twitter/X",
        max_length=1400,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.LINKEDIN_POST: FormatInfo(
        format_id=ContentFormat.LINKEDIN_POST,
        name="LinkedIn Post",
        description="Professional post for LinkedIn",
        max_length=3000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.NEWSLETTER: FormatInfo(
        format_id=ContentFormat.NEWSLETTER,
        name="Newsletter",
        description="Email newsletter content",
        max_length=10000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.VIDEO_SCRIPT: FormatInfo(
        format_id=ContentFormat.VIDEO_SCRIPT,
        name="Video Script",
        description="Script for video production",
        max_length=5000,
        supports_images=False,
        supports_links=False,
    ),
    ContentFormat.PODCAST_OUTLINE: FormatInfo(
        format_id=ContentFormat.PODCAST_OUTLINE,
        name="Podcast Outline",
        description="Outline structure for podcast episodes",
        max_length=3000,
        supports_images=False,
        supports_links=True,
    ),
    ContentFormat.EMAIL_SEQUENCE: FormatInfo(
        format_id=ContentFormat.EMAIL_SEQUENCE,
        name="Email Sequence",
        description="Multi-part email drip campaign",
        max_length=8000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.SOCIAL_MEDIA: FormatInfo(
        format_id=ContentFormat.SOCIAL_MEDIA,
        name="Social Media",
        description="Short social media post",
        max_length=500,
        supports_images=True,
        supports_links=True,
    ),
}


@router.get("/formats", response_model=list[FormatInfo])
async def list_formats() -> list[FormatInfo]:
    """List all supported content formats."""
    return list(FORMAT_INFO_MAP.values())


@router.get("/formats/{format_id}", response_model=FormatInfo)
async def get_format(format_id: str) -> FormatInfo:
    """Get details for a specific format."""
    for fmt in ContentFormat:
        if fmt.value == format_id:
            return FORMAT_INFO_MAP[fmt]
    raise HTTPException(status_code=404, detail=f"Format '{format_id}' not found")
