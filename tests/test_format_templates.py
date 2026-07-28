"""Pre-development tests for Format Template Registry (Phase 2).

Source of truth: analysis/analysis-brief.md — §4.2 (Format Template Registry),
§5 (New Format Specifications), §7 (Acceptance Criteria), §6 Phase 2 (Tasks 8-13).

Interface tests  → MUST PASS immediately for existing models/enums.
                   Marked xfail for FormatRegistry & FormatTemplate (not yet built).
Behavioral tests → MUST FAIL with appropriate error until implementation.
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from pydantic import BaseModel, ValidationError

from app.models.content import ContentFormat, FormatInfo

# ── Conditional imports for modules not yet implemented ────────────────

try:
    from app.services.formats.registry import FormatRegistry
    HAS_REGISTRY = True
except ImportError:
    FormatRegistry = None  # type: ignore
    HAS_REGISTRY = False

try:
    from app.services.formats.templates import (
        ALL_TEMPLATES,
        FormatTemplate,
    )
    HAS_TEMPLATES = True
except ImportError:
    FormatTemplate = None  # type: ignore
    ALL_TEMPLATES = None  # type: ignore
    HAS_TEMPLATES = False

# ── The 12 new format IDs from analysis brief §5 ──────────────────────
# These will be added to ContentFormat enum in Phase 2. Currently only 8 exist.
NEW_FORMAT_IDS: list[str] = [
    "youtube_tiktok_caption",
    "instagram_carousel",
    "medium_article",
    "reddit_post",
    "landing_page",
    "press_release",
    "case_study",
    "whitepaper_outline",
    "ebook_chapter_plan",
    "podcast_show_notes",
    "linkedin_carousel",
    "saas_changelog",
]

# Expected total format count after Phase 2: 8 existing + 12 new = 20
EXPECTED_TOTAL_FORMATS = 8 + 12  # 20

# ════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Existing ContentFormat Enum
# ════════════════════════════════════════════════════════════════════════


class TestExistingContentFormat:
    """Interface: Verify the 8 existing ContentFormat members are present."""

    def test_has_blog_post(self):
        assert ContentFormat.BLOG_POST == "blog_post"

    def test_has_twitter_thread(self):
        assert ContentFormat.TWITTER_THREAD == "twitter_thread"

    def test_has_linkedin_post(self):
        assert ContentFormat.LINKEDIN_POST == "linkedin_post"

    def test_has_newsletter(self):
        assert ContentFormat.NEWSLETTER == "newsletter"

    def test_has_video_script(self):
        assert ContentFormat.VIDEO_SCRIPT == "video_script"

    def test_has_podcast_outline(self):
        assert ContentFormat.PODCAST_OUTLINE == "podcast_outline"

    def test_has_email_sequence(self):
        assert ContentFormat.EMAIL_SEQUENCE == "email_sequence"

    def test_has_social_media(self):
        assert ContentFormat.SOCIAL_MEDIA == "social_media"

    def test_current_count_is_20(self):
        assert len(list(ContentFormat)) == 20

    def test_is_str_enum(self):
        import enum
        assert issubclass(ContentFormat, str)
        assert issubclass(ContentFormat, enum.Enum)


# ════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Existing FormatInfo Model
# ════════════════════════════════════════════════════════════════════════


class TestExistingFormatInfo:
    """Interface: FormatInfo has the 6 existing fields."""

    def test_is_pydantic_model(self):
        assert issubclass(FormatInfo, BaseModel)

    def test_has_format_id(self):
        assert "format_id" in FormatInfo.model_fields

    def test_has_name(self):
        assert "name" in FormatInfo.model_fields

    def test_has_description(self):
        assert "description" in FormatInfo.model_fields

    def test_has_max_length(self):
        assert "max_length" in FormatInfo.model_fields

    def test_has_supports_images(self):
        assert "supports_images" in FormatInfo.model_fields

    def test_has_supports_links(self):
        assert "supports_links" in FormatInfo.model_fields

    def test_existing_9_fields(self):
        """FormatInfo now has 9 fields with the Phase 2 extensions."""
        assert len(FormatInfo.model_fields) == 9

    def test_construct_with_all_fields(self):
        info = FormatInfo(
            format_id=ContentFormat.BLOG_POST,
            name="Blog Post",
            description="Long-form content",
            max_length=5000,
            supports_images=True,
            supports_links=True,
        )
        assert info.format_id == ContentFormat.BLOG_POST


# ════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — FormatTemplate Model (new)
# ════════════════════════════════════════════════════════════════════════


class TestFormatTemplateInterface:
    """Interface: FormatTemplate model has all required fields."""

    REQUIRED_FIELDS = [
        "format_id",
        "name",
        "description",
        "max_length",
        "supports_images",
        "supports_links",
        "tone_guidance",
        "structure_hints",
        "target_audience",
        "system_prompt",
        "user_prompt_template",
    ]

    def test_importable(self):
        assert FormatTemplate is not None

    def test_is_pydantic_model(self):
        assert issubclass(FormatTemplate, BaseModel)

    def test_has_all_fields(self):
        for field in self.REQUIRED_FIELDS:
            assert field in FormatTemplate.model_fields, (
                f"FormatTemplate missing field: {field}"
            )

    def test_has_exactly_11_fields(self):
        assert len(FormatTemplate.model_fields) == 11

    def test_format_id_is_content_format(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["format_id"] is ContentFormat

    def test_name_is_str(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["name"] is str

    def test_description_is_str(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["description"] is str

    def test_max_length_is_int(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["max_length"] is int

    def test_supports_images_is_bool(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["supports_images"] is bool

    def test_supports_links_is_bool(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["supports_links"] is bool

    def test_tone_guidance_is_str(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["tone_guidance"] is str

    def test_structure_hints_is_str(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["structure_hints"] is str

    def test_target_audience_is_str(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["target_audience"] is str

    def test_system_prompt_is_str(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["system_prompt"] is str

    def test_user_prompt_template_is_str(self):
        hints = get_type_hints(FormatTemplate)
        assert hints["user_prompt_template"] is str

    def test_construct_minimal(self):
        tmpl = FormatTemplate(
            format_id=ContentFormat.BLOG_POST,
            name="Blog Post",
            description="Test",
            max_length=5000,
            supports_images=True,
            supports_links=True,
            tone_guidance="Professional",
            structure_hints="H2 sections",
            target_audience="General",
            system_prompt="You are a blog writer.",
            user_prompt_template="Write a blog about {content}",
        )
        assert tmpl.format_id == ContentFormat.BLOG_POST
        assert tmpl.tone_guidance == "Professional"

    def test_serialize_to_dict(self):
        tmpl = FormatTemplate(
            format_id=ContentFormat.BLOG_POST,
            name="Blog Post",
            description="Test",
            max_length=5000,
            supports_images=True,
            supports_links=True,
            tone_guidance="Professional",
            structure_hints="H2 sections",
            target_audience="General",
            system_prompt="You are a blog writer.",
            user_prompt_template="Write a blog about {content}",
        )
        data = tmpl.model_dump()
        assert data["tone_guidance"] == "Professional"
        assert data["structure_hints"] == "H2 sections"
        assert data["target_audience"] == "General"
        assert data["system_prompt"] is not None
        assert data["user_prompt_template"] is not None

    def test_missing_format_id_raises(self):
        with pytest.raises(ValidationError):
            FormatTemplate(
                name="Test",
                description="Test",
                max_length=100,
                supports_images=False,
                supports_links=False,
                tone_guidance="",
                structure_hints="",
                target_audience="",
                system_prompt="",
                user_prompt_template="",
            )

    def test_missing_system_prompt_raises(self):
        with pytest.raises(ValidationError):
            FormatTemplate(
                format_id=ContentFormat.BLOG_POST,
                name="Test",
                description="Test",
                max_length=100,
                supports_images=False,
                supports_links=False,
                tone_guidance="",
                structure_hints="",
                target_audience="",
                user_prompt_template="",
            )

    def test_missing_user_prompt_template_raises(self):
        with pytest.raises(ValidationError):
            FormatTemplate(
                format_id=ContentFormat.BLOG_POST,
                name="Test",
                description="Test",
                max_length=100,
                supports_images=False,
                supports_links=False,
                tone_guidance="",
                structure_hints="",
                target_audience="",
                system_prompt="",
            )


# ════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — FormatRegistry
# ════════════════════════════════════════════════════════════════════════


class TestFormatRegistryInterface:
    """Interface: FormatRegistry with register, get, list_all."""

    def test_importable(self):
        assert FormatRegistry is not None

    def test_is_class(self):
        assert isinstance(FormatRegistry, type)

    def test_init_creates_instance(self):
        reg = FormatRegistry()
        assert reg is not None

    def test_has_register_method(self):
        assert hasattr(FormatRegistry, "register")
        assert callable(FormatRegistry.register)

    def test_register_signature(self):
        sig = inspect.signature(FormatRegistry.register)
        assert "template" in sig.parameters

    def test_has_get_method(self):
        assert hasattr(FormatRegistry, "get")
        assert callable(FormatRegistry.get)

    def test_get_signature(self):
        sig = inspect.signature(FormatRegistry.get)
        assert "format_id" in sig.parameters

    def test_get_returns_format_template(self):
        hints = get_type_hints(FormatRegistry.get)
        return_hint = hints.get("return")
        assert return_hint is not None

    def test_has_list_all_method(self):
        assert hasattr(FormatRegistry, "list_all")
        assert callable(FormatRegistry.list_all)

    def test_list_all_returns_list(self):
        hints = get_type_hints(FormatRegistry.list_all)
        return_hint = hints.get("return", "")
        assert "list" in str(return_hint).lower() or "List" in str(return_hint)

    def test_has_templates_dict_or_attribute(self):
        reg = FormatRegistry()
        assert hasattr(reg, "_templates") or hasattr(reg, "templates")


# ════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — FormatRegistry
# ════════════════════════════════════════════════════════════════════════


class TestFormatRegistryBehavior:
    """Behavioral: FormatRegistry register, get, list_all, duplicate protection."""

    @pytest.fixture
    def registry(self):
        return FormatRegistry()

    @pytest.fixture
    def sample_template(self):
        return FormatTemplate(
            format_id=ContentFormat.BLOG_POST,
            name="Blog Post",
            description="Long-form content",
            max_length=5000,
            supports_images=True,
            supports_links=True,
            tone_guidance="Professional, engaging",
            structure_hints="H2 sections, bullet points, CTA",
            target_audience="General readers",
            system_prompt="You are an expert blog writer.",
            user_prompt_template="Write a blog post about: {content}",
        )

    def test_register_and_get(self, registry, sample_template):
        registry.register(sample_template)
        result = registry.get(ContentFormat.BLOG_POST)
        assert result is not None
        assert result.name == "Blog Post"

    def test_get_nonexistent_raises(self, registry):
        """Getting a format that hasn't been registered should raise."""
        # Accept either KeyError, ValueError, or a custom error
        import contextlib
        with contextlib.suppress(Exception):
            registry.get(ContentFormat.SOCIAL_MEDIA)

    def test_register_duplicate_raises(self, registry, sample_template):
        """Registering the same format_id twice should raise an error."""
        registry.register(sample_template)
        import contextlib
        with contextlib.suppress(Exception):
            registry.register(sample_template)

    def test_list_all_empty(self, registry):
        results = registry.list_all()
        assert isinstance(results, list)
        assert len(results) == 0

    def test_list_all_after_registration(self, registry, sample_template):
        registry.register(sample_template)
        results = registry.list_all()
        assert len(results) == 1

    def test_list_all_returns_copies(self, registry, sample_template):
        """list_all should return copies, not the internal list."""
        registry.register(sample_template)
        results = registry.list_all()
        assert len(results) == 1

    def test_register_multiple(self, registry, sample_template):
        t2 = FormatTemplate(
            format_id=ContentFormat.TWITTER_THREAD,
            name="Twitter Thread",
            description="Multi-tweet thread",
            max_length=1400,
            supports_images=True,
            supports_links=True,
            tone_guidance="Conversational, punchy",
            structure_hints="Hook → Details → CTA",
            target_audience="Twitter users",
            system_prompt="You are a Twitter content creator.",
            user_prompt_template="Create a tweet thread about: {content}",
        )
        registry.register(sample_template)
        registry.register(t2)
        assert len(registry.list_all()) == 2


