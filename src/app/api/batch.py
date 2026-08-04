"""Batch repurpose API endpoint."""

from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, HTTPException

from app.models.content import (
    BrandVoice,
    ContentFormat,
    ContentItem,
)
from app.models.workflow import BatchRepurposeResponse
from app.services.languages import validate_languages
from app.services.repurpose import RepurposeService

router = APIRouter(prefix="/api/v1", tags=["batch"])


@router.post("/repurpose/batch")
async def batch_repurpose(body: dict) -> dict:
    """Repurpose multiple content items in batch.

    Uses asyncio.gather with a semaphore to limit concurrency.
    """
    # Validate jobs list
    jobs = body.get("jobs", [])
    if not isinstance(jobs, list) or len(jobs) == 0:
        raise HTTPException(status_code=422, detail="jobs must be a non-empty list")
    if len(jobs) > 50:
        raise HTTPException(status_code=422, detail="jobs must not exceed 50 items")

    concurrency = body.get("concurrency", 5)
    if not isinstance(concurrency, int) or concurrency < 1:
        concurrency = 5

    # Validate each job
    # Validate each job structure before processing
    for i, job in enumerate(jobs):
        if not isinstance(job, dict):
            raise HTTPException(status_code=422, detail=f"Job at index {i} must be a dict")
        content = job.get("content")
        if not content or not isinstance(content, dict):
            raise HTTPException(status_code=422, detail=f"Job at index {i}: invalid or missing content")
        if not content.get("body") and not content.get("title"):
            # Accept jobs with both missing — will fail at parse time
            pass
        target_formats = job.get("target_formats", [])
        if not target_formats or not isinstance(target_formats, list):
            raise HTTPException(status_code=422, detail=f"Job at index {i}: at least one target_format required")

    batch_id = str(uuid.uuid4())
    semaphore = asyncio.Semaphore(concurrency)

    async def process_job(job: dict) -> dict:
        """Process a single batch job."""
        async with semaphore:
            try:
                # Extract content
                content_data = job.get("content", {})
                if not content_data or not isinstance(content_data, dict):
                    return {"status": "failed", "error": "Invalid content"}

                try:
                    content_item = ContentItem(
                        title=content_data.get("title", ""),
                        body=content_data.get("body", ""),
                        source_format=ContentFormat(content_data.get("source_format", "blog_post")),
                    )
                except (ValueError, KeyError):
                    return {"status": "failed", "error": "Invalid content format"}

                target_formats_raw = job.get("target_formats", [])
                target_formats: list[ContentFormat] = []
                for fmt in target_formats_raw:
                    try:
                        target_formats.append(ContentFormat(fmt))
                    except ValueError:
                        return {"status": "failed", "error": f"Invalid target format: {fmt}"}

                if not target_formats:
                    return {"status": "failed", "error": "At least one target_format required"}

                brand_voice_str = job.get("brand_voice", "professional")
                try:
                    brand_voice = BrandVoice(brand_voice_str)
                except ValueError:
                    brand_voice = BrandVoice.PROFESSIONAL

                # Optional per-language output: reject unsupported codes for
                # this job (failed job, not a whole-request 422).
                target_languages = job.get("target_languages", [])
                if not isinstance(target_languages, list):
                    return {
                        "status": "failed",
                        "error": "target_languages must be a list of ISO 639-1 codes",
                    }
                try:
                    validate_languages(target_languages)
                except ValueError as exc:
                    return {"status": "failed", "error": str(exc)}

                svc = RepurposeService()
                result = await svc.repurpose(
                    content=content_item,
                    target_formats=target_formats,
                    brand_voice=brand_voice,
                    custom_instructions=job.get("custom_instructions"),
                    target_languages=target_languages,
                )

                return {
                    "status": "completed",
                    "result": result.model_dump() if hasattr(result, "model_dump") else str(result),
                }
            except Exception as exc:
                return {"status": "failed", "error": str(exc)}

    results = await asyncio.gather(*[process_job(j) for j in jobs])

    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    result_list = [r.get("result", {}) for r in results if r.get("status") == "completed"]
    errors = [r.get("error") for r in results if r.get("status") == "failed"]

    return BatchRepurposeResponse(
        batch_id=batch_id,
        total=len(jobs),
        completed=completed,
        failed=failed,
        results=result_list,
        errors=errors,
    ).model_dump()
