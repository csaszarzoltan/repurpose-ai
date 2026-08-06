"""Platform authentication service for OAuth2 flows."""
from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timedelta

import httpx

from app.models.publish import PlatformCredentials, PublishPlatform

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
        "client_id": "",
        "scope": "instagram_basic,instagram_content_publish,instagram_manage_insights",
    },
}


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
        """Generate the OAuth2 authorization URL for a platform."""
        config = PLATFORM_AUTH_CONFIG[platform.value]
        params = {
            "response_type": "code",
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "scope": config["scope"],
            "state": "state_placeholder",
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
        config = PLATFORM_AUTH_CONFIG[platform.value]
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": config["client_id"],
            "client_secret": "client_secret_placeholder",
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
        config = PLATFORM_AUTH_CONFIG[credentials.platform.value]
        data = {
            "grant_type": "refresh_token",
            "refresh_token": credentials.refresh_token or "",
            "client_id": config["client_id"],
            "client_secret": "client_secret_placeholder",
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
        config = PLATFORM_AUTH_CONFIG[platform.value]
        data = {
            "token": "",
            "client_id": config["client_id"],
            "client_secret": "client_secret_placeholder",
        }

        with suppress(httpx.HTTPError):
            await self._http.post(config["revoke_url"], data=data)

        # Clear stored credentials
        self._credentials.pop(platform.value, None)
