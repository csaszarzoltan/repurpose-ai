"""Example: Ghost CMS publishing via the Admin API.

Demonstrates:
  - GhostPublisher.create_post with draft/published status
  - Tag mapping (options.tags as [{name: ...}])
  - Featured image URL (SSRF-checked on upload)
  - Mobiledoc content formatting (0.3.1 format)
  - JWT authentication (id:secret → HMAC-signed JWT)

Usage: PYTHONPATH=src .venv/bin/python examples/publish_ghost.py

Requires:
  - A valid PlatformCredentials instance with a Ghost Admin API key
    (format: "id:secret", stored as access_token)
"""
from __future__ import annotations

import asyncio
import os

from app.models.publish import PlatformCredentials, PublishPlatform
from app.services.publishers.ghost import GhostPublisher


async def main() -> None:
    # ── 1. Create credentials ──
    # Ghost Admin API key format: "id:secret" — stored as access_token.
    # No OAuth flow: PUT /publish/ghost/credentials to store the key.
    api_key = os.getenv("GHOST_ADMIN_API_KEY", "demo_id:demo_secret")
    creds = PlatformCredentials(
        platform=PublishPlatform.GHOST,
        access_token=api_key,
        platform_user_id=os.getenv("GHOST_SITE_URL", "https://mysite.ghost.io"),
    )
    print(f"Ghost credentials for site: {creds.platform_user_id}")

    publisher = GhostPublisher()

    # ── 2. Build payload (instance method, no HTTP call) ──
    payload = publisher._build_payload(
        title="AI in Software Development",
        content="Artificial intelligence is reshaping how we build software.",
        status="draft",
        tags=[{"name": "tech"}, {"name": "ai"}],
        feature_image="https://example.com/ai-cover.png",
    )
    print(f"Ghost payload: {payload}")

    # ── 3. Build JWT (demonstrates HMAC signing) ──
    jwt_token = await publisher._build_jwt(api_key=api_key)
    print(f"JWT token (first 40 chars): {jwt_token[:40]}...")

    headers = publisher._build_headers(jwt_token)
    print(f"Request headers: {headers}")

    # ── 4. Auth endpoint behavior ──
    # GET /publish/ghost/auth-url returns 400 — Ghost uses API key auth, not OAuth2.
    print("\nNote: Ghost does not support OAuth2.")
    print("Store the Admin API key directly:")
    print('  curl -X PUT .../publish/ghost/credentials \\')
    print('    -d \'{"platform": "ghost", "access_token": "YOUR_KEY", "is_active": true}\'')

    print("\nGhost publish example complete.")


if __name__ == "__main__":
    asyncio.run(main())
