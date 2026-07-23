"""Subscription and billing API endpoint (Stripe integration)."""

from __future__ import annotations

from fastapi import APIRouter, Header, Request

from app.models.subscription import (
    SubscriptionRequest,
    SubscriptionResponse,
    SubscriptionStatusResponse,
    WebhookEvent,
)


def create_subscription_router() -> APIRouter:
    """Create and return the subscription API router."""
    router = APIRouter(prefix="/api/v1", tags=["subscription"])

    @router.post("/subscription", response_model=SubscriptionResponse)
    async def create_subscription(
        request: SubscriptionRequest,
    ) -> SubscriptionResponse:
        """Create or update a user subscription.

        - No prior subscription -> free tier (5 repurposes/month)
        - Pro tier ($49/month) -> unlimited repurposes
        - Invalid tier -> 400
        """
        raise NotImplementedError(
            "Subscription creation not yet implemented"
        )

    @router.get("/subscription/status", response_model=SubscriptionStatusResponse)
    async def get_subscription_status(user_id: str) -> SubscriptionStatusResponse:
        """Get current subscription tier and usage for a user."""
        raise NotImplementedError(
            "Subscription status not yet implemented"
        )

    @router.post("/webhook")
    async def handle_webhook(
        request: Request,
        stripe_signature: str = Header(default=""),
    ) -> dict:
        """Handle Stripe webhook events.

        - invoice.payment_succeeded -> active
        - invoice.payment_failed -> past_due
        - customer.subscription.deleted -> downgrade to free
        - Invalid/missing signature -> 403
        """
        raise NotImplementedError(
            "Webhook handling not yet implemented"
        )

    return router


# Module-level router for direct import
router = create_subscription_router()
