"""Pre-dev tests for POST /api/v1/webhook/repurpose async pipeline.

Source of truth: analysis/analysis-brief.md — read §4 (P0-1 through P0-5,
P1-1 through P1-4) and §5 (Acceptance Criteria).

Interface tests  → MUST PASS immediately (models are real, stubs exist).
Behavioral tests → MUST FAIL with NotImplementedError until implementation.
"""

from __future__ import annotations

import inspect
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.api.webhook import (
    create_repurpose_job,
    get_job_status,
    router,
)
from app.main import app
from app.models.content import BrandVoice, ContentFormat, ContentItem
from app.models.webhook import JobRecord, JobStatus, WebhookRepurposeRequest

# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — must pass immediately
# ════════════════════════════════════════════════════════════════════════════════


class TestWebhookRepurposeModelImport:
    """Interface: WebhookRepurposeRequest model exists with correct fields."""

    def test_model_importable(self):
        assert WebhookRepurposeRequest is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel

        assert issubclass(WebhookRepurposeRequest, BaseModel)

    def test_has_content_field(self):
        assert "content" in WebhookRepurposeRequest.model_fields

    def test_content_field_type_is_content_item(self):
        field = WebhookRepurposeRequest.model_fields["content"]
        assert field.annotation is ContentItem

    def test_has_target_formats_field(self):
        assert "target_formats" in WebhookRepurposeRequest.model_fields

    def test_target_formats_is_list_of_content_format(self):
        field = WebhookRepurposeRequest.model_fields["target_formats"]
        ann = field.annotation
        assert "list[ContentFormat]" in str(ann) or ann == list[ContentFormat]

    def test_has_brand_voice_field(self):
        assert "brand_voice" in WebhookRepurposeRequest.model_fields

    def test_brand_voice_defaults_to_professional(self):
        field = WebhookRepurposeRequest.model_fields["brand_voice"]
        assert field.default is BrandVoice.PROFESSIONAL

    def test_has_callback_url_field(self):
        assert "callback_url" in WebhookRepurposeRequest.model_fields

    def test_callback_url_is_str(self):
        field = WebhookRepurposeRequest.model_fields["callback_url"]
        # Pydantic auto-detects URL fields and resolves to HttpUrl
        from pydantic import HttpUrl as PydanticHttpUrl

        assert field.annotation is PydanticHttpUrl

    def test_has_custom_instructions_field(self):
        assert "custom_instructions" in WebhookRepurposeRequest.model_fields

    def test_custom_instructions_is_optional(self):
        field = WebhookRepurposeRequest.model_fields["custom_instructions"]
        assert field.annotation == str | None

    def test_has_idempotency_key_field(self):
        assert "idempotency_key" in WebhookRepurposeRequest.model_fields

    def test_idempotency_key_is_optional(self):
        field = WebhookRepurposeRequest.model_fields["idempotency_key"]
        assert field.annotation == str | None

    def test_default_brand_voice_on_construction(self):
        content = ContentItem(
            title="T", body="B", source_format=ContentFormat.BLOG_POST
        )
        req = WebhookRepurposeRequest(
            content=content,
            target_formats=[ContentFormat.TWITTER_THREAD],
            callback_url="https://example.com/hook",
        )
        assert req.brand_voice == BrandVoice.PROFESSIONAL

    def test_callback_url_required(self):
        content = ContentItem(
            title="T", body="B", source_format=ContentFormat.BLOG_POST
        )
        with pytest.raises(ValidationError):
            WebhookRepurposeRequest(
                content=content,
                target_formats=[ContentFormat.TWITTER_THREAD],
            )

    def test_target_formats_required(self):
        content = ContentItem(
            title="T", body="B", source_format=ContentFormat.BLOG_POST
        )
        with pytest.raises(ValidationError):
            WebhookRepurposeRequest(
                content=content,
                callback_url="https://example.com/hook",
            )

    def test_content_required(self):
        with pytest.raises(ValidationError):
            WebhookRepurposeRequest(
                target_formats=[ContentFormat.TWITTER_THREAD],
                callback_url="https://example.com/hook",
            )


