"""Webhook API endpoints for async content repurposing and workflow triggers."""

from __future__ import annotations

import hashlib
import hmac
import uuid
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from app.models.webhook import JobRecord, WebhookRepurposeRequest
from app.services.ssrf import SSRFChecker
from app.services.workflow_engine import WorkflowEngine
from app.services.workflow_store import WORKFLOWS_DB, get_workflow

router = APIRouter(prefix="/api/v1", tags=["webhook"])

# In-memory job store — shared by create + status endpoints
JOBS_DB: dict[str, JobRecord] = {}

# Only HTTPS callbacks are allowed
ALLOWED_CALLBACK_SCHEMES: set[str] = {"https"}
# Max content body size in bytes
MAX_CONTENT_BODY_SIZE: int = 100_000


def _make_engine() -> WorkflowEngine:
    """Create a WorkflowEngine backed by the shared in-memory store."""
    return WorkflowEngine(store={"workflows": WORKFLOWS_DB})


def _verify_hmac(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature."""
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    # Constant-time comparison
    return hmac.compare_digest(f"sha256={expected}", signature)


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

    # Schedule background processing
    from app.services.job_processor import process_repurpose_job
    background_tasks.add_task(
        process_repurpose_job,
        job_id=job_id,
        content=request.content,
        target_formats=request.target_formats,
        callback_url=callback_str,
        brand_voice=request.brand_voice,
        custom_instructions=request.custom_instructions,
    )

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


@router.post("/webhook/workflow/{workflow_id}", status_code=202)
async def trigger_workflow_via_webhook(
    workflow_id: str,
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
) -> dict:
    """Trigger a workflow via incoming webhook.

    If the workflow's webhook_config has a secret, HMAC-SHA256 verification
    is performed via the X-Hub-Signature-256 header.
    """
    wf = get_workflow(workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # ── HMAC signature verification ────────────────────────────────────
    webhook_config = wf.webhook_config
    if webhook_config and webhook_config.secret:
        if not x_hub_signature_256:
            raise HTTPException(
                status_code=401,
                detail="Missing X-Hub-Signature-256 header",
            )
        body = await request.body()
        if not _verify_hmac(body, x_hub_signature_256, webhook_config.secret):
            raise HTTPException(
                status_code=403,
                detail="Invalid HMAC signature",
            )

    # ── SSRF validation on callback URLs in request body ────────────────
    try:
        body_json = await request.json()
    except Exception:
        body_json = {}

    callback_urls = _extract_callback_urls(body_json)
    checker = SSRFChecker()
    for url in callback_urls:
        if not checker.validate_url(url):
            raise HTTPException(
                status_code=422,
                detail=f"SSRF-blocked callback URL: {url}",
            )

    # ── Trigger the workflow ────────────────────────────────────────────
    engine = _make_engine()
    execution = await engine.run_workflow(workflow_id)

    return {"execution_id": execution.execution_id}


def _extract_callback_urls(data: dict) -> list[str]:
    """Extract callback URLs from a JSON body."""
    urls: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ("callback_url", "callback", "url", "webhook_url"):
                if isinstance(value, str):
                    urls.append(value)
            elif isinstance(value, dict):
                urls.extend(_extract_callback_urls(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        urls.extend(_extract_callback_urls(item))
    return urls
