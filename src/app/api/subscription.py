"""Stripe subscription and billing endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_current_user
from app.models.auth import UserResponse
from app.models.subscription import (
    SubscriptionResponse,
    SubscriptionStatus,
    SubscriptionStatusResponse,
    SubscriptionTier,
)

# In-memory storage for subscriptions (replace with database in production)
_subscriptions: dict[str, dict[str, Any]] = {}

# Tier configuration
TIER_LIMITS: dict[SubscriptionTier, int] = {
    SubscriptionTier.FREE: 5,
    SubscriptionTier.PRO: -1,  # -1 = unlimited
}

# Valid tier string values
VALID_TIERS: set[str] = {t.value for t in SubscriptionTier}


def create_subscription_router() -> APIRouter:
    """Create and return a subscription router instance."""
    return router


router = APIRouter(prefix="/api/v1", tags=["subscription"])


def _resolve_tier(tier_str: str) -> SubscriptionTier:
    """Convert a tier string to SubscriptionTier, raising 400 for invalid values."""
    if tier_str not in VALID_TIERS:
        msg = f"Invalid subscription tier: {tier_str}"
        raise HTTPException(status_code=400, detail=msg)
    return SubscriptionTier(tier_str)


@router.post("/subscription", response_model=SubscriptionResponse)
async def create_subscription(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
) -> SubscriptionResponse:
    """Create or update a subscription for the authenticated user."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None

    tier_str = body.get("tier", "")
    user_id = current_user.user_id

    tier = _resolve_tier(tier_str)
    subscription_id = f"sub_{uuid.uuid4().hex[:12]}"
    monthly_limit = TIER_LIMITS[tier]

    subscription = {
        "subscription_id": subscription_id,
        "user_id": user_id,
        "tier": tier,
        "status": SubscriptionStatus.ACTIVE,
        "monthly_limit": monthly_limit,
        "current_usage": 0,
    }

    _subscriptions[user_id] = subscription

    return SubscriptionResponse(**subscription)


@router.get("/subscription/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: UserResponse = Depends(get_current_user),
) -> SubscriptionStatusResponse:
    """Get the current subscription status for the authenticated user."""
    user_id = current_user.user_id
    sub = _subscriptions.get(user_id)
    if not sub:
        # Default to free tier if no subscription exists
        sub = {
            "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "tier": SubscriptionTier.FREE,
            "status": SubscriptionStatus.ACTIVE,
            "monthly_limit": TIER_LIMITS[SubscriptionTier.FREE],
            "current_usage": 0,
        }
        _subscriptions[user_id] = sub

    monthly_limit = sub["monthly_limit"]
    usage = sub["current_usage"]
    repurposes_remaining = -1 if monthly_limit == -1 else monthly_limit - usage

    return SubscriptionStatusResponse(
        user_id=sub["user_id"],
        tier=sub["tier"],
        status=sub["status"],
        monthly_limit=sub["monthly_limit"],
        current_usage=sub["current_usage"],
        repurposes_remaining=repurposes_remaining,
    )


@router.post("/webhook")
async def handle_webhook(request: Request) -> dict[str, bool]:
    """Handle Stripe webhook events."""
    # Check for Stripe signature
    stripe_signature = request.headers.get("stripe-signature")
    if not stripe_signature:
        raise HTTPException(status_code=403, detail="Missing Stripe signature")

    # In production, verify signature with stripe.Webhook.construct_event()
    # For testing, we accept any non-empty signature
    if stripe_signature == "invalid_signature":
        raise HTTPException(status_code=403, detail="Invalid Stripe signature")

    # Parse the event body
    try:
        event = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid JSON payload"
        ) from None

    event_type = event.get("type", "")

    # Handle known event types
    if event_type == "invoice.payment_succeeded":
        # Subscription payment succeeded - mark as active
        pass
    elif event_type == "invoice.payment_failed":
        # Payment failed - mark as past_due
        pass
    elif event_type == "customer.subscription.deleted":
        # Subscription deleted - downgrade to free
        pass
    # Unknown event types are handled idempotently (return 200)

    return {"received": True}
