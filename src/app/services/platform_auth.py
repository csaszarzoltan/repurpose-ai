"""Platform authentication service for OAuth2 flows."""
from __future__ import annotations

import os
import secrets
from contextlib import suppress
from datetime import datetime, timedelta

import httpx

from app.models.publish import PlatformCredentials, PublishPlatform


class PlatformAuthNotSupportedError(Exception):
    """Raised when a platform has no OAuth2 authorization flow (e.g. Ghost)."""


# Backward-compatible alias (pre-N818 name).
PlatformAuthNotSupported = PlatformAuthNotSupportedError


# Platform OAuth2 configuration
PLATFORM_AUTH_CONFIG: dict[str, dict[str, str]] = {
    "linkedin": {
        "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "revoke_url": "https://www.linkedin.com/oauth/v2/revoke",
        "client_id": "linkedin_client_id",
        "scope": "openid profile email w_member_social",
    },
    "twitter": {
        "auth_url": "https://twitter.com/i/oauth2/authorize",
        "token_url": "https://api.twitter.com/2/oauth2/token",
        "revoke_url": "https://api.twitter.com/2/oauth2/revoke",
        "client_id": "twitter_client_id",
        "scope": "tweet.read tweet.write users.read offline.access",
    },
    "medium": {
        "auth_url": "https://medium.com/m/oauth/authorize",
        "token_url": "https://api.medium.com/v1/tokens",
        "revoke_url": "https://api.medium.com/v1/tokens/revoke",
        "client_id": "medium_client_id",
        "scope": "basicProfile,listPublications,publishPost",
    },
    "instagram": {
        "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v19.0/oauth/access_token",
        "revoke_url": "https://graph.facebook.com/v19.0/oauth/authorize",
        # Client id/secret are secrets — resolved from the environment at
        # auth time (INSTAGRAM_CLIENT_ID / INSTAGRAM_CLIENT_SECRET) with a
        # placeholder fallback so the authorize URL stays well-formed even
        # before credentials are configured. See get_auth_url()/exchange_code().
        "client_id": "",
        "client_secret": "",
        "scope": "instagram_basic,instagram_content_publish,instagram_manage_insights",
    },
    "wordpress": {
        # WordPress.com Application OAuth2 (https://developer.wordpress.com/docs/oauth2/).
        # Client id/secret are secrets — resolved from the environment at auth
        # time (WORDPRESS_CLIENT_ID / WORDPRESS_CLIENT_SECRET), mirroring the
        # Instagram pattern below. Placeholders keep the authorize URL
        # well-formed before credentials are configured.
        "auth_url": "https://public-api.wordpress.com/oauth2/authorize",
        "token_url": "https://public-api.wordpress.com/oauth2/token",
        "revoke_url": "https://public-api.wordpress.com/oauth2/token",
        "client_id": "",
        "client_secret": "",
        "scope": "global",
    },
    "ghost": {
        # Ghost uses Admin API keys (JWT-signed), not OAuth2 — there is no
        # authorization URL. `get_auth_url` raises PlatformAuthNotSupported
        # for this platform; the API layer maps it to a clean 400.
        "auth_url": "",
        "token_url": "",
        "revoke_url": "",
        "client_id": "",
        "client_secret": "",
        "scope": "",
    },
}

# Env vars that supply real OAuth credentials for Instagram (Meta app).
_INSTAGRAM_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID", "")
_INSTAGRAM_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET", "")

# Env vars that supply real OAuth credentials for WordPress.com apps.
_WORDPRESS_CLIENT_ID = os.getenv("WORDPRESS_CLIENT_ID", "")
_WORDPRESS_CLIENT_SECRET = os.getenv("WORDPRESS_CLIENT_SECRET", "")


def _instagram_config() -> dict[str, str]:
    """Resolve the effective Instagram OAuth config (env override)."""
    cfg = dict(PLATFORM_AUTH_CONFIG["instagram"])
    if _INSTAGRAM_CLIENT_ID:
        cfg["client_id"] = _INSTAGRAM_CLIENT_ID
    if _INSTAGRAM_CLIENT_SECRET:
        cfg["client_secret"] = _INSTAGRAM_CLIENT_SECRET
    return cfg


