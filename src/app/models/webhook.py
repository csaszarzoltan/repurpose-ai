"""Webhook models for async content repurposing pipeline."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl

from app.models.content import BrandVoice, ContentFormat, ContentItem, RepurposeResponse


class JobStatus(StrEnum):
    """Status values for async repurpose jobs."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WebhookRepurposeRequest(BaseModel):
    """Inbound request for async content repurposing via webhook."""

    content: ContentItem
    target_formats: list[ContentFormat] = Field(min_length=1)
    callback_url: HttpUrl
    brand_voice: BrandVoice = BrandVoice.PROFESSIONAL
    custom_instructions: str | None = None
    idempotency_key: str | None = None


class JobRecord(BaseModel):
    """Persistent record of an async repurpose job."""

    job_id: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    result: RepurposeResponse | None = None
    error: str | None = None


class JobStatusResponse(BaseModel):
    """Response model for job status endpoint."""

    job_id: str
    status: JobStatus
    created_at: datetime
    completed_at: datetime | None = None
    result: RepurposeResponse | None = None
    error: str | None = None
