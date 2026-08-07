"""Example: WordPress CMS publishing via the REST API.

Demonstrates:
  - WordPressPublisher.create_post with draft/publish status
  - Category and tag mapping
  - Featured image upload
  - Auto-generated excerpt (first-paragraph summary ≤160 chars)
  - Self-hosted vs WP.com site routing

Usage: PYTHONPATH=src .venv/bin/python examples/publish_wordpress.py

Requires:
  - WORDPRESS_CLIENT_ID and WORDPRESS_CLIENT_SECRET env vars (for OAuth2 token refresh)
  - A valid PlatformCredentials instance with a WordPress access_token
"""
from __future__ import annotations

import asyncio
import os

from app.models.publish import PlatformCredentials, PublishPlatform
from app.services.publishers.wordpress import WordPressPublisher


async def main() -> None:
    # ── 1. Create credentials ──
    # In production these come from the OAuth2 callback flow.
    # platform_user_id is the site URL — determines the REST API base.
    creds = PlatformCredentials(
        platform=PublishPlatform.WORDPRESS,
        access_token=os.getenv("WORDPRESS_ACCESS_TOKEN", "demo_token"),
        platform_user_id=os.getenv("WORDPRESS_SITE_URL", "https://mysite.wordpress.com"),
        options={},
    )
    print(f"WordPress credentials for site: {creds.platform_user_id}")

    publisher = WordPressPublisher()

    # ── 2. Derive excerpt from content (static method) ──
    long_content = (
        "Artificial intelligence is reshaping how we build software. "
        "From automated code review to intelligent test generation, "
        "LLMs are becoming a core part of the development workflow. "
        "This post explores practical applications you can adopt today."
    )
    excerpt = WordPressPublisher._derive_excerpt(long_content)
    print(f"Derived excerpt ({len(excerpt)} chars): {excerpt!r}")

    # ── 3. Build REST API payload (instance method, no HTTP call) ──
    payload = publisher._build_payload(
        content=long_content,
        title="AI in Software Development",
        status="draft",
        categories=[1, 5],
        tags=[10, 12],
        featured_media="42",
        excerpt="AI is transforming software development workflows.",
    )
    print(f"WordPress payload: {payload}")

    # ── 4. Site URL routing ──
    base_url = publisher._get_base_url(creds)
    print(f"REST API base URL: {base_url}")

    # For self-hosted WordPress, set platform_user_id to the site URL
    # and optionally override the token endpoint:
    self_hosted_creds = PlatformCredentials(
        platform=PublishPlatform.WORDPRESS,
        access_token="self_hosted_token",
        platform_user_id="https://mysite.example.com",
        options={"token_endpoint": "https://mysite.example.com/oauth/token"},
    )
    self_hosted_url = publisher._get_base_url(self_hosted_creds)
    print(f"Self-hosted REST API base: {self_hosted_url}")

    # ── 5. Auth URL (informational — shows the WP.com OAuth2 flow) ──
    client_id = os.getenv("WORDPRESS_CLIENT_ID", "")
    if client_id:
        print(f"WORDPRESS_CLIENT_ID is set: {client_id[:4]}...")
    else:
        print("WORDPRESS_CLIENT_ID not set — token refresh will use env fallback")

    print("\nWordPress publish example complete.")


if __name__ == "__main__":
    asyncio.run(main())