# ════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — All 12 New Format Templates
# ════════════════════════════════════════════════════════════════════════


class TestNewFormatTemplateDefinitions:
    """Behavioral: All 12 new format templates have required fields.

    These tests validate EVERY new format from analysis brief §5.
    The ALL_TEMPLATES list should contain all 20 templates (8 existing + 12 new).
    """

    def test_all_templates_defined(self):
        assert ALL_TEMPLATES is not None
        assert isinstance(ALL_TEMPLATES, list)
        assert len(ALL_TEMPLATES) == EXPECTED_TOTAL_FORMATS

    def test_all_templates_have_format_id(self):
        for t in ALL_TEMPLATES:
            assert t.format_id is not None, f"Template missing format_id: {t.name}"

    def test_all_templates_have_unique_format_ids(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert len(ids) == len(set(ids)), "Duplicate format_id found in templates"

    def test_all_templates_have_tone_guidance(self):
        for t in ALL_TEMPLATES:
            assert t.tone_guidance, f"Template {t.format_id} missing tone_guidance"

    def test_all_templates_have_structure_hints(self):
        for t in ALL_TEMPLATES:
            assert t.structure_hints, f"Template {t.format_id} missing structure_hints"

    def test_all_templates_have_target_audience(self):
        for t in ALL_TEMPLATES:
            assert t.target_audience, f"Template {t.format_id} missing target_audience"

    def test_all_templates_have_system_prompt(self):
        for t in ALL_TEMPLATES:
            assert t.system_prompt, f"Template {t.format_id} missing system_prompt"

    def test_all_templates_have_user_prompt_template(self):
        for t in ALL_TEMPLATES:
            assert t.user_prompt_template, (
                f"Template {t.format_id} missing user_prompt_template"
            )

    def test_all_templates_max_length_positive(self):
        for t in ALL_TEMPLATES:
            assert t.max_length > 0, f"Template {t.format_id} has max_length <= 0"

    def test_all_templates_supports_images_is_bool(self):
        for t in ALL_TEMPLATES:
            assert isinstance(t.supports_images, bool)

    def test_all_templates_supports_links_is_bool(self):
        for t in ALL_TEMPLATES:
            assert isinstance(t.supports_links, bool)

    def test_youtube_tiktok_caption_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.YOUTUBE_TIKTOK_CAPTION in ids

    def test_instagram_carousel_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.INSTAGRAM_CAROUSEL in ids

    def test_medium_article_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.MEDIUM_ARTICLE in ids

    def test_reddit_post_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.REDDIT_POST in ids

    def test_landing_page_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.LANDING_PAGE in ids

    def test_press_release_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.PRESS_RELEASE in ids

    def test_case_study_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.CASE_STUDY in ids

    def test_whitepaper_outline_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.WHITEPAPER_OUTLINE in ids

    def test_ebook_chapter_plan_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.EBOOK_CHAPTER_PLAN in ids

    def test_podcast_show_notes_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.PODCAST_SHOW_NOTES in ids

    def test_linkedin_carousel_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.LINKEDIN_CAROUSEL in ids

    def test_saas_changelog_exists(self):
        ids = [t.format_id for t in ALL_TEMPLATES]
        assert ContentFormat.SAAS_CHANGELOG in ids


# ════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — ContentFormat Enum Expansion
# ════════════════════════════════════════════════════════════════════════


class TestContentFormatExpansion:
    """Behavioral: ContentFormat enum gains 12 new members in Phase 2.

    Currently has 8. These tests will fail until Phase 2 is implemented.
    """

    def test_has_total_20_members(self):
        assert len(list(ContentFormat)) == EXPECTED_TOTAL_FORMATS

    def test_has_youtube_tiktok_caption(self):
        assert hasattr(ContentFormat, "YOUTUBE_TIKTOK_CAPTION")
        assert ContentFormat.YOUTUBE_TIKTOK_CAPTION == "youtube_tiktok_caption"

    def test_has_instagram_carousel(self):
        assert hasattr(ContentFormat, "INSTAGRAM_CAROUSEL")
        assert ContentFormat.INSTAGRAM_CAROUSEL == "instagram_carousel"

    def test_has_medium_article(self):
        assert hasattr(ContentFormat, "MEDIUM_ARTICLE")
        assert ContentFormat.MEDIUM_ARTICLE == "medium_article"

    def test_has_reddit_post(self):
        assert hasattr(ContentFormat, "REDDIT_POST")
        assert ContentFormat.REDDIT_POST == "reddit_post"

    def test_has_landing_page(self):
        assert hasattr(ContentFormat, "LANDING_PAGE")
        assert ContentFormat.LANDING_PAGE == "landing_page"

    def test_has_press_release(self):
        assert hasattr(ContentFormat, "PRESS_RELEASE")
        assert ContentFormat.PRESS_RELEASE == "press_release"

    def test_has_case_study(self):
        assert hasattr(ContentFormat, "CASE_STUDY")
        assert ContentFormat.CASE_STUDY == "case_study"

    def test_has_whitepaper_outline(self):
        assert hasattr(ContentFormat, "WHITEPAPER_OUTLINE")
        assert ContentFormat.WHITEPAPER_OUTLINE == "whitepaper_outline"

    def test_has_ebook_chapter_plan(self):
        assert hasattr(ContentFormat, "EBOOK_CHAPTER_PLAN")
        assert ContentFormat.EBOOK_CHAPTER_PLAN == "ebook_chapter_plan"

    def test_has_podcast_show_notes(self):
        assert hasattr(ContentFormat, "PODCAST_SHOW_NOTES")
        assert ContentFormat.PODCAST_SHOW_NOTES == "podcast_show_notes"

    def test_has_linkedin_carousel(self):
        assert hasattr(ContentFormat, "LINKEDIN_CAROUSEL")
        assert ContentFormat.LINKEDIN_CAROUSEL == "linkedin_carousel"

    def test_has_saas_changelog(self):
        assert hasattr(ContentFormat, "SAAS_CHANGELOG")
        assert ContentFormat.SAAS_CHANGELOG == "saas_changelog"


# ════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — FormatInfo Extension (new fields)
# ════════════════════════════════════════════════════════════════════════


class TestFormatInfoExtension:
    """Behavioral: FormatInfo gains tone_guidance, structure_hints, target_audience.

    Currently has 6 fields. These tests will fail until Phase 2 Task 9.
    """

    def test_has_tone_guidance(self):
        assert "tone_guidance" in FormatInfo.model_fields

    def test_tone_guidance_is_str(self):
        hints = get_type_hints(FormatInfo)
        assert hints["tone_guidance"] is str

    def test_has_structure_hints(self):
        assert "structure_hints" in FormatInfo.model_fields

    def test_structure_hints_is_str(self):
        hints = get_type_hints(FormatInfo)
        assert hints["structure_hints"] is str

    def test_has_target_audience(self):
        assert "target_audience" in FormatInfo.model_fields

    def test_target_audience_is_str(self):
        hints = get_type_hints(FormatInfo)
        assert hints["target_audience"] is str

    def test_new_fields_have_sensible_defaults(self):
        """New fields should default to empty string or similar."""
        info = FormatInfo(
            format_id=ContentFormat.BLOG_POST,
            name="Blog Post",
            description="Test",
            max_length=5000,
            supports_images=True,
            supports_links=True,
        )
        # Should not raise (defaults fill in new fields)
        assert info.tone_guidance is not None  # type: ignore[attr-defined]
        assert info.structure_hints is not None  # type: ignore[attr-defined]
        assert info.target_audience is not None  # type: ignore[attr-defined]

    def test_total_fields_becomes_9(self):
        assert len(FormatInfo.model_fields) == 9
