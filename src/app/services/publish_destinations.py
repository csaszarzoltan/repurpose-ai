"""Publish-destinations step for the repurpose flow.

The repurpose page lets the user pick one or more publish destinations
(e.g. ``["instagram"]``). After content is repurposed, each destination is
resolved to a :class:`PublishPlatform` and published with the stored active
credentials (the same lookup used by the publish API endpoint).

Error contract (from the tech-lead review, task t_e227759f):

* unknown destination value → raises ``ValueError`` (the API maps it to 422);
* destination with no stored credentials → warning entry, repurpose still
  succeeds (do NOT fail the whole repurpose);
* publish failure for a destination → warning entry, repurpose still succeeds.
"""
from __future__ import annotations

import logging

from app.models.publish import (
    PlatformCredentials,
    PublishPlatform,
    PublishRequest,
    PublishResponse,
)
from app.services.platform_auth import PlatformAuthService
from app.services.publish import PublishService

logger = logging.getLogger(__name__)

# Module-level singletons matching the publish API module (publish.py) — the
# credential store is shared in-memory state across the app.
_publish_service = PublishService()
_auth_service = PlatformAuthService()


def get_active_credentials(
    auth_service: PlatformAuthService, platform: PublishPlatform
) -> PlatformCredentials | None:
    """Return the first active stored credential for ``platform``, else None.

    Mirrors the lookup in src/app/api/publish.py (handle_publish). Unlike that
    endpoint there is deliberately NO fallback dummy credential: a destination
    without real stored credentials must surface as a warning, not silently
    publish with a placeholder token.
    """
    stored = getattr(auth_service, "_credentials", {}).get(platform.value, [])
    for cred in stored:
        if cred.is_active:
            return cred
    return None


async def publish_to_destinations(
    destinations: list[str],
    content: str,
    *,
    title: str | None = None,
    media_urls: list[str] | None = None,
    publish_service: PublishService | None = None,
    auth_service: PlatformAuthService | None = None,
) -> list[tuple[str, PublishResponse]]:
    """Publish ``content`` to every requested destination.

    ``media_urls`` is forwarded to image-driven platforms (Instagram IMAGE
    posts). Returns a list of ``(platform_name, response)`` for the
    destinations that had stored credentials and were dispatched (including
    failed publishes — the caller decides how to surface them). Raises
    ``ValueError`` for an unknown destination value before any publish is
    attempted.
    """
    svc = publish_service or _publish_service
    auth = auth_service or _auth_service

    published: list[tuple[str, PublishResponse]] = []
    for destination in destinations:
        try:
            platform = PublishPlatform(destination.lower())
        except ValueError:
            raise ValueError(f"Unknown publish destination: {destination}") from None

        creds = get_active_credentials(auth, platform)
        if creds is None:
            logger.warning("No stored credentials for destination '%s', skipping publish", destination)
            continue

        request = PublishRequest(
            platform=platform,
            content=content,
            title=title,
            media_urls=media_urls or [],
        )
        response = await svc.publish(request, creds)
        published.append((platform.value, response))

    return published


def summarize_publish_results(
    published: list[tuple[str, PublishResponse]],
) -> list[str]:
    """Build human-readable per-destination status lines for ``RepurposeResponse.warnings``.

    A failed publish is recorded as a warning (the repurpose result itself is
    not failed); a successful publish is informational and included so the
    response is self-describing.
    """
    lines: list[str] = []
    for platform_name, response in published:
        if response.status == "published":
            lines.append(
                f"Published to {platform_name}"
                + (f" (post id: {response.platform_post_id})" if response.platform_post_id else "")
            )
        else:
            errors = "; ".join(response.errors) if response.errors else response.status
            lines.append(f"Publish to {platform_name} failed: {errors}")
    return lines
