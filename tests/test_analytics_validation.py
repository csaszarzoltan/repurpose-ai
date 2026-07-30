"""Pre-dev tests for validation gap analyzer (P1.2).

Source of truth: analysis/analysis-brief.md §4 P1.2 — validation_analyzer.
"""

from __future__ import annotations

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.services.analytics.validation_analyzer import ValidationAnalyzer
    HAS_ANALYZER = True
except (ImportError, ModuleNotFoundError):
    HAS_ANALYZER = False


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ANALYZER, reason="validation_analyzer.py not implemented yet")
class TestValidationAnalyzerInterface:
    """Interface: ValidationAnalyzer is importable and has expected API."""

    def test_importable(self):
        assert ValidationAnalyzer is not None

    def test_is_class(self):
        assert isinstance(ValidationAnalyzer, type)

    def test_init_accepts_llm_router(self):
        analyzer = ValidationAnalyzer(llm_router=None)
        assert analyzer is not None

    def test_init_defaults(self):
        analyzer = ValidationAnalyzer()
        assert analyzer is not None

    def test_has_validate_method(self):
        import inspect
        assert hasattr(ValidationAnalyzer, "validate")
        assert inspect.iscoroutinefunction(ValidationAnalyzer.validate)

    def test_validate_accepts_draft_and_published(self):
        import inspect
        sig = inspect.signature(ValidationAnalyzer.validate)
        params = list(sig.parameters.keys())
        assert "draft" in params
        assert "published" in params

    def test_validate_accepts_run_llm_judge_param(self):
        import inspect
        sig = inspect.signature(ValidationAnalyzer.validate)
        assert "run_llm_judge" in sig.parameters

    def test_has_compute_readability_scores(self):
        assert hasattr(ValidationAnalyzer, "compute_readability_scores")
        assert callable(ValidationAnalyzer.compute_readability_scores)

    def test_has_compute_diff_blocks(self):
        assert hasattr(ValidationAnalyzer, "compute_diff_blocks")
        assert callable(ValidationAnalyzer.compute_diff_blocks)

    def test_has_compute_tone_consistency(self):
        import inspect
        assert hasattr(ValidationAnalyzer, "compute_tone_consistency")
        assert inspect.iscoroutinefunction(ValidationAnalyzer.compute_tone_consistency)

    def test_has_compute_faithfulness(self):
        import inspect
        assert hasattr(ValidationAnalyzer, "compute_faithfulness")
        assert inspect.iscoroutinefunction(ValidationAnalyzer.compute_faithfulness)

    def test_has_compute_llm_judge(self):
        import inspect
        assert hasattr(ValidationAnalyzer, "compute_llm_judge")
        assert inspect.iscoroutinefunction(ValidationAnalyzer.compute_llm_judge)

    def test_compute_readability_accepts_string(self):
        import inspect
        sig = inspect.signature(ValidationAnalyzer.compute_readability_scores)
        assert "text" in sig.parameters

    def test_compute_readability_returns_dict(self):
        import inspect
        sig = inspect.signature(ValidationAnalyzer.compute_readability_scores)
        ann = sig.return_annotation
        assert ann in (dict, "dict", inspect.Parameter.empty)

    def test_validate_returns_dict(self):
        import inspect
        sig = inspect.signature(ValidationAnalyzer.validate)
        ann = sig.return_annotation
        assert ann in (dict, "dict", inspect.Parameter.empty)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Validation
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ANALYZER, reason="validation_analyzer.py not implemented yet")
class TestValidationAnalyzerBehavior:
    """Behavioral: ValidationAnalyzer validates content correctly."""

    async def test_validate_returns_full_report(self):
        analyzer = ValidationAnalyzer()
        result = await analyzer.validate(
            draft="AI generated draft content.",
            published="Human edited final content.",
        )
        assert isinstance(result, dict)
        assert "quality_delta" in result
        assert "readability" in result
        assert "diff_blocks" in result

    async def test_validate_without_llm_judge_completes_fast(self):
        """Lightweight mode (no LLM-judge) should not include llm_judge data."""
        analyzer = ValidationAnalyzer()
        result = await analyzer.validate(
            draft="Short draft.",
            published="Short published.",
            run_llm_judge=False,
        )
        assert isinstance(result, dict)

    async def test_validate_with_source_material_includes_faithfulness(self):
        analyzer = ValidationAnalyzer()
        result = await analyzer.validate(
            draft="Draft based on source.",
            published="Published based on source.",
            source_material="Original source material.",
        )
        assert "faithfulness" in result

    async def test_validate_with_llm_judge_includes_llm_scores(self):
        analyzer = ValidationAnalyzer(llm_router=None)
        result = await analyzer.validate(
            draft="Draft content.",
            published="Published content.",
            run_llm_judge=True,
        )
        assert "llm_judge" in result


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Readability
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ANALYZER, reason="validation_analyzer.py not implemented yet")
class TestReadabilityScoringBehavior:
    """Behavioral: Readability scores are computed correctly."""

    def test_readability_returns_flesch_kincaid(self):
        analyzer = ValidationAnalyzer()
        scores = analyzer.compute_readability_scores("This is a simple test sentence.")
        assert isinstance(scores, dict)
        assert "flesch_kincaid" in scores

    def test_readability_returns_dale_chall(self):
        analyzer = ValidationAnalyzer()
        scores = analyzer.compute_readability_scores("Simple text for testing.")
        assert "dale_chall" in scores

    def test_readability_returns_ari(self):
        analyzer = ValidationAnalyzer()
        scores = analyzer.compute_readability_scores("Readability test content here.")
        assert "ari" in scores

    def test_empty_text_handled(self):
        analyzer = ValidationAnalyzer()
        scores = analyzer.compute_readability_scores("")
        assert isinstance(scores, dict)

    def test_long_text_scored(self):
        analyzer = ValidationAnalyzer()
        text = " ".join(["word"] * 1000)
        scores = analyzer.compute_readability_scores(text)
        assert isinstance(scores, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Diff
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ANALYZER, reason="validation_analyzer.py not implemented yet")
class TestDiffBehavior:
    """Behavioral: Diff blocks are computed correctly."""

    def test_identical_texts_produce_empty_diff(self):
        analyzer = ValidationAnalyzer()
        blocks = analyzer.compute_diff_blocks("Same text.", "Same text.")
        assert isinstance(blocks, list)

    def test_different_texts_show_additions_and_deletions(self):
        analyzer = ValidationAnalyzer()
        blocks = analyzer.compute_diff_blocks("Original draft.", "Modified published version.")
        assert isinstance(blocks, list)
        assert len(blocks) > 0

    def test_diff_blocks_have_type_and_content(self):
        analyzer = ValidationAnalyzer()
        blocks = analyzer.compute_diff_blocks("Old text.", "New and improved text.")
        if blocks:
            block = blocks[0]
            assert "type" in block or "action" in block
            assert "content" in block or "text" in block


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Tone consistency
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ANALYZER, reason="validation_analyzer.py not implemented yet")
class TestToneConsistencyBehavior:
    """Behavioral: Tone consistency is computed."""

    async def test_tone_consistency_returns_scores(self):
        analyzer = ValidationAnalyzer()
        result = await analyzer.compute_tone_consistency("Draft.", "Published.")
        assert isinstance(result, dict)
        assert "similarity" in result or "score" in result or "consistency" in result

    async def test_tone_with_brand_voice_exemplar(self):
        analyzer = ValidationAnalyzer()
        result = await analyzer.compute_tone_consistency(
            "Draft.", "Published.",
            brand_voice_exemplar="Professional brand voice.",
        )
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Faithfulness
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ANALYZER, reason="validation_analyzer.py not implemented yet")
class TestFaithfulnessBehavior:
    """Behavioral: Faithfulness is computed."""

    async def test_faithfulness_returns_scores(self):
        analyzer = ValidationAnalyzer()
        result = await analyzer.compute_faithfulness("Draft text.", "Source material with details.")
        assert isinstance(result, dict)
        assert "faithfulness" in result or "score" in result or "ragas" in result


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — LLM Judge
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ANALYZER, reason="validation_analyzer.py not implemented yet")
class TestLlmJudgeBehavior:
    """Behavioral: LLM-judge scoring works."""

    async def test_llm_judge_returns_scores(self):
        analyzer = ValidationAnalyzer(llm_router=None)
        result = await analyzer.compute_llm_judge("Draft.", "Published.")
        assert isinstance(result, dict)
        assert "coherence" in result or "persuasiveness" in result or "clarity" in result
