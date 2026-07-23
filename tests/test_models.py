"""Tests for content models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.content import (
    BrandVoice,
    ContentFormat,
    ContentItem,
    FormatInfo,
    RepurposeRequest,
    RepurposeResponse,
)

# ── Interface Tests (must pass immediately) ──────────────────


class TestContentFormat:
    """Interface: ContentFormat enum exists and has expected members."""

    def test_importable(self):
        assert ContentFormat is not None

    def test_has_blog_post(self):
        assert hasattr(ContentFormat, "BLOG_POST")

    def test_has_twitter_thread(self):
        assert hasattr(ContentFormat, "TWITTER_THREAD")

    def test_has_linkedin_post(self):
        assert hasattr(ContentFormat, "LINKEDIN_POST")

    def test_has_newsletter(self):
        assert hasattr(ContentFormat, "NEWSLETTER")

    def test_has_video_script(self):
        assert hasattr(ContentFormat, "VIDEO_SCRIPT")

    def test_has_podcast_outline(self):
        assert hasattr(ContentFormat, "PODCAST_OUTLINE")

    def test_has_email_sequence(self):
        assert hasattr(ContentFormat, "EMAIL_SEQUENCE")

    def test_has_social_media(self):
        assert hasattr(ContentFormat, "SOCIAL_MEDIA")

    def test_is_str_enum(self):
        assert issubclass(ContentFormat, str)


class TestBrandVoice:
    """Interface: BrandVoice enum exists and has expected members."""

    def test_importable(self):
        assert BrandVoice is not None

    def test_has_professional(self):
        assert hasattr(BrandVoice, "PROFESSIONAL")

    def test_has_casual(self):
        assert hasattr(BrandVoice, "CASUAL")

    def test_has_humorous(self):
        assert hasattr(BrandVoice, "HUMOROUS")

    def test_has_authoritative(self):
        assert hasattr(BrandVoice, "AUTHORITATIVE")

    def test_has_friendly(self):
        assert hasattr(BrandVoice, "FRIENDLY")

    def test_has_technical(self):
        assert hasattr(BrandVoice, "TECHNICAL")

    def test_is_str_enum(self):
        assert issubclass(BrandVoice, str)


class TestContentItem:
    """Interface: ContentItem model has correct fields."""

    def test_importable(self):
        assert ContentItem is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(ContentItem, BaseModel)

    def test_required_fields(self):
        item = ContentItem(title="T", body="B", source_format=ContentFormat.BLOG_POST)
        assert item.title == "T"
        assert item.body == "B"
        assert item.source_format == ContentFormat.BLOG_POST

    def test_optional_id(self):
        item = ContentItem(title="T", body="B", source_format=ContentFormat.BLOG_POST)
        assert item.id is None

    def test_optional_created_at(self):
        item = ContentItem(title="T", body="B", source_format=ContentFormat.BLOG_POST)
        assert item.created_at is None

    def test_default_tags_empty(self):
        item = ContentItem(title="T", body="B", source_format=ContentFormat.BLOG_POST)
        assert item.tags == []

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            ContentItem(body="B", source_format=ContentFormat.BLOG_POST)

    def test_missing_body_raises(self):
        with pytest.raises(ValidationError):
            ContentItem(title="T", source_format=ContentFormat.BLOG_POST)

    def test_missing_source_format_raises(self):
        with pytest.raises(ValidationError):
            ContentItem(title="T", body="B")


class TestRepurposeRequest:
    """Interface: RepurposeRequest model has correct fields."""

    def test_importable(self):
        assert RepurposeRequest is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(RepurposeRequest, BaseModel)

    def test_required_fields(self):
        item = ContentItem(title="T", body="B", source_format=ContentFormat.BLOG_POST)
        req = RepurposeRequest(
            content=item,
            target_formats=[ContentFormat.TWITTER_THREAD],
        )
        assert req.content == item
        assert req.target_formats == [ContentFormat.TWITTER_THREAD]

    def test_default_brand_voice(self):
        item = ContentItem(title="T", body="B", source_format=ContentFormat.BLOG_POST)
        req = RepurposeRequest(
            content=item,
            target_formats=[ContentFormat.TWITTER_THREAD],
        )
        assert req.brand_voice == BrandVoice.PROFESSIONAL

    def test_optional_custom_instructions(self):
        item = ContentItem(title="T", body="B", source_format=ContentFormat.BLOG_POST)
        req = RepurposeRequest(
            content=item,
            target_formats=[ContentFormat.TWITTER_THREAD],
        )
        assert req.custom_instructions is None


class TestRepurposeResponse:
    """Interface: RepurposeResponse model has correct fields."""

    def test_importable(self):
        assert RepurposeResponse is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(RepurposeResponse, BaseModel)

    def test_has_original_id(self):
        resp = RepurposeResponse(original_id="abc-123")
        assert resp.original_id == "abc-123"

    def test_default_repurposed_empty(self):
        resp = RepurposeResponse(original_id="abc-123")
        assert resp.repurposed == {}

    def test_default_warnings_empty(self):
        resp = RepurposeResponse(original_id="abc-123")
        assert resp.warnings == []

    def test_has_created_at(self):
        resp = RepurposeResponse(original_id="abc-123")
        assert isinstance(resp.created_at, datetime)

    def test_missing_original_id_raises(self):
        with pytest.raises(ValidationError):
            RepurposeResponse()


class TestFormatInfo:
    """Interface: FormatInfo model has correct fields."""

    def test_importable(self):
        assert FormatInfo is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(FormatInfo, BaseModel)

    def test_all_fields_required(self):
        info = FormatInfo(
            format_id=ContentFormat.BLOG_POST,
            name="Blog Post",
            description="Long-form content",
            max_length=5000,
            supports_images=True,
            supports_links=True,
        )
        assert info.format_id == ContentFormat.BLOG_POST
        assert info.name == "Blog Post"
        assert info.description == "Long-form content"
        assert info.max_length == 5000
        assert info.supports_images is True
        assert info.supports_links is True


# ── Behavioral Tests (must fail until implementation) ────────


class TestContentItemBehavior:
    """Behavioral: ContentItem validation and serialization."""

    def test_serialization_roundtrip(self):
        """Model should serialize to dict and back."""
        item = ContentItem(
            id="test-id",
            title="My Title",
            body="My body text",
            source_format=ContentFormat.BLOG_POST,
            tags=["ai", "content"],
            created_at=datetime(2025, 1, 15, 10, 30),
        )
        data = item.model_dump()
        restored = ContentItem(**data)
        assert restored.id == item.id
        assert restored.title == item.title
        assert restored.tags == ["ai", "content"]

    def test_json_serialization(self):
        """Model should serialize to valid JSON string."""
        import json
        item = ContentItem(title="T", body="B", source_format=ContentFormat.BLOG_POST)
        json_str = item.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["title"] == "T"

    def test_accepts_all_formats(self):
        """ContentItem should accept every ContentFormat value."""
        for fmt in ContentFormat:
            item = ContentItem(title="T", body="B", source_format=fmt)
            assert item.source_format == fmt


class TestRepurposeResponseBehavior:
    """Behavioral: RepurposeResponse with repurposed content."""

    def test_repurposed_dict_stores_content(self):
        """Repurposed dict should store content keyed by format."""
        resp = RepurposeResponse(
            original_id="orig-1",
            repurposed={
                ContentFormat.TWITTER_THREAD: "Thread text here",
                ContentFormat.LINKEDIN_POST: "LinkedIn text here",
            },
        )
        assert resp.repurposed[ContentFormat.TWITTER_THREAD] == "Thread text here"
        assert resp.repurposed[ContentFormat.LINKEDIN_POST] == "LinkedIn text here"

    def test_warnings_list(self):
        """Warnings should be a list of strings."""
        resp = RepurposeResponse(
            original_id="orig-1",
            warnings=["Content too long for Twitter thread"],
        )
        assert len(resp.warnings) == 1
        assert "too long" in resp.warnings[0]