def _wordpress_config() -> dict[str, str]:
    """Resolve the effective WordPress OAuth config (env override)."""
    cfg = dict(PLATFORM_AUTH_CONFIG["wordpress"])
    if _WORDPRESS_CLIENT_ID:
        cfg["client_id"] = _WORDPRESS_CLIENT_ID
    if _WORDPRESS_CLIENT_SECRET:
        cfg["client_secret"] = _WORDPRESS_CLIENT_SECRET
    return cfg


def _platform_config(platform: PublishPlatform) -> dict[str, str]:
    """Return the effective auth config for a platform (env-aware)."""
    if platform is PublishPlatform.INSTAGRAM:
        return _instagram_config()
    if platform is PublishPlatform.WORDPRESS:
        return _wordpress_config()
    return PLATFORM_AUTH_CONFIG[platform.value]


class PlatformAuthService:
    """OAuth2 authentication service for social platforms.

    Handles auth URL generation, token exchange, token refresh, and revocation.
    Stores credentials in-memory (dict per platform).
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._http = http_client or httpx.AsyncClient()
        self._credentials: dict[str, list[PlatformCredentials]] = {}

    # ── Auth URL generation (sync, no HTTP call) ────────────────────────────

    def get_auth_url(self, platform: PublishPlatform, redirect_uri: str) -> str:
        """Generate the OAuth2 authorization URL for a platform.

        Raises PlatformAuthNotSupported for platforms without an OAuth2
        authorization flow (e.g. Ghost, which uses Admin API keys).
        """
        config = _platform_config(platform)
        if not config["auth_url"]:
            raise PlatformAuthNotSupported(
                f"{platform.value} does not use OAuth2 — configure an API key instead (see /publish/{platform.value}/credentials)"
            )
        params = {
            "response_type": "code",
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "scope": config["scope"],
            "state": secrets.token_urlsafe(32),
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{config['auth_url']}?{query}"

    # ── Token exchange (async, HTTP POST) ───────────────────────────────────

    async def exchange_code(
        self,
        platform: PublishPlatform,
        code: str,
        redirect_uri: str,
    ) -> PlatformCredentials:
        """Exchange an authorization code for access+refresh tokens."""
        config = _platform_config(platform)
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": config["client_id"],
            "client_secret": config.get("client_secret", "client_secret_placeholder"),
        }

        response = await self._http.post(config["token_url"], data=data)
        response.raise_for_status()
        body = response.json()

        expires_in = body.get("expires_in", 3600)
        token_expiry = datetime.now() + timedelta(seconds=expires_in)

        creds = PlatformCredentials(
            platform=platform,
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token"),
            token_expiry=token_expiry,
        )

        # Store in memory
        self._credentials.setdefault(platform.value, []).append(creds)

        return creds

    # ── Token refresh (async, HTTP POST) ────────────────────────────────────

    async def refresh_credentials(self, credentials: PlatformCredentials) -> PlatformCredentials:
        """Refresh an expired token using its refresh token."""
        config = _platform_config(credentials.platform)
        data = {
            "grant_type": "refresh_token",
            "refresh_token": credentials.refresh_token or "",
            "client_id": config["client_id"],
            "client_secret": config.get("client_secret", "client_secret_placeholder"),
        }

        response = await self._http.post(config["token_url"], data=data)
        response.raise_for_status()
        body = response.json()

        expires_in = body.get("expires_in", 3600)
        token_expiry = datetime.now() + timedelta(seconds=expires_in)

        return PlatformCredentials(
            platform=credentials.platform,
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token", credentials.refresh_token),
            token_expiry=token_expiry,
        )

    # ── Token revocation (async, HTTP POST + remove from store) ─────────────

    async def revoke_credentials(self, platform: PublishPlatform) -> None:
        """Revoke tokens and remove stored credentials."""
        config = _platform_config(platform)
        data = {
            "token": "",
            "client_id": config["client_id"],
            "client_secret": config.get("client_secret", "client_secret_placeholder"),
        }

        with suppress(httpx.HTTPError):
            await self._http.post(config["revoke_url"], data=data)

        # Clear stored credentials
        self._credentials.pop(platform.value, None)
