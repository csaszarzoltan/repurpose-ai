"""Regression tests for the publish-destinations wiring on /api/v1/repurpose.

Tech-lead finding B1 (task t_e227759f): the frontend repurpose page sends
``destinations: ["instagram"]`` in the payload, but ``RepurposeRequest`` had no
``destinations`` field and Pydantic v2 ``extra='ignore'`` dropped it silently —
a dead feature with silent data loss. These tests lock in the fixed contract:

* ``RepurposeRequest.destinations`` is a real field (default empty list).
* POST /api/v1/repurpose with destinations + stored active credentials invokes
  PublishService.publish() per destination (Graph API calls mocked with respx).
* A destination with no stored credentials produces a warning entry, and the
  repurpose itself still succeeds (200).
* An unknown destination value is rejected with 422.
* An empty destinations list preserves the legacy behavior (no publish calls).

Mock strategy mirrors tests/test_publish_api.py + test_publish_instagram.py:
httpx ASGITransport against the real app, respx for outbound Graph API calls.
"""
from __future__ import annotations

import respx
from httpx import ASGITransport, AsyncClient

from app.main import app

GRAPH_API = "https://graph.facebook.com/v19.0"
IG_USER_ID = "17841400123456789"

# Fallback credential used by the endpoint when none is stored (publish.py:43)
FALLBACK_IG_TOKEN = "no_token"


def _repurpose_payload(**overrides) -> dict:
    body = {
        "content": {
            "title": "AI in Healthcare",
            "body": "Artificial intelligence is transforming healthcare diagnostics.",
            "source_format": "blog_post",
            "tags": ["ai"],
        },
        "target_formats": ["twitter_thread"],
        "brand_voice": "professional",
    }
    body.update(overrides)
    return body


class TestRepurposeRequestDestinationsField:
    """Model contract: the destinations field must exist and default to empty."""

    def test_has_destinations_field(self):
        from app.models.content import RepurposeRequest

        assert "destinations" in RepurposeRequest.model_fields

    def test_destinations_defaults_to_empty_list(self):
        from app.models.content import RepurposeRequest

        item = {
            "content": {
                "title": "T",
                "body": "B" * 20,
                "source_format": "blog_post",
            },
            "target_formats": ["twitter_thread"],
        }
        req = RepurposeRequest.model_validate(item)
        assert req.destinations == []

    def test_destinations_parsed_from_payload(self):
        from app.models.content import RepurposeRequest

        item = {
            "content": {
                "title": "T",
                "body": "B" * 20,
                "source_format": "blog_post",
            },
            "target_formats": ["twitter_thread"],
            "destinations": ["instagram"],
        }
        req = RepurposeRequest.model_validate(item)
        assert req.destinations == ["instagram"]


class TestInstagramPlatformCapabilityClaim:
    """B2 regression: list_platforms must not claim unsupported 'story' posts."""

    async def test_instagram_platform_does_not_claim_story(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/publish/platforms")
        assert response.status_code == 200
        platforms = response.json()
        instagram = next(
            (p for p in platforms if p.get("name") == "instagram"), None
        )
        assert instagram is not None, "instagram platform missing from list"
        post_type = instagram.get("post_type", "")
        assert "story" not in post_type.lower()
        # The real supported types remain advertised
        for kind in ("image", "carousel", "reel"):
            assert kind in post_type.lower()


class TestRepurposeDestinationsPublishFlow:
    """End-to-end: destinations trigger PublishService against stored credentials."""

    async def test_repurpose_with_instagram_destination_publishes(self):
        """POST /api/v1/repurpose with destinations:["instagram"] + stored creds
        → Graph API publish invoked, response carries the per-destination status."""
        from app.api.publish import _auth_service
        from app.models.publish import PlatformCredentials

        _auth_service._credentials["instagram"] = [
            PlatformCredentials(
                platform="instagram",
                access_token="valid_ig_token_dest",
                platform_user_id=IG_USER_ID,
                is_active=True,
            )
        ]

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            with respx.mock:
                media_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                    status_code=200,
                    json={"id": "container_dest_123"},
                )
                publish_route = respx.post(
                    f"{GRAPH_API}/{IG_USER_ID}/media_publish"
                ).respond(
                    status_code=200,
                    json={"id": "post_dest_123"},
                )
                response = await client.post(
                    "/api/v1/repurpose",
                    json=_repurpose_payload(
                        destinations=["instagram"],
                        content={
                            "title": "AI in Healthcare",
                            "body": "Artificial intelligence is transforming healthcare diagnostics.",
                            "source_format": "blog_post",
                            "tags": ["ai"],
                            # The source content references media; the frontend
                            # repurpose payload has no media field today, but
                            # the wiring must forward media when present.
                            "media_url": "https://example.com/photo.jpg",
                        },
                    ),
                )

        assert response.status_code == 200
        data = response.json()
        assert data["repurposed"]["twitter_thread"]
        # The Graph API flow must actually have been invoked
        assert media_route.called, "container creation must be invoked"
        assert publish_route.called, "media_publish must be invoked"
        # The stored active credential (not the fallback) must have been used
        sent_json = media_route.calls[0].request.json()
        assert sent_json["access_token"] == "valid_ig_token_dest"
        assert sent_json["access_token"] != "no_token"
        # Publish warnings: only informational success lines, no failures
        assert not any("failed" in str(w).lower() for w in data["warnings"])
        assert any(
            "Published to instagram" in str(w) for w in data["warnings"]
        ), "expected per-destination publish status in warnings"

    async def test_no_credentials_destination_warns_but_succeeds(self):
        """Destination with no stored credentials → warning, repurpose still 200."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            with respx.mock:
                response = await client.post(
                    "/api/v1/repurpose",
                    json=_repurpose_payload(destinations=["instagram"]),
                )

        assert response.status_code == 200
        data = response.json()
        assert data["repurposed"]["twitter_thread"]
        assert any("instagram" in str(w) for w in data["warnings"])

    async def test_unknown_destination_returns_422(self):
        """Unknown platform value in destinations → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_repurpose_payload(destinations=["tiktok"]),
            )

        assert response.status_code == 422
        data = response.json()
        assert "tiktok" in str(data.get("detail", ""))

    async def test_empty_destinations_legacy_behavior_no_publish(self):
        """Empty destinations list → legacy behavior, no publish calls."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            with respx.mock:
                media_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media")
                media_publish_route = respx.post(
                    f"{GRAPH_API}/{IG_USER_ID}/media_publish"
                )
                response = await client.post(
                    "/api/v1/repurpose",
                    json=_repurpose_payload(destinations=[]),
                )

        assert response.status_code == 200
        data = response.json()
        assert data["repurposed"]["twitter_thread"]
        assert media_route.called is False
        assert media_publish_route.called is False

    async def test_mixed_destinations_unknown_first_still_422(self):
        """Unknown destination fails the whole request with 422 before any publish."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_repurpose_payload(
                    destinations=["instagram", "snapchat", "tiktok"]
                ),
            )

        assert response.status_code == 422
        data = response.json()
        detail = str(data.get("detail", ""))
        assert "snapchat" in detail or "tiktok" in detail
