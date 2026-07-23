"""Subscription models for RepurposeAI billing."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class SubscriptionTier(StrEnum):
    """Subscription tier options."""

    FREE = "free"
    PRO = "pro"


class SubscriptionStatus(StrEnum):
    """Subscription status options."""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


class SubscriptionRequest(BaseModel):
    """Request to create or update a subscription.

    tier is a plain string; the API handler validates it and
    returns 400 for invalid values (instead of Pydantic's default 422).
    """

    tier: str
    user_id: str


class SubscriptionResponse(BaseModel):
    """Response after creating/updating a subscription."""

    subscription_id: str
    user_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    monthly_limit: int  # -1 for unlimited
    current_usage: int = 0


class SubscriptionStatusResponse(BaseModel):
    """Response for subscription status query."""

    user_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    monthly_limit: int
    current_usage: int
    repurposes_remaining: int


class WebhookEvent(BaseModel):
    """Stripe webhook event payload."""

    id: str
    type: str
    data: dict
