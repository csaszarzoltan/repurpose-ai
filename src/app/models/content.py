"""Content models for RepurposeAI."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ContentFormat(StrEnum):
    """Supported content formats."""
    BLOG_POST = "blog_post"
    TWITTER_THREAD = "twitter_thread"
    LINKEDIN_POST = "linkedin_post"
    NEWSLETTER = "newsletter"
    VIDEO_SCRIPT = "video_script"
    PODCAST_OUTLINE = "podcast_outline"
    EMAIL_SEQUENCE = "email_sequence"
    SOCIAL_MEDIA = "social_media"
    # New formats from Phase 2
    YOUTUBE_TIKTOK_CAPTION = "youtube_tiktok_caption"
    INSTAGRAM_CAROUSEL = "instagram_carousel"
    MEDIUM_ARTICLE = "medium_article"
    REDDIT_POST = "reddit_post"
    LANDING_PAGE = "landing_page"
    PRESS_RELEASE = "press_release"
    CASE_STUDY = "case_study"
    WHITEPAPER_OUTLINE = "whitepaper_outline"
    EBOOK_CHAPTER_PLAN = "ebook_chapter_plan"
    PODCAST_SHOW_NOTES = "podcast_show_notes"
    LINKEDIN_CAROUSEL = "linkedin_carousel"
    SAAS_CHANGELOG = "saas_changelog"


class BrandVoice(StrEnum):
    """Brand voice presets."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    HUMOROUS = "humorous"
    AUTHORITATIVE = "authoritative"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"


class ContentItem(BaseModel):
    """A piece of content to be repurposed."""
    id: str | None = None
    title: str
    body: str
    source_format: ContentFormat
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class RepurposeRequest(BaseModel):
    """Request to repurpose content."""
    content: ContentItem
    target_formats: list[ContentFormat]
    brand_voice: BrandVoice = BrandVoice.PROFESSIONAL
    custom_instructions: str | None = None
    llm_strategy: str | None = None
    target_languages: list[str] = Field(default_factory=list)


class RepurposeResponse(BaseModel):
    """Response containing repurposed content.

    ``repurposed`` maps each requested format to its generated content.
    The value is a plain ``str`` for the legacy single-language shape, or a
    ``{lang_code: content}`` mapping when ``target_languages`` was requested.
    """
    original_id: str
    repurposed: dict[ContentFormat, str | dict[str, str]] = Field(default_factory=dict)
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
    # Extended fields from Phase 2
    tone_guidance: str = ""
    structure_hints: str = ""
    target_audience: str = ""
