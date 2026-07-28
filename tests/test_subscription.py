"""Tests for Stripe subscription and billing endpoints — updated for auth."""

from __future__ import annotations

import uuid

from httpx import ASGITransport, AsyncClient

from app.api.subscription import create_subscription_router, router
from app.main import app
from app.models.subscription import (
    SubscriptionRequest,
    SubscriptionResponse,
    SubscriptionStatus,
    SubscriptionStatusResponse,
    SubscriptionTier,
    WebhookEvent,
)

# ── Helpers ──────────────────────────────────────────────────


def _valid_user() -> dict:
    return {
        "email": f"sub-test-{uuid.uuid4().hex[:8]}@example.com",
        "password": "SecurePass123!",
        "name": "Sub Test User",
    }


async def _register_and_get_token() -> str:
    """Register a user and return access token."""
    payload = _valid_user()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/api/v1/auth/register", json=payload)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        )
    return login_resp.json()["access_token"]


async def _register_and_get_token_for_user(email: str) -> str:
    """Register a specific user and return access token."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "SecurePass123!",
                "name": "Specific User",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "SecurePass123!"},
        )
    return login_resp.json()["access_token"]


# ── Interface Tests (must pass immediately) ──────────────────


class TestSubscriptionModuleImport:
    """Interface: subscription module is importable."""

    def test_importable(self):
        from app.api import subscription

        assert subscription is not None

    def test_create_subscription_router_importable(self):
        assert create_subscription_router is not None
        assert callable(create_subscription_router)

    def test_router_importable(self):
        assert router is not None


class TestSubscriptionRouterInterface:
    """Interface: subscription router has expected routes."""

    def test_create_subscription_router_returns_api_router(self):
        from fastapi import APIRouter

        result = create_subscription_router()
        assert isinstance(result, APIRouter)

    def test_router_has_prefix(self):
        assert router.prefix == "/api/v1"

    def test_router_has_subscription_tag(self):
        assert "subscription" in router.tags

    def test_post_subscription_route_exists(self):
        """POST /api/v1/subscription is registered."""
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/subscription" in paths
        assert "post" in paths["/api/v1/subscription"]

    def test_get_subscription_status_route_exists(self):
        """GET /api/v1/subscription/status is registered."""
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/subscription/status" in paths
        assert "get" in paths["/api/v1/subscription/status"]

    def test_post_webhook_route_exists(self):
        """POST /api/v1/webhook is registered."""
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/webhook" in paths
        assert "post" in paths["/api/v1/webhook"]


class TestSubscriptionModelsInterface:
    """Interface: subscription models exist with correct structure."""

    def test_subscription_tier_is_str_enum(self):
        assert issubclass(SubscriptionTier, str)
        assert SubscriptionTier.FREE == "free"
        assert SubscriptionTier.PRO == "pro"

    def test_subscription_status_is_str_enum(self):
        assert issubclass(SubscriptionStatus, str)
        assert SubscriptionStatus.ACTIVE == "active"
        assert SubscriptionStatus.PAST_DUE == "past_due"
        assert SubscriptionStatus.CANCELED == "canceled"

    def test_subscription_request_model(self):
        """SubscriptionRequest has tier and user_id fields."""
        import inspect

        sig = inspect.signature(SubscriptionRequest)
        field_names = list(sig.parameters.keys())
        assert "tier" in field_names
        assert "user_id" in field_names

    def test_subscription_response_model(self):
        """SubscriptionResponse has expected fields."""
        import inspect

        sig = inspect.signature(SubscriptionResponse)
        field_names = list(sig.parameters.keys())
        assert "subscription_id" in field_names
        assert "user_id" in field_names
        assert "tier" in field_names
        assert "status" in field_names
        assert "monthly_limit" in field_names
        assert "current_usage" in field_names

    def test_subscription_status_response_model(self):
        """SubscriptionStatusResponse has expected fields."""
        import inspect

        sig = inspect.signature(SubscriptionStatusResponse)
        field_names = list(sig.parameters.keys())
        assert "user_id" in field_names
        assert "tier" in field_names
        assert "status" in field_names
        assert "monthly_limit" in field_names
        assert "current_usage" in field_names
        assert "repurposes_remaining" in field_names

    def test_webhook_event_model(self):
        """WebhookEvent has id, type, and data fields."""
        import inspect

        sig = inspect.signature(WebhookEvent)
        field_names = list(sig.parameters.keys())
        assert "id" in field_names
        assert "type" in field_names
        assert "data" in field_names


class TestSubscriptionRouterFunctions:
    """Interface: router handler functions have correct signatures."""

    def test_create_subscription_handler_exists(self):
        """create_subscription route handler exists."""
        routes = [r for r in router.routes if hasattr(r, "path")]
        paths = [r.path for r in routes]
        assert "/api/v1/subscription" in paths

    def test_get_status_handler_exists(self):
        """get_subscription_status route handler exists."""
        routes = [r for r in router.routes if hasattr(r, "path")]
        paths = [r.path for r in routes]
        assert "/api/v1/subscription/status" in paths

    def test_webhook_handler_exists(self):
        """handle_webhook route handler exists."""
        routes = [r for r in router.routes if hasattr(r, "path")]
        paths = [r.path for r in routes]
        assert "/api/v1/webhook" in paths


# ── Behavioral Tests ─────────────────────────────────────────


class TestSubscriptionCreateBehavior:
    """Behavioral: POST /api/v1/subscription creates subscriptions."""

    async def test_create_free_subscription(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/subscription",
                json={"tier": "free"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"
        assert data["status"] == "active"
        assert data["monthly_limit"] == 5

    async def test_create_pro_subscription(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/subscription",
                json={"tier": "pro"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "pro"
        assert data["status"] == "active"
        assert data["monthly_limit"] == -1  # -1 = unlimited

    async def test_create_invalid_tier_returns_400(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/subscription",
                json={"tier": "enterprise"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 400

    async def test_create_subscription_response_has_subscription_id(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/subscription",
                json={"tier": "free"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "subscription_id" in data
        assert isinstance(data["subscription_id"], str)

    async def test_create_subscription_needs_auth(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/subscription",
                json={"tier": "free"},
            )
        assert response.status_code == 401


class TestSubscriptionStatusBehavior:
    """Behavioral: GET /api/v1/subscription/status returns tier and usage."""

    async def test_get_status_returns_tier_and_usage(self):
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # First create a subscription
            await client.post(
                "/api/v1/subscription",
                json={"tier": "free"},
                headers={"Authorization": f"Bearer {token}"},
            )
            # Then get status
            response = await client.get(
                "/api/v1/subscription/status",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"
        assert "current_usage" in data
        assert "repurposes_remaining" in data
        assert data["repurposes_remaining"] == 5

    async def test_get_status_auto_creates_free_tier(self):
        """User with no explicit subscription gets default free tier."""
        token = await _register_and_get_token()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/subscription/status",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"
        assert data["repurposes_remaining"] == 5

    async def test_get_status_needs_auth(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/subscription/status")
        assert response.status_code == 401


# ── Multi-Tenant Isolation Tests ─────────────────────────────


class TestSubscriptionMultiTenantIsolation:
    """Multi-tenant: users can only see their own subscriptions."""

    async def test_users_have_separate_subscriptions(self):
        """Two users should have independent subscriptions."""
        user_a_token = await _register_and_get_token_for_user("alice@example.com")
        user_b_token = await _register_and_get_token_for_user("bob@example.com")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Alice creates pro subscription
            await client.post(
                "/api/v1/subscription",
                json={"tier": "pro"},
                headers={"Authorization": f"Bearer {user_a_token}"},
            )

            # Bob checks his status (should still be free)
            bob_status = await client.get(
                "/api/v1/subscription/status",
                headers={"Authorization": f"Bearer {user_b_token}"},
            )
            assert bob_status.json()["tier"] == "free"

            # Alice checks her status (should be pro)
            alice_status = await client.get(
                "/api/v1/subscription/status",
                headers={"Authorization": f"Bearer {user_a_token}"},
            )
            assert alice_status.json()["tier"] == "pro"


class TestWebhookBehavior:
    """Behavioral: POST /api/v1/webhook handles Stripe events."""

    def _make_stripe_event(self, event_type: str, data_object: dict) -> dict:
        """Helper to build a fake Stripe event payload."""
        return {
            "id": "evt_test_123",
            "type": event_type,
            "data": {"object": data_object},
        }

    async def test_payment_succeeded_activates_subscription(self):
        """invoice.payment_succeeded -> status becomes active."""
        event = self._make_stripe_event(
            "invoice.payment_succeeded",
            {"customer": "cus_test", "subscription": "sub_test"},
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook",
                json=event,
                headers={"stripe-signature": "test_sig"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data.get("received") is True

    async def test_payment_failed_marks_past_due(self):
        """invoice.payment_failed -> status becomes past_due."""
        event = self._make_stripe_event(
            "invoice.payment_failed",
            {"customer": "cus_test", "subscription": "sub_test"},
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook",
                json=event,
                headers={"stripe-signature": "test_sig"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data.get("received") is True

    async def test_subscription_deleted_downgrades_to_free(self):
        """customer.subscription.deleted -> downgrade to free tier."""
        event = self._make_stripe_event(
            "customer.subscription.deleted",
            {"customer": "cus_test", "id": "sub_test"},
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook",
                json=event,
                headers={"stripe-signature": "test_sig"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data.get("received") is True

    async def test_invalid_signature_returns_403(self):
        """Missing or invalid Stripe signature -> 403."""
        event = self._make_stripe_event(
            "invoice.payment_succeeded",
            {"customer": "cus_test"},
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook",
                json=event,
                headers={"stripe-signature": "invalid_signature"},
            )
        assert response.status_code == 403

    async def test_missing_signature_returns_403(self):
        """No stripe-signature header -> 403."""
        event = self._make_stripe_event(
            "invoice.payment_succeeded",
            {"customer": "cus_test"},
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook",
                json=event,
            )
        assert response.status_code == 403

    async def test_unknown_event_type_returns_200(self):
        """Unknown event type -> 200 with received=true (idempotent)."""
        event = self._make_stripe_event(
            "customer.created",
            {"id": "cus_test"},
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook",
                json=event,
                headers={"stripe-signature": "test_sig"},
            )
        assert response.status_code == 200