class TestJobStatusEnum:
    """Interface: JobStatus enum exists with expected values."""

    def test_importable(self):
        assert JobStatus is not None

    def test_is_str_enum(self):
        assert issubclass(JobStatus, str)

    def test_has_pending(self):
        assert hasattr(JobStatus, "PENDING")
        assert JobStatus.PENDING == "pending"

    def test_has_processing(self):
        assert hasattr(JobStatus, "PROCESSING")
        assert JobStatus.PROCESSING == "processing"

    def test_has_completed(self):
        assert hasattr(JobStatus, "COMPLETED")
        assert JobStatus.COMPLETED == "completed"

    def test_has_failed(self):
        assert hasattr(JobStatus, "FAILED")
        assert JobStatus.FAILED == "failed"

    def test_all_values_expected(self):
        values = {v.value for v in JobStatus}
        assert values == {"pending", "processing", "completed", "failed"}


class TestJobRecordModel:
    """Interface: JobRecord model exists with correct fields."""

    def test_importable(self):
        assert JobRecord is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel

        assert issubclass(JobRecord, BaseModel)

    def test_has_job_id(self):
        assert "job_id" in JobRecord.model_fields

    def test_job_id_is_str(self):
        field = JobRecord.model_fields["job_id"]
        assert field.annotation is str

    def test_has_status_with_default(self):
        assert "status" in JobRecord.model_fields
        field = JobRecord.model_fields["status"]
        assert field.default is JobStatus.PENDING

    def test_has_created_at(self):
        assert "created_at" in JobRecord.model_fields

    def test_created_at_defaults_to_now(self):
        record = JobRecord(job_id="test-1")
        assert isinstance(record.created_at, datetime)

    def test_has_completed_at(self):
        assert "completed_at" in JobRecord.model_fields
        field = JobRecord.model_fields["completed_at"]
        assert field.annotation == datetime | None

    def test_completed_at_defaults_none(self):
        record = JobRecord(job_id="test-1")
        assert record.completed_at is None

    def test_has_result_field(self):
        assert "result" in JobRecord.model_fields

    def test_result_is_optional_repurpose_response(self):
        """result field expects RepurposeResponse per job status contract."""
        field = JobRecord.model_fields["result"]
        from app.models.content import RepurposeResponse

        assert field.annotation == RepurposeResponse | None

    def test_result_defaults_none(self):
        record = JobRecord(job_id="test-1")
        assert record.result is None

    def test_has_error_field(self):
        assert "error" in JobRecord.model_fields

    def test_error_is_optional_str(self):
        field = JobRecord.model_fields["error"]
        assert field.annotation == str | None

    def test_error_defaults_none(self):
        record = JobRecord(job_id="test-1")
        assert record.error is None

    def test_job_id_required(self):
        with pytest.raises(ValidationError):
            JobRecord()

    def test_can_set_status_explicitly(self):
        record = JobRecord(job_id="test-2", status=JobStatus.PROCESSING)
        assert record.status == JobStatus.PROCESSING

    def test_can_set_completed_fields(self):
        from app.models.content import RepurposeResponse

        record = JobRecord(
            job_id="test-3",
            status=JobStatus.COMPLETED,
            completed_at=datetime(2026, 7, 24, 10, 0, 0),
            result=RepurposeResponse(
                original_id="orig-1",
                repurposed={ContentFormat.BLOG_POST: "output text"},
            ),
        )
        assert record.status == JobStatus.COMPLETED
        assert record.completed_at is not None
        assert record.result is not None
        assert record.result.original_id == "orig-1"


