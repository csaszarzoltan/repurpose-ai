"""Pre-dev tests for Publish models (Phase 0).

Source of truth: analysis/analysis-brief.md §4.1 Data Models.
Interface tests → xfail until models/publish.py is implemented.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.publish import (
        PlatformCredentials,
        PublishPlatform,
        PublishRequest,
        PublishResponse,
    )

    HAS_PUBLISH_MODELS = True
except (ImportError, ModuleNotFoundError):
    HAS_PUBLISH_MODELS = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — PublishPlatform enum
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_MODELS, reason="models/publish.py not implemented yet")
class TestPublishPlatform:
    """Interface: PublishPlatform enum values."""

    def test_importable(self):
        assert PublishPlatform is not None

    def test_is_str_enum(self):
        assert issubclass(PublishPlatform, str)

    def test_has_linkedin(self):
        assert hasattr(PublishPlatform, "LINKEDIN")
        assert PublishPlatform.LINKEDIN == "linkedin"

    def test_has_twitter(self):
        assert hasattr(PublishPlatform, "TWITTER")
        assert PublishPlatform.TWITTER == "twitter"

    def test_has_medium(self):
        assert hasattr(PublishPlatform, "MEDIUM")
        assert PublishPlatform.MEDIUM == "medium"

    def test_has_instagram(self):
        assert hasattr(PublishPlatform, "INSTAGRAM")
        assert PublishPlatform.INSTAGRAM == "instagram"

    def test_all_values_expected(self):
        values = {v.value for v in PublishPlatform}
        assert values == {"linkedin", "twitter", "medium", "instagram", "wordpress", "ghost"}

    def test_all_members_expected(self):
        members = set(PublishPlatform.__members__)
        assert members == {"LINKEDIN", "TWITTER", "MEDIUM", "INSTAGRAM", "WORDPRESS", "GHOST"}


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — PlatformCredentials
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_MODELS, reason="models/publish.py not implemented yet")
class TestPlatformCredentialsInterface:
    """Interface: PlatformCredentials model fields and validation."""

    def test_importable(self):
        assert PlatformCredentials is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(PlatformCredentials, BaseModel)

    def test_required_fields(self):
        creds = PlatformCredentials(
            platform=PublishPlatform.LINKEDIN,
            access_token="tok_abc123",
        )
        assert creds.platform == PublishPlatform.LINKEDIN
        assert creds.access_token == "tok_abc123"

    def test_optional_refresh_token(self):
        creds = PlatformCredentials(
            platform=PublishPlatform.TWITTER,
            access_token="tok_abc123",
        )
        assert creds.refresh_token is None

    def test_optional_token_expiry(self):
        creds = PlatformCredentials(
            platform=PublishPlatform.MEDIUM,
            access_token="tok_abc123",
        )
        assert creds.token_expiry is None

    def test_optional_platform_user_id(self):
        creds = PlatformCredentials(
            platform=PublishPlatform.LINKEDIN,
            access_token="tok_abc123",
        )
        assert creds.platform_user_id is None

    def test_is_active_defaults_true(self):
        creds = PlatformCredentials(
            platform=PublishPlatform.LINKEDIN,
            access_token="tok_abc123",
        )
        assert creds.is_active is True

    def test_is_active_can_be_false(self):
        creds = PlatformCredentials(
            platform=PublishPlatform.LINKEDIN,
            access_token="tok_abc123",
            is_active=False,
        )
        assert creds.is_active is False

    def test_missing_platform_raises(self):
        with pytest.raises(ValidationError):
            PlatformCredentials(access_token="tok_abc123")

    def test_missing_access_token_raises(self):
        with pytest.raises(ValidationError):
            PlatformCredentials(platform=PublishPlatform.LINKEDIN)


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — PublishRequest
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_MODELS, reason="models/publish.py not implemented yet")
class TestPublishRequestInterface:
    """Interface: PublishRequest model fields and defaults."""

    def test_importable(self):
        assert PublishRequest is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(PublishRequest, BaseModel)

    def test_required_fields(self):
        req = PublishRequest(
            platform=PublishPlatform.TWITTER,
            content="Hello world!",
        )
        assert req.platform == PublishPlatform.TWITTER
        assert req.content == "Hello world!"

    def test_optional_title(self):
        req = PublishRequest(
            platform=PublishPlatform.LINKEDIN,
            content="Post body",
        )
        assert req.title is None

    def test_title_when_provided(self):
        req = PublishRequest(
            platform=PublishPlatform.LINKEDIN,
            content="Post body",
            title="My Post Title",
        )
        assert req.title == "My Post Title"

    def test_media_urls_defaults_empty(self):
        req = PublishRequest(
            platform=PublishPlatform.MEDIUM,
            content="Article body",
        )
        assert req.media_urls == []

    def test_media_urls_when_provided(self):
        req = PublishRequest(
            platform=PublishPlatform.MEDIUM,
            content="Article body",
            media_urls=["https://example.com/img.png"],
        )
        assert req.media_urls == ["https://example.com/img.png"]

    def test_options_defaults_empty(self):
        req = PublishRequest(
            platform=PublishPlatform.TWITTER,
            content="Hello",
        )
        assert req.options == {}

    def test_options_with_values(self):
        req = PublishRequest(
            platform=PublishPlatform.MEDIUM,
            content="Article",
            options={"publish_status": "draft", "tags": ["tech"]},
        )
        assert req.options["publish_status"] == "draft"

    def test_missing_platform_raises(self):
        with pytest.raises(ValidationError):
            PublishRequest(content="Hello")

    def test_missing_content_raises(self):
        with pytest.raises(ValidationError):
            PublishRequest(platform=PublishPlatform.TWITTER)


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — PublishResponse
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_MODELS, reason="models/publish.py not implemented yet")
class TestPublishResponseInterface:
    """Interface: PublishResponse model fields and defaults."""

    def test_importable(self):
        assert PublishResponse is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(PublishResponse, BaseModel)

    def test_required_fields(self):
        resp = PublishResponse(
            job_id="job-123",
            platform=PublishPlatform.TWITTER,
            status="queued",
        )
        assert resp.job_id == "job-123"
        assert resp.platform == PublishPlatform.TWITTER
        assert resp.status == "queued"

    def test_platform_post_id_optional(self):
        resp = PublishResponse(
            job_id="job-123",
            platform=PublishPlatform.TWITTER,
            status="queued",
        )
        assert resp.platform_post_id is None

    def test_errors_defaults_empty(self):
        resp = PublishResponse(
            job_id="job-123",
            platform=PublishPlatform.TWITTER,
            status="queued",
        )
        assert resp.errors == []

    def test_has_created_at(self):
        resp = PublishResponse(
            job_id="job-123",
            platform=PublishPlatform.TWITTER,
            status="queued",
        )
        assert isinstance(resp.created_at, datetime)

    def test_errors_with_values(self):
        resp = PublishResponse(
            job_id="job-123",
            platform=PublishPlatform.TWITTER,
            status="failed",
            errors=["Rate limit exceeded"],
        )
        assert "Rate limit" in resp.errors[0]

    def test_platform_post_id_when_provided(self):
        resp = PublishResponse(
            job_id="job-123",
            platform=PublishPlatform.TWITTER,
            status="published",
            platform_post_id="tweet_98765",
        )
        assert resp.platform_post_id == "tweet_98765"

    def test_missing_job_id_raises(self):
        with pytest.raises(ValidationError):
            PublishResponse(platform=PublishPlatform.TWITTER, status="queued")

    def test_missing_platform_raises(self):
        with pytest.raises(ValidationError):
            PublishResponse(job_id="job-123", status="queued")

    def test_missing_status_raises(self):
        with pytest.raises(ValidationError):
            PublishResponse(job_id="job-123", platform=PublishPlatform.TWITTER)


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Serialization round-trip
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_MODELS, reason="models/publish.py not implemented yet")
class TestPublishModelsBehavior:
    """Behavioral: Model serialization and edge cases."""

    def test_credentials_serialization_roundtrip(self):
        creds = PlatformCredentials(
            platform=PublishPlatform.LINKEDIN,
            access_token="tok_secret",
            refresh_token="refresh_xyz",
            platform_user_id="user-42",
            is_active=True,
        )
        data = creds.model_dump()
        restored = PlatformCredentials(**data)
        assert restored.platform == creds.platform
        assert restored.access_token == creds.access_token
        assert restored.refresh_token == creds.refresh_token

    def test_request_serialization_roundtrip(self):
        req = PublishRequest(
            platform=PublishPlatform.MEDIUM,
            content="# Hello\n\nThis is markdown.",
            title="My Article",
            media_urls=["https://example.com/img.png"],
            options={"publish_status": "public", "tags": ["ai"]},
        )
        data = req.model_dump()
        restored = PublishRequest(**data)
        assert restored.platform == req.platform
        assert restored.options["publish_status"] == "public"

    def test_response_serialization_roundtrip(self):
        resp = PublishResponse(
            job_id="job-abc",
            platform=PublishPlatform.TWITTER,
            status="published",
            platform_post_id="tweet_123",
            errors=[],
        )
        data = resp.model_dump()
        restored = PublishResponse(**data)
        assert restored.job_id == resp.job_id
        assert restored.platform_post_id == "tweet_123"

    def test_response_json_serialization(self):
        import json

        resp = PublishResponse(
            job_id="job-abc",
            platform=PublishPlatform.LINKEDIN,
            status="queued",
        )
        json_str = resp.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["job_id"] == "job-abc"
        assert parsed["status"] == "queued"

    def test_credentials_with_expiry(self):
        exp = datetime(2026, 12, 31, 23, 59, 59)
        creds = PlatformCredentials(
            platform=PublishPlatform.LINKEDIN,
            access_token="tok_active",
            token_expiry=exp,
        )
        assert creds.token_expiry == exp

    def test_request_accepts_all_platforms(self):
        for platform in PublishPlatform:
            req = PublishRequest(platform=platform, content="Test")
            assert req.platform == platform
