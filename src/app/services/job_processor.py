"""Background job processor for async webhook repurpose jobs."""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.models.content import BrandVoice, ContentFormat, ContentItem
from app.models.webhook import JobRecord, JobStatus
from app.services.repurpose import RepurposeService
from app.services.ssrf import SSRFChecker

logger = logging.getLogger(__name__)

# Shared reference to the webhook module's JOBS_DB — set at registration time
_JOBS_DB: dict[str, JobRecord] | None = None


def set_jobs_db(db: dict[str, JobRecord]) -> None:
    """Inject the webhook module's jobs store reference."""
    global _JOBS_DB
    _JOBS_DB = db


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
    jobs_db = _JOBS_DB or {}
    record = jobs_db.get(job_id)
    if record is None:
        logger.warning("Job %s not found in store — cannot process", job_id)
        return

    # Mark as processing
    record.status = JobStatus.PROCESSING
    logger.info("Processing job %s: %s -> %s", job_id, content.source_format, target_formats)

    try:
        # Call the repurpose service
        svc = RepurposeService()
        result = await svc.repurpose(
            content=content,
            target_formats=target_formats,
            brand_voice=brand_voice,
            custom_instructions=custom_instructions,
        )

        record.result = result
        record.status = JobStatus.COMPLETED

        # Deliver callback
        if callback_url:
            await _deliver_callback_with_retry(job_id, callback_url, result)

    except Exception as exc:
        logger.error("Job %s failed: %s", job_id, exc)
        record.status = JobStatus.FAILED
        record.error = str(exc)

    record.completed_at = __import__("datetime").datetime.utcnow()  # type: ignore[attr-defined]


async def _deliver_callback_with_retry(
    job_id: str,
    callback_url: str,
    result: object,
) -> None:
    """Deliver callback URL with retry logic (3 attempts, 2s/5s/10s backoff).

    SSRF-validates the URL before any attempt.
    """
    # SSRF validation
    checker = SSRFChecker()
    if not checker.validate_url(callback_url):
        logger.warning("Job %s: SSRF-blocked callback URL %s — skipping delivery", job_id, callback_url)
        return

    backoff = [2, 5, 10]
    result_data = result.model_dump() if hasattr(result, "model_dump") else {"result": str(result)}

    for attempt, delay in enumerate(backoff, start=1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(callback_url, json=result_data)
                resp.raise_for_status()
                logger.info("Job %s: callback delivered (attempt %d, status %d)", job_id, attempt, resp.status_code)
                return
        except Exception as exc:
            logger.warning("Job %s: callback attempt %d failed: %s", job_id, attempt, exc)
            if attempt < len(backoff):
                await asyncio.sleep(delay)

    logger.error("Job %s: callback delivery failed after %d attempts", job_id, len(backoff))
