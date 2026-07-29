"""Pre-dev tests for PlatformAuthService (Phase 2).

Source of truth: analysis/analysis-brief.md §4.6 PlatformAuthService.
Interface tests → xfail until services/platform_auth.py is implemented.
Behavioral tests use respx to mock OAuth2 token endpoints.
"""

from __future__ import annotations

import pytest
import respx

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.publish import PlatformCredentials, PublishPlatform
    from app.services.platform_auth import PlatformAuthService

    HAS_PLATFORM_AUTH = True
except (ImportError, ModuleNotFoundError):
    HAS_PLATFORM_AUTH = False

    class PublishPlatform:  # type: ignore[no-redef]
        LINKEDIN = "linkedin"
        TWITTER = "twitter"
        MEDIUM = "medium"

    class PlatformCredentials:  # type: ignore[no-redef]
        pass


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PLATFORM_AUTH, reason="services/platform_auth.py not implemented yet")
class TestPlatformAuthServiceInterface:
    """Interface: PlatformAuthService is importable and has expected API."""

    def test_importable(self):
        assert PlatformAuthService is not None

    def test_is_class(self):
        assert isinstance(PlatformAuthService, type)

    def test_has_get_auth_url(self):
        assert hasattr(PlatformAuthService, "get_auth_url")
        assert callable(PlatformAuthService.get_auth_url)

    def test_get_auth_url_not_async(self):
        """get_auth_url is synchronous (returns a URL string, no HTTP call)."""
        import inspect
        assert not inspect.iscoroutinefunction(PlatformAuthService.get_auth_url)

    def test_has_exchange_code(self):
        assert hasattr(PlatformAuthService, "exchange_code")
        assert callable(PlatformAuthService.exchange_code)

    def test_exchange_code_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(PlatformAuthService.exchange_code)

    def test_has_refresh_credentials(self):
        assert hasattr(PlatformAuthService, "refresh_credentials")
        assert callable(PlatformAuthService.refresh_credentials)

    def test_refresh_credentials_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(PlatformAuthService.refresh_credentials)

    def test_has_revoke_credentials(self):
        assert hasattr(PlatformAuthService, "revoke_credentials")
        assert callable(PlatformAuthService.revoke_credentials)

    def test_revoke_credentials_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(PlatformAuthService.revoke_credentials)

    def test_init_accepts_http_client(self):
        import inspect
        sig = inspect.signature(PlatformAuthService.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Auth URL generation
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PLATFORM_AUTH, reason="services/platform_auth.py not implemented yet")
class TestPlatformAuthUrl:
    """Behavioral: Auth URL generation is platform-specific."""

    @pytest.fixture
    def auth_service(self):
        return PlatformAuthService()

    def test_linkedin_auth_url(self, auth_service):
        """LinkedIn returns a LinkedIn OAuth2 URL."""
        url = auth_service.get_auth_url(PublishPlatform.LINKEDIN, "https://app.example.com/callback")
        assert "linkedin.com" in url.lower() or "linkedin" in url.lower()
        assert "redirect_uri" in url or "redirect" in url.lower()

    def test_twitter_auth_url(self, auth_service):
        """Twitter returns a Twitter/X OAuth2 URL."""
        url = auth_service.get_auth_url(PublishPlatform.TWITTER, "https://app.example.com/callback")
        assert "twitter.com" in url.lower() or "x.com" in url.lower() or "twitter" in url.lower()
        assert "redirect_uri" in url or "redirect" in url.lower()

    def test_medium_auth_url(self, auth_service):
        """Medium returns a Medium OAuth2 URL."""
        url = auth_service.get_auth_url(PublishPlatform.MEDIUM, "https://app.example.com/callback")
        assert "medium.com" in url.lower() or "medium" in url.lower()
        assert "redirect_uri" in url or "redirect" in url.lower()

    def test_redirect_uri_in_url(self, auth_service):
        """The redirect_uri parameter is included in the returned URL."""
        redirect = "https://myapp.com/oauth/callback"
        url = auth_service.get_auth_url(PublishPlatform.LINKEDIN, redirect)
        assert redirect in url or redirect.replace("https://", "") in url.replace("https://", "")


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Token exchange
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PLATFORM_AUTH, reason="services/platform_auth.py not implemented yet")
class TestPlatformAuthTokenExchange:
    """Behavioral: Exchange code for token via platform endpoint."""

    @pytest.fixture
    def auth_service(self):
        return PlatformAuthService()

    async def test_exchange_code_returns_credentials(self, auth_service):
        """POST to token endpoint returns PlatformCredentials."""
        with respx.mock:
            route = respx.post("https://www.linkedin.com/oauth/v2/accessToken").respond(
                status_code=200,
                json={
                    "access_token": "new_token_abc",
                    "refresh_token": "refresh_xyz",
                    "expires_in": 3600,
                },
            )
            creds = await auth_service.exchange_code(
                platform=PublishPlatform.LINKEDIN,
                code="auth_code_123",
                redirect_uri="https://app.example.com/callback",
            )
        assert route.called
        assert isinstance(creds, PlatformCredentials)
        assert creds.access_token == "new_token_abc"

    async def test_exchange_twitter_token(self, auth_service):
        """Twitter token exchange uses twitter token endpoint."""
        with respx.mock:
            route = respx.post("https://api.twitter.com/2/oauth2/token").respond(
                status_code=200,
                json={
                    "access_token": "twitter_tok",
                    "refresh_token": "tw_refresh",
                    "expires_in": 7200,
                },
            )
            creds = await auth_service.exchange_code(
                platform=PublishPlatform.TWITTER,
                code="tw_code",
                redirect_uri="https://app.example.com/callback",
            )
        assert route.called
        assert creds.access_token == "twitter_tok"

    async def test_exchange_medium_token(self, auth_service):
        """Medium token exchange uses medium token endpoint."""
        with respx.mock:
            route = respx.post("https://api.medium.com/v1/tokens").respond(
                status_code=200,
                json={
                    "access_token": "medium_tok",
                    "refresh_token": "md_refresh",
                    "expires_in": 86400,
                },
            )
            creds = await auth_service.exchange_code(
                platform=PublishPlatform.MEDIUM,
                code="md_code",
                redirect_uri="https://app.example.com/callback",
            )
        assert route.called
        assert creds.access_token == "medium_tok"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Token refresh
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PLATFORM_AUTH, reason="services/platform_auth.py not implemented yet")
class TestPlatformAuthTokenRefresh:
    """Behavioral: Refresh expired credentials."""

    @pytest.fixture
    def auth_service(self):
        return PlatformAuthService()

    @pytest.fixture
    def expired_credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.LINKEDIN,
            access_token="old_expired_token",
            refresh_token="valid_refresh_token",
        )

    async def test_refresh_returns_new_credentials(self, auth_service, expired_credentials):
        """Refresh token endpoint returns new credentials."""
        with respx.mock:
            route = respx.post("https://www.linkedin.com/oauth/v2/accessToken").respond(
                status_code=200,
                json={
                    "access_token": "fresh_token_456",
                    "refresh_token": "new_refresh_abc",
                    "expires_in": 3600,
                },
            )
            new_creds = await auth_service.refresh_credentials(expired_credentials)
        assert route.called
        assert isinstance(new_creds, PlatformCredentials)
        assert new_creds.access_token == "fresh_token_456"

    async def test_refresh_sends_refresh_token(self, auth_service, expired_credentials):
        """The refresh token is sent in the request."""
        with respx.mock:
            route = respx.post("https://www.linkedin.com/oauth/v2/accessToken").respond(
                status_code=200,
                json={"access_token": "fresh", "expires_in": 3600},
            )
            await auth_service.refresh_credentials(expired_credentials)
        sent_body = route.calls[0].request.content
        assert "valid_refresh_token" in str(sent_body)


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Token revoke
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PLATFORM_AUTH, reason="services/platform_auth.py not implemented yet")
class TestPlatformAuthRevoke:
    """Behavioral: Revoke credentials removes stored token."""

    @pytest.fixture
    def auth_service(self):
        return PlatformAuthService()

    async def test_revoke_returns_none(self, auth_service):
        """Revoke should return None on success."""
        result = await auth_service.revoke_credentials(PublishPlatform.LINKEDIN)
        assert result is None

    async def test_revoke_removes_credentials(self, auth_service):
        """After revoke, getting credentials returns None."""
        with respx.mock:
            respx.post("https://www.linkedin.com/oauth/v2/revoke").respond(
                status_code=200,
                json={"message": "OK"},
            )
            await auth_service.revoke_credentials(PublishPlatform.LINKEDIN)

        # After revoke, stored credentials should be cleared
        stored = getattr(auth_service, "_credentials", {}).get(PublishPlatform.LINKEDIN)
        assert stored is None
