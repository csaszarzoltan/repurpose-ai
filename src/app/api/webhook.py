"""Webhook API endpoints for async content repurposing."""

from __future__ import annotations

import uuid
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException

from app.models.webhook import JobRecord, WebhookRepurposeRequest
from app.services.ssrf import SSRFChecker

router = APIRouter(prefix="/api/v1", tags=["webhook"])

# In-memory job store — shared by create + status endpoints
JOBS_DB: dict[str, JobRecord] = {}

# Only HTTPS callbacks are allowed
ALLOWED_CALLBACK_SCHEMES: set[str] = {"https"}
# Max content body size in bytes
MAX_CONTENT_BODY_SIZE: int = 100_000


@router.post("/webhook/repurpose", status_code=202)
async def create_repurpose_job(
    request: WebhookRepurposeRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    """Accept a repurpose request, enqueue as background job, return job_id."""
    # ── Content size check ──────────────────────────────────────────────
    if len(request.content.body) > MAX_CONTENT_BODY_SIZE:
        raise HTTPException(status_code=413, detail="Content body too large")

    # ── SSRF / callback URL validation ──────────────────────────────────
    callback_str = str(request.callback_url)
    parsed = urlparse(callback_str)
    if parsed.scheme not in ALLOWED_CALLBACK_SCHEMES:
        raise HTTPException(
            status_code=422, detail="Callback URL must use HTTPS"
        )

    checker = SSRFChecker()
    if not checker.validate_url(callback_str):
        raise HTTPException(status_code=422, detail="SSRF-blocked callback URL")

    # ── Create job ──────────────────────────────────────────────────────
    job_id = str(uuid.uuid4())
    record = JobRecord(job_id=job_id)
    JOBS_DB[job_id] = record

    # TODO: schedule background processing (P0-3 placeholder)

    return {
        "job_id": job_id,
        "status_url": f"/api/v1/webhook/repurpose/status/{job_id}",
    }


@router.get("/webhook/repurpose/status/{job_id}")
async def get_job_status(job_id: str) -> dict:
    """Return the current status of a repurpose job."""
    record = JOBS_DB.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return record.model_dump()
