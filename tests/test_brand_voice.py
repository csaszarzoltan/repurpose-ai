"""Tests for brand voice customization service."""


from app.models.content import BrandVoice
from app.services.brand_voice import BrandVoiceConfig

# ── Interface Tests (must pass immediately) ──────────────────


class TestBrandVoiceConfigImport:
    """Interface: BrandVoiceConfig is importable and has expected API."""

    def test_importable(self):
        assert BrandVoiceConfig is not None

    def test_is_class(self):
        assert isinstance(BrandVoiceConfig, type)

    def test_has_default_configs(self):
        assert hasattr(BrandVoiceConfig, "DEFAULT_CONFIGS")
        assert isinstance(BrandVoiceConfig.DEFAULT_CONFIGS, dict)

    def test_has_get_prompt_prefix(self):
        assert hasattr(BrandVoiceConfig, "get_prompt_prefix")
        assert callable(BrandVoiceConfig.get_prompt_prefix)

    def test_has_get_style_guide(self):
        assert hasattr(BrandVoiceConfig, "get_style_guide")
        assert callable(BrandVoiceConfig.get_style_guide)

    def test_has_adapt_text(self):
        assert hasattr(BrandVoiceConfig, "adapt_text")
        assert callable(BrandVoiceConfig.adapt_text)

    def test_has_validate_tone(self):
        assert hasattr(BrandVoiceConfig, "validate_tone")
        assert callable(BrandVoiceConfig.validate_tone)

    def test_has_merge_custom(self):
        assert hasattr(BrandVoiceConfig, "merge_custom")
        assert callable(BrandVoiceConfig.merge_custom)

    def test_init_signature(self):
        """BrandVoiceConfig.__init__ accepts optional voice."""
        import inspect
        sig = inspect.signature(BrandVoiceConfig.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params


class TestBrandVoiceConfigDefaults:
    """Interface: default configs cover core voices."""

    def test_professional_config_exists(self):
        assert BrandVoice.PROFESSIONAL in BrandVoiceConfig.DEFAULT_CONFIGS

    def test_casual_config_exists(self):
        assert BrandVoice.CASUAL in BrandVoiceConfig.DEFAULT_CONFIGS

    def test_humorous_config_exists(self):
        assert BrandVoice.HUMOROUS in BrandVoiceConfig.DEFAULT_CONFIGS

    def test_config_has_tone_key(self):
        cfg = BrandVoiceConfig.DEFAULT_CONFIGS[BrandVoice.PROFESSIONAL]
        assert "tone" in cfg

    def test_config_has_style_key(self):
        cfg = BrandVoiceConfig.DEFAULT_CONFIGS[BrandVoice.PROFESSIONAL]
        assert "style" in cfg

    def test_config_has_vocabulary_key(self):
        cfg = BrandVoiceConfig.DEFAULT_CONFIGS[BrandVoice.PROFESSIONAL]
        assert "vocabulary" in cfg


# ── Behavioral Tests (must fail until implementation) ────────


class TestBrandVoiceConfigBehavior:
    """Behavioral: BrandVoiceConfig customization logic."""

    def test_init_default_professional(self):
        config = BrandVoiceConfig()
        assert config.voice == BrandVoice.PROFESSIONAL

    def test_init_explicit_voice(self):
        config = BrandVoiceConfig(voice=BrandVoice.CASUAL)
        assert config.voice == BrandVoice.CASUAL

    def test_prompt_prefix_contains_voice_name(self):
        config = BrandVoiceConfig(voice=BrandVoice.PROFESSIONAL)
        prefix = config.get_prompt_prefix()
        assert isinstance(prefix, str)
        assert len(prefix) > 0

    def test_style_guide_returns_dict(self):
        config = BrandVoiceConfig()
        guide = config.get_style_guide()
        assert isinstance(guide, dict)
        assert "tone" in guide

    def test_style_guide_matches_voice(self):
        config = BrandVoiceConfig(voice=BrandVoice.CASUAL)
        guide = config.get_style_guide()
        assert guide.get("tone") == "informal"

    def test_adapt_text_returns_string(self):
        config = BrandVoiceConfig()
        result = config.adapt_text("Hello world")
        assert isinstance(result, str)

    def test_adapt_text_changes_content(self):
        config = BrandVoiceConfig(voice=BrandVoice.HUMOROUS)
        result = config.adapt_text("This is important information")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_validate_tone_returns_tuple(self):
        config = BrandVoiceConfig()
        result = config.validate_tone("Some text")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_validate_tone_returns_bool_and_list(self):
        config = BrandVoiceConfig()
        is_valid, issues = config.validate_tone("Professional business content")
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)

    def test_merge_custom_updates_config(self):
        config = BrandVoiceConfig(voice=BrandVoice.PROFESSIONAL)
        config.merge_custom({"tone": "aggressive"})
        guide = config.get_style_guide()
        assert guide.get("tone") == "aggressive"

    def test_merge_custom_preserves_other_keys(self):
        config = BrandVoiceConfig(voice=BrandVoice.PROFESSIONAL)
        config.merge_custom({"tone": "aggressive"})
        guide = config.get_style_guide()
        assert "style" in guide
        assert guide.get("style") == "business"

    def test_different_voices_different_prefixes(self):
        prof = BrandVoiceConfig(voice=BrandVoice.PROFESSIONAL)
        casual = BrandVoiceConfig(voice=BrandVoice.CASUAL)
        assert prof.get_prompt_prefix() != casual.get_prompt_prefix()
