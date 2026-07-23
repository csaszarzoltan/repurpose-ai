"""Subscription and billing models for RepurposeAI."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SubscriptionTier(StrEnum):
    """Subscription tier options."""
    FREE = "free"
    PRO = "pro"


class SubscriptionStatus(StrEnum):
    """Subscription status states."""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


class SubscriptionRequest(BaseModel):
    """Request to create or update a subscription."""
    tier: SubscriptionTier
    user_id: str


class SubscriptionResponse(BaseModel):
    """Response containing subscription details."""
    subscription_id: str
    user_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    monthly_limit: int
    current_usage: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


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