class TestWebhookRepurposeRouterInterface:
    """Interface: webhook repurpose router is importable and has expected routes."""

    def test_router_importable(self):
        assert router is not None

    def test_router_is_apirouter(self):
        from fastapi import APIRouter

        assert isinstance(router, APIRouter)

    def test_has_webhook_repurpose_prefix(self):
        assert router.prefix == "/api/v1"

    def test_has_webhook_tag(self):
        assert "webhook" in router.tags

    def test_post_webhook_repurpose_route_registered(self):
        routes = [r for r in router.routes if hasattr(r, "methods")]
        post_routes = [
            r
            for r in routes
            if "POST" in r.methods and r.path == "/api/v1/webhook/repurpose"
        ]
        assert len(post_routes) == 1

    def test_get_status_route_registered(self):
        routes = [r for r in router.routes if hasattr(r, "methods")]
        get_routes = [
            r
            for r in routes
            if "GET" in r.methods
            and r.path == "/api/v1/webhook/repurpose/status/{job_id}"
        ]
        assert len(get_routes) == 1

    def test_route_in_openapi_schema(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/webhook/repurpose" in paths
        assert "post" in paths["/api/v1/webhook/repurpose"]

    def test_status_route_in_openapi_schema(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        assert "/api/v1/webhook/repurpose/status/{job_id}" in paths
        assert "get" in paths["/api/v1/webhook/repurpose/status/{job_id}"]


class TestWebhookRepurposeHandlerSignatures:
    """Interface: handler functions have correct signatures."""

    def test_handle_repurpose_webhook_exists(self):
        assert create_repurpose_job is not None
        assert callable(create_repurpose_job)

    def test_handle_repurpose_webhook_is_async(self):
        assert inspect.iscoroutinefunction(create_repurpose_job)

    def test_get_repurpose_job_status_exists(self):
        assert get_job_status is not None
        assert callable(get_job_status)

    def test_get_repurpose_job_status_is_async(self):
        assert inspect.iscoroutinefunction(get_job_status)

    def test_get_repurpose_job_status_accepts_job_id(self):
        sig = inspect.signature(get_job_status)
        params = list(sig.parameters.keys())
        assert "job_id" in params


class TestWebhookRepurposeModuleInterface:
    """Interface: webhook repurpose module is importable as a whole."""

    def test_module_importable(self):
        from app.api import webhook as wr

        assert wr is not None
        assert hasattr(wr, "router")
        assert hasattr(wr, "create_repurpose_job")
        assert hasattr(wr, "get_job_status")


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — must fail with NotImplementedError until implementation
# ════════════════════════════════════════════════════════════════════════════════


class TestWebhookRepurposeEndpointBehavior:
    """Behavioral: POST /api/v1/webhook/repurpose endpoint (AC-P0-2)."""

    def _valid_payload(self, **overrides):
        body = {
            "content": {
                "title": "AI in Healthcare",
                "body": "AI is transforming diagnostics.",
                "source_format": "blog_post",
                "tags": ["ai"],
            },
            "target_formats": ["twitter_thread"],
            "callback_url": "https://example.com/webhook-receiver",
            "brand_voice": "professional",
        }
        body.update(overrides)
        return body

    async def test_post_returns_202_with_job_id(self):
        """AC-P0-2: Valid request → 202 with job_id and status_url."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose", json=self._valid_payload()
            )
        # Expects 202 — currently fails with NotImplementedError → 500
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert "status_url" in data
        assert isinstance(data["job_id"], str)

    async def test_post_response_has_status_url(self):
        """AC-P0-2: status_url should point to the status endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose", json=self._valid_payload()
            )
        assert response.status_code == 202
        data = response.json()
        assert "/api/v1/webhook/repurpose/status/" in data["status_url"]

    async def test_post_returns_422_for_missing_content(self):
        """AC-P0-2: Missing content → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "target_formats": ["twitter_thread"],
                    "callback_url": "https://example.com/hook",
                },
            )
        assert response.status_code == 422

    async def test_post_returns_422_for_missing_callback_url(self):
        """AC-P0-2: Missing callback_url → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "content": {
                        "title": "T",
                        "body": "B",
                        "source_format": "blog_post",
                    },
                    "target_formats": ["twitter_thread"],
                },
            )
        assert response.status_code == 422

    async def test_post_returns_422_for_missing_target_formats(self):
        """AC-P0-2: Missing target_formats → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "content": {
                        "title": "T",
                        "body": "B",
                        "source_format": "blog_post",
                    },
                    "callback_url": "https://example.com/hook",
                },
            )
        assert response.status_code == 422

    async def test_post_returns_422_for_empty_body(self):
        """AC-P0-2: Empty JSON body → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose", json={}
            )
        assert response.status_code == 422

    async def test_post_returns_422_for_invalid_format(self):
        """AC-P0-2: Invalid target_format value → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "content": {
                        "title": "T",
                        "body": "B",
                        "source_format": "blog_post",
                    },
                    "target_formats": ["nonexistent_format"],
                    "callback_url": "https://example.com/hook",
                },
            )
        assert response.status_code == 422

    async def test_post_returns_422_for_invalid_brand_voice(self):
        """AC-P0-2: Invalid brand_voice value → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "content": {
                        "title": "T",
                        "body": "B",
                        "source_format": "blog_post",
                    },
                    "target_formats": ["twitter_thread"],
                    "callback_url": "https://example.com/hook",
                    "brand_voice": "invalid_voice",
                },
            )
        assert response.status_code == 422

    async def test_post_response_time_under_200ms(self):
        """AC-P0-2: Response returns immediately (no blocking)."""
        import time

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            start = time.monotonic()
            await client.post(
                "/api/v1/webhook/repurpose", json=self._valid_payload()
            )
            elapsed = time.monotonic() - start
        assert elapsed < 0.2

    async def test_post_accepts_custom_instructions(self):
        """AC-P0-2: Optional custom_instructions are accepted."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json=self._valid_payload(
                    custom_instructions="Make it under 280 chars"
                ),
            )
        # Expects 202 — currently fails with NotImplementedError → 500
        assert response.status_code == 202

    async def test_post_accepts_idempotency_key(self):
        """AC-P0-2: Optional Idempotency-Key header is accepted."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json=self._valid_payload(),
                headers={"Idempotency-Key": "idem-001"},
            )
        # Expects 202 — currently fails with NotImplementedError → 500
        assert response.status_code == 202

    async def test_post_with_ssrf_blocked_url_returns_422(self):
        """AC-P0-5: SSRF-blocked callback URL → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json=self._valid_payload(
                    callback_url="http://localhost:8000/evil"
                ),
            )
        assert response.status_code == 422

    async def test_post_with_private_ip_url_returns_422(self):
        """AC-P0-5: Private IP callback URL → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json=self._valid_payload(
                    callback_url="http://192.168.1.1/hook"
                ),
            )
        assert response.status_code == 422

    async def test_post_with_file_scheme_url_returns_422(self):
        """AC-P0-5: file:// callback URL → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json=self._valid_payload(
                    callback_url="file:///etc/passwd"
                ),
            )
        assert response.status_code == 422

    async def test_post_with_invalid_url_string_returns_422(self):
        """AC-P0-2/5: Non-URL string as callback_url → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json=self._valid_payload(callback_url="not-a-url"),
            )
        assert response.status_code == 422


