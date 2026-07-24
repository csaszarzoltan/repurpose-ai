"""Background job processor for async webhook repurpose jobs."""

from __future__ import annotations

from app.models.content import BrandVoice, ContentFormat, ContentItem


async def process_repurpose_job(
    job_id: str,
    content: ContentItem,
    target_formats: list[ContentFormat],
    callback_url: str,
    brand_voice: BrandVoice = BrandVoice.PROFESSIONAL,
    custom_instructions: str | None = None,
) -> None:
    """Process a repurpose job: call service, deliver callback, update status.

    Retries callback delivery up to 3 times with backoff (2s / 5s / 10s).
    Validates callback URL via SSRFChecker before sending.
    Marks job as failed after all retries exhausted (silent — no unhandled exceptions).
    """
    raise NotImplementedError("P0-3: process_repurpose_job not implemented")
