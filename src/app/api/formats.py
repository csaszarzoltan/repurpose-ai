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
    ContentFormat.YOUTUBE_TIKTOK_CAPTION: FormatInfo(
        format_id=ContentFormat.YOUTUBE_TIKTOK_CAPTION,
        name="YouTube/TikTok Caption",
        description="Short-form video caption for YouTube Shorts or TikTok",
        max_length=300,
        supports_images=False,
        supports_links=False,
    ),
    ContentFormat.INSTAGRAM_CAROUSEL: FormatInfo(
        format_id=ContentFormat.INSTAGRAM_CAROUSEL,
        name="Instagram Carousel",
        description="Multi-slide Instagram carousel post",
        max_length=2200,
        supports_images=True,
        supports_links=False,
    ),
    ContentFormat.MEDIUM_ARTICLE: FormatInfo(
        format_id=ContentFormat.MEDIUM_ARTICLE,
        name="Medium Article",
        description="Long-form article for Medium publication",
        max_length=10000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.REDDIT_POST: FormatInfo(
        format_id=ContentFormat.REDDIT_POST,
        name="Reddit Post",
        description="Post for Reddit communities",
        max_length=40000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.LANDING_PAGE: FormatInfo(
        format_id=ContentFormat.LANDING_PAGE,
        name="Landing Page",
        description="Conversion-focused landing page copy",
        max_length=3000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.PRESS_RELEASE: FormatInfo(
        format_id=ContentFormat.PRESS_RELEASE,
        name="Press Release",
        description="Official press release for media distribution",
        max_length=2000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.CASE_STUDY: FormatInfo(
        format_id=ContentFormat.CASE_STUDY,
        name="Case Study",
        description="Customer success story case study",
        max_length=4000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.WHITEPAPER_OUTLINE: FormatInfo(
        format_id=ContentFormat.WHITEPAPER_OUTLINE,
        name="Whitepaper Outline",
        description="Outline and structure for an in-depth whitepaper",
        max_length=5000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.EBOOK_CHAPTER_PLAN: FormatInfo(
        format_id=ContentFormat.EBOOK_CHAPTER_PLAN,
        name="eBook Chapter Plan",
        description="Structured chapter plan for an eBook",
        max_length=5000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.PODCAST_SHOW_NOTES: FormatInfo(
        format_id=ContentFormat.PODCAST_SHOW_NOTES,
        name="Podcast Show Notes",
        description="Show notes and summary for podcast episodes",
        max_length=2500,
        supports_images=False,
        supports_links=True,
    ),
    ContentFormat.LINKEDIN_CAROUSEL: FormatInfo(
        format_id=ContentFormat.LINKEDIN_CAROUSEL,
        name="LinkedIn Carousel",
        description="Multi-page carousel PDF post for LinkedIn",
        max_length=3000,
        supports_images=True,
        supports_links=True,
    ),
    ContentFormat.SAAS_CHANGELOG: FormatInfo(
        format_id=ContentFormat.SAAS_CHANGELOG,
        name="SaaS Changelog",
        description="Product update and changelog entry",
        max_length=1500,
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