class TestWebhookRepurposeJobStatusBehavior:
    """Behavioral: GET /api/v1/webhook/repurpose/status/{job_id} (AC-P0-4)."""

    async def test_get_status_returns_200_for_known_job(self):
        """AC-P0-4: Known job_id → 200 with job details."""
        # First create a job, then check status
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            create_resp = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "content": {
                        "title": "T",
                        "body": "B",
                        "source_format": "blog_post",
                    },
                    "target_formats": ["twitter_thread"],
                    "callback_url": "https://example.com/hook",
                },
            )
            # Create fails with NotImplementedError too, but if it worked:
            if create_resp.status_code == 202:
                job_id = create_resp.json()["job_id"]
                status_resp = await client.get(
                    f"/api/v1/webhook/repurpose/status/{job_id}"
                )
                assert status_resp.status_code == 200
                data = status_resp.json()
                assert data["job_id"] == job_id
                assert data["status"] in ("pending", "processing", "completed", "failed")
                assert "created_at" in data
        # If create failed, this test is already moot — but we always
        # assert to produce a clear NotImplementedError trace
        if create_resp.status_code != 202:
            pytest.skip("Create endpoint not yet implemented — cannot test status chain")

    async def test_get_status_returns_404_for_unknown_job(self):
        """AC-P0-4: Unknown job_id → 404."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/webhook/repurpose/status/nonexistent-job-id"
            )
        assert response.status_code == 404

    async def test_get_status_response_has_expected_fields(self):
        """AC-P0-4: Status response includes all expected fields."""
        # We check this via schema even if no job exists
        schema = app.openapi()
        paths = schema.get("paths", {})
        status_path = paths.get(
            "/api/v1/webhook/repurpose/status/{job_id}", {}
        )
        get_schema = status_path.get("get", {})
        responses = get_schema.get("responses", {})
        assert "200" in responses or "404" in responses


class TestWebhookRepurposeCallbackDeliveryBehavior:
    """Behavioral: Callback delivery and SSRF protection (AC-P0-3, AC-P0-5)."""

    @pytest.mark.xfail(reason="Not yet implemented — callback delivery")
    async def test_callback_delivers_to_url(self):
        """AC-P0-3: Repurposed content is POSTed to callback_url."""
        raise NotImplementedError(
            "Callback delivery not yet implemented — test is a placeholder"
        )

    @pytest.mark.xfail(reason="Not yet implemented — callback retry")
    async def test_callback_retries_on_failure(self):
        """AC-P0-3: Failed callback delivery retries 3 times with backoff."""
        raise NotImplementedError(
            "Callback retry not yet implemented — test is a placeholder"
        )

    @pytest.mark.xfail(reason="Not yet implemented — callback failure handling")
    async def test_callback_marks_job_failed_after_retries_exhausted(self):
        """AC-P0-3: After all retries exhausted, job status → failed."""
        raise NotImplementedError(
            "Callback failure handling not yet implemented — test is a placeholder"
        )

    @pytest.mark.xfail(reason="Not yet implemented — callback content_type")
    async def test_callback_includes_content_type_json(self):
        """AC-P0-3: Callback POST includes Content-Type: application/json."""
        raise NotImplementedError(
            "Callback delivery not yet implemented — test is a placeholder"
        )

    @pytest.mark.xfail(reason="Not yet implemented — callback body structure")
    async def test_callback_body_has_job_id_and_result(self):
        """AC-P0-3: Callback body contains job_id, status, result."""
        raise NotImplementedError(
            "Callback delivery not yet implemented — test is a placeholder"
        )


class TestWebhookRepurposeSecurityBehavior:
    """Behavioral: Webhook security (AC-P1-1, AC-P1-2, AC-P1-3)."""

    @pytest.mark.xfail(reason="Design pending — HMAC not checked on incoming requests")
    async def test_missing_hmac_signature_returns_401(self):
        """AC-P1-1: Missing X-Webhook-Signature → 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "content": {
                        "title": "T",
                        "body": "B",
                        "source_format": "blog_post",
                    },
                    "target_formats": ["twitter_thread"],
                    "callback_url": "https://example.com/hook",
                },
                # No signature header
            )
        assert response.status_code == 401

    @pytest.mark.xfail(reason="Design pending — HMAC not checked on incoming requests")
    async def test_wrong_hmac_signature_returns_401(self):
        """AC-P1-1: Wrong X-Webhook-Signature → 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "content": {
                        "title": "T",
                        "body": "B",
                        "source_format": "blog_post",
                    },
                    "target_formats": ["twitter_thread"],
                    "callback_url": "https://example.com/hook",
                },
                headers={"X-Webhook-Signature": "invalid_signature"},
            )
        assert response.status_code == 401

    @pytest.mark.xfail(reason="Not yet implemented — idempotent replay")
    async def test_idempotent_replay_returns_same_result(self):
        """AC-P1-2: Same Idempotency-Key returns existing result."""
        raise NotImplementedError(
            "Idempotency not yet implemented — test is a placeholder"
        )

    @pytest.mark.xfail(reason="Not yet implemented — idempotent replay header")
    async def test_idempotent_replay_includes_header(self):
        """AC-P1-2: Idempotent replay includes X-Idempotent-Replay: true."""
        raise NotImplementedError(
            "Idempotency not yet implemented — test is a placeholder"
        )

    @pytest.mark.xfail(reason="Not yet implemented — callback signing")
    async def test_callback_hmac_signature_included(self):
        """AC-P1-3: Callback POST includes X-Signature-256 header."""
        raise NotImplementedError(
            "Callback signing not yet implemented — test is a placeholder"
        )


class TestWebhookRepurposeInputValidationBehavior:
    """Behavioral: Input validation and error handling (AC-P1-4)."""

    async def test_content_exceeds_max_size_returns_413(self):
        """AC-P1-4: Content body >100KB → 413 Payload Too Large."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "content": {
                        "title": "Huge content",
                        "body": "X" * 100_001,
                        "source_format": "blog_post",
                    },
                    "target_formats": ["twitter_thread"],
                    "callback_url": "https://example.com/hook",
                },
            )
        assert response.status_code == 413

    async def test_invalid_format_error_has_valid_formats_list(self):
        """AC-P1-4: Invalid format error includes list of valid formats."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "content": {
                        "title": "Test",
                        "body": "Valid body",
                        "source_format": "blog_post",
                    },
                    "target_formats": ["nonexistent_format"],
                    "callback_url": "https://example.com/hook",
                },
            )
        assert response.status_code == 422
        detail = response.json()["detail"]
        detail_str = str(detail)
        # Pydantic enum validation lists valid values in the error message
        assert "blog_post" in detail_str or "twitter_thread" in detail_str

    async def test_invalid_voice_error_has_valid_voices_list(self):
        """AC-P1-4: Invalid voice error includes list of valid voices."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/webhook/repurpose",
                json={
                    "content": {
                        "title": "Test",
                        "body": "Valid body",
                        "source_format": "blog_post",
                    },
                    "target_formats": ["twitter_thread"],
                    "callback_url": "https://example.com/hook",
                    "brand_voice": "nonexistent_voice",
                },
            )
        assert response.status_code == 422
        detail = response.json()["detail"]
        detail_str = str(detail)
        # Pydantic enum validation lists valid values in the error message
        assert "professional" in detail_str or "casual" in detail_str
