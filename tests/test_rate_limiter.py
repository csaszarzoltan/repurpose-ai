"""Pre-dev tests for RateLimiter (Phase 1).

Source of truth: analysis/analysis-brief.md §4.9 RateLimiter.
Interface tests → xfail until services/rate_limiter.py is implemented.
"""

from __future__ import annotations

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.services.rate_limiter import RateLimiter

    HAS_RATE_LIMITER = True
except (ImportError, ModuleNotFoundError):
    HAS_RATE_LIMITER = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_RATE_LIMITER, reason="services/rate_limiter.py not implemented yet")
class TestRateLimiterInterface:
    """Interface: RateLimiter is importable and has expected API."""

    def test_importable(self):
        assert RateLimiter is not None

    def test_is_class(self):
        assert isinstance(RateLimiter, type)

    def test_init_accepts_max_calls_and_period(self):
        limiter = RateLimiter(max_calls=5, period=60.0)
        assert limiter is not None

    def test_init_defaults(self):
        limiter = RateLimiter()
        assert limiter is not None

    def test_has_check_method(self):
        assert hasattr(RateLimiter, "check")
        assert callable(RateLimiter.check)

    def test_has_consume_method(self):
        assert hasattr(RateLimiter, "consume")
        assert callable(RateLimiter.consume)

    def test_check_is_not_async(self):
        import inspect
        assert not inspect.iscoroutinefunction(RateLimiter.check)

    def test_consume_is_not_async(self):
        import inspect
        assert not inspect.iscoroutinefunction(RateLimiter.consume)


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Within limit
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_RATE_LIMITER, reason="services/rate_limiter.py not implemented yet")
class TestRateLimiterWithinLimit:
    """Behavioral: Within limit returns True."""

    @pytest.fixture
    def limiter(self):
        return RateLimiter(max_calls=10, period=60.0)

    def test_check_returns_true_within_limit(self, limiter):
        """Before any calls, check returns True."""
        assert limiter.check("linkedin") is True

    def test_consume_returns_true_within_limit(self, limiter):
        """Consume returns True while under limit."""
        for _ in range(5):
            assert limiter.consume("linkedin") is True

    def test_consume_up_to_limit(self, limiter):
        """Consume returns True up to max_calls."""
        for _ in range(10):
            assert limiter.consume("twitter") is True


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Over limit
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_RATE_LIMITER, reason="services/rate_limiter.py not implemented yet")
class TestRateLimiterOverLimit:
    """Behavioral: Over limit returns False with backoff."""

    @pytest.fixture
    def limiter(self):
        return RateLimiter(max_calls=3, period=60.0)

    def test_check_returns_false_when_over_limit(self, limiter):
        """After exhausting calls, check returns False."""
        for _ in range(3):
            limiter.consume("linkedin")
        assert limiter.check("linkedin") is False

    def test_consume_returns_false_when_over_limit(self, limiter):
        """After max_calls, consume returns False."""
        for _ in range(3):
            limiter.consume("twitter")
        assert limiter.consume("twitter") is False

    def test_consume_returns_false_on_exact_boundary(self, limiter):
        """At exactly max_calls+1, consume returns False."""
        for _ in range(3):
            limiter.consume("medium")
        # The 4th should return False
        assert limiter.consume("medium") is False


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Per-platform isolation
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_RATE_LIMITER, reason="services/rate_limiter.py not implemented yet")
class TestRateLimiterIsolation:
    """Behavioral: Rate limiting is isolated per platform."""

    @pytest.fixture
    def limiter(self):
        return RateLimiter(max_calls=2, period=60.0)

    def test_platforms_isolated(self, limiter):
        """Exhausting one platform does not affect another."""
        # Exhaust linkedin
        for _ in range(2):
            limiter.consume("linkedin")
        assert limiter.consume("linkedin") is False

        # Twitter should still be available
        assert limiter.consume("twitter") is True
        assert limiter.consume("twitter") is True
        assert limiter.consume("twitter") is False  # Now exhausted too

        # Medium should still be available
        assert limiter.consume("medium") is True

    def test_three_platforms_independent(self, limiter):
        """All three platforms have independent counters."""
        limiter.consume("linkedin")
        limiter.consume("twitter")
        limiter.consume("medium")
        # Second consume on each should still work (max_calls=2)
        assert limiter.consume("linkedin") is True
        assert limiter.consume("twitter") is True
        assert limiter.consume("medium") is True
        # Third should fail
        assert limiter.consume("linkedin") is False
        assert limiter.consume("twitter") is False
        assert limiter.consume("medium") is False


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Window reset
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_RATE_LIMITER, reason="services/rate_limiter.py not implemented yet")
class TestRateLimiterWindowReset:
    """Behavioral: After the period elapses, the counter resets."""

    def test_window_resets_after_period(self):
        """After period elapses, calls are allowed again."""
        limiter = RateLimiter(max_calls=1, period=0.01)  # Very short period
        import time

        # Exhaust
        limiter.consume("linkedin")
        assert limiter.consume("linkedin") is False
        # Wait for reset
        time.sleep(0.02)
        assert limiter.consume("linkedin") is True


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Edge cases
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_RATE_LIMITER, reason="services/rate_limiter.py not implemented yet")
class TestRateLimiterEdgeCases:
    """Behavioral: Edge cases for edge conditions."""

    def test_zero_max_calls(self):
        """max_calls=0 means no calls allowed."""
        limiter = RateLimiter(max_calls=0, period=60.0)
        assert limiter.check("linkedin") is False
        assert limiter.consume("linkedin") is False

    def test_very_large_limit(self):
        """Very large limits work without overflow."""
        limiter = RateLimiter(max_calls=10_000, period=60.0)
        for _ in range(100):
            assert limiter.consume("linkedin") is True
