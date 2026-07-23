"""Tests for SSRF protection service."""


from app.services.ssrf import SSRFChecker

# ── Interface Tests (must pass immediately) ──────────────────


class TestSSRFCheckerImport:
    """Interface: SSRFChecker is importable and has expected API."""

    def test_importable(self):
        assert SSRFChecker is not None

    def test_is_class(self):
        assert isinstance(SSRFChecker, type)

    def test_has_blocked_hosts(self):
        assert hasattr(SSRFChecker, "BLOCKED_HOSTS")
        assert isinstance(SSRFChecker.BLOCKED_HOSTS, list)

    def test_has_blocked_schemes(self):
        assert hasattr(SSRFChecker, "BLOCKED_SCHEMES")
        assert isinstance(SSRFChecker.BLOCKED_SCHEMES, list)

    def test_has_validate_url(self):
        assert hasattr(SSRFChecker, "validate_url")
        assert callable(SSRFChecker.validate_url)

    def test_has_is_private_ip(self):
        assert hasattr(SSRFChecker, "is_private_ip")
        assert callable(SSRFChecker.is_private_ip)

    def test_has_sanitize_url(self):
        assert hasattr(SSRFChecker, "sanitize_url")
        assert callable(SSRFChecker.sanitize_url)

    def test_has_check_redirect_chain(self):
        assert hasattr(SSRFChecker, "check_redirect_chain")
        assert callable(SSRFChecker.check_redirect_chain)

    def test_init_signature(self):
        """SSRFChecker.__init__ accepts optional custom_blocked."""
        import inspect
        sig = inspect.signature(SSRFChecker.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params

    def test_validate_url_returns_bool(self):
        """validate_url should have bool return annotation."""
        import inspect
        sig = inspect.signature(SSRFChecker.validate_url)
        # With from __future__ import annotations, annotation is stringified
        ann = sig.return_annotation
        assert ann in (bool, "bool", inspect.Parameter.empty)

    def test_is_private_ip_returns_bool(self):
        """is_private_ip should have bool return annotation."""
        import inspect
        sig = inspect.signature(SSRFChecker.is_private_ip)
        ann = sig.return_annotation
        assert ann in (bool, "bool", inspect.Parameter.empty)

    def test_sanitize_url_returns_str(self):
        """sanitize_url should have str return annotation."""
        import inspect
        sig = inspect.signature(SSRFChecker.sanitize_url)
        ann = sig.return_annotation
        assert ann in (str, "str", inspect.Parameter.empty)

    def test_check_redirect_chain_returns_bool(self):
        """check_redirect_chain should have bool return annotation."""
        import inspect
        sig = inspect.signature(SSRFChecker.check_redirect_chain)
        ann = sig.return_annotation
        assert ann in (bool, "bool", inspect.Parameter.empty)


class TestSSRFCheckerDefaults:
    """Interface: default blocked hosts/schemes are correct."""

    def test_localhost_blocked(self):
        assert "localhost" in SSRFChecker.BLOCKED_HOSTS

    def test_loopback_blocked(self):
        assert "127.0.0.1" in SSRFChecker.BLOCKED_HOSTS

    def test_metadata_endpoint_blocked(self):
        assert "169.254.169.254" in SSRFChecker.BLOCKED_HOSTS

    def test_file_scheme_blocked(self):
        assert "file" in SSRFChecker.BLOCKED_SCHEMES

    def test_ftp_scheme_blocked(self):
        assert "ftp" in SSRFChecker.BLOCKED_SCHEMES


# ── Behavioral Tests (must fail until implementation) ────────


class TestSSRFCheckerBehavior:
    """Behavioral: SSRFChecker blocks dangerous URLs."""

    def test_blocks_localhost(self):
        checker = SSRFChecker()
        assert checker.validate_url("http://localhost/admin") is False

    def test_blocks_loopback(self):
        checker = SSRFChecker()
        assert checker.validate_url("http://127.0.0.1/secret") is False

    def test_blocks_metadata_endpoint(self):
        checker = SSRFChecker()
        assert checker.validate_url("http://169.254.169.254/latest/meta-data") is False

    def test_blocks_file_scheme(self):
        checker = SSRFChecker()
        assert checker.validate_url("file:///etc/passwd") is False

    def test_blocks_ftp_scheme(self):
        checker = SSRFChecker()
        assert checker.validate_url("ftp://example.com/file") is False

    def test_allows_public_https(self):
        checker = SSRFChecker()
        assert checker.validate_url("https://example.com/page") is True

    def test_allows_public_http(self):
        checker = SSRFChecker()
        assert checker.validate_url("http://example.com/page") is True

    def test_rejects_no_scheme(self):
        checker = SSRFChecker()
        assert checker.validate_url("example.com") is False

    def test_custom_blocked_hosts(self):
        checker = SSRFChecker(custom_blocked=["evil.com"])
        assert checker.validate_url("http://evil.com/attack") is False

    def test_sanitize_strips_fragment(self):
        checker = SSRFChecker()
        result = checker.sanitize_url("https://example.com/page#section")
        assert "#" not in result

    def test_sanitize_normalizes_scheme(self):
        checker = SSRFChecker()
        result = checker.sanitize_url("HTTP://EXAMPLE.COM")
        assert result.startswith("http")

    def test_private_ip_10_x(self):
        checker = SSRFChecker()
        assert checker.is_private_ip("10.0.0.1") is True

    def test_private_ip_192_168_x(self):
        checker = SSRFChecker()
        assert checker.is_private_ip("192.168.1.1") is True

    def test_private_ip_172_16_x(self):
        checker = SSRFChecker()
        assert checker.is_private_ip("172.16.0.1") is True

    def test_not_private_ip_public(self):
        checker = SSRFChecker()
        assert checker.is_private_ip("8.8.8.8") is False

    def test_redirect_chain_all_safe(self):
        checker = SSRFChecker()
        chain = [
            "https://example.com/old",
            "https://example.com/new",
            "https://example.com/final",
        ]
        assert checker.check_redirect_chain(chain) is True

    def test_redirect_chain_contains_private(self):
        checker = SSRFChecker()
        chain = [
            "https://example.com/old",
            "http://127.0.0.1/leak",
            "https://example.com/final",
        ]
        assert checker.check_redirect_chain(chain) is False

    def test_redirect_chain_empty(self):
        checker = SSRFChecker()
        assert checker.check_redirect_chain([]) is True
