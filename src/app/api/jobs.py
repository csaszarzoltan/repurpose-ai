"""Unified job status API endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.webhook import JOBS_DB as WEBHOOK_JOBS_DB
from app.services.workflow_store import WORKFLOW_EXECUTIONS_DB

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict:
    """Return the current status of any job (webhook or workflow)."""
    # Check webhook jobs first
    webhook_job = WEBHOOK_JOBS_DB.get(job_id)
    if webhook_job is not None:
        return webhook_job.model_dump()

    # Check workflow executions
    execution = WORKFLOW_EXECUTIONS_DB.get(job_id)
    if execution is not None:
        return execution.model_dump()

    raise HTTPException(status_code=404, detail="Job not found")
