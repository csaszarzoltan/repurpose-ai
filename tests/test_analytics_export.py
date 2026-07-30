"""Pre-dev tests for CSV export (P1.3) and PDF export (P2.1).

Source of truth: analysis/analysis-brief.md §4 P1.3 (CSV), §4 P2.1 (PDF).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.services.analytics.export_service import ExportService
    HAS_SERVICE = True
except (ImportError, ModuleNotFoundError):
    HAS_SERVICE = False


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_SERVICE, reason="export_service.py not implemented yet")
class TestExportServiceInterface:
    """Interface: ExportService is importable and has expected API."""

    def test_importable(self):
        assert ExportService is not None

    def test_is_class(self):
        assert isinstance(ExportService, type)

    def test_init_accepts_data_store(self):
        svc = ExportService(data_store=None)
        assert svc is not None

    def test_init_defaults(self):
        svc = ExportService()
        assert svc is not None

    # ── CSV methods ─────────────────────────────────────

    def test_has_export_csv_method(self):
        import inspect
        assert hasattr(ExportService, "export_csv")
        assert inspect.iscoroutinefunction(ExportService.export_csv)

    def test_export_csv_returns_string_type_hint(self):
        import inspect
        sig = inspect.signature(ExportService.export_csv)
        ann = sig.return_annotation
        assert ann in (str, "str", inspect.Parameter.empty)

    def test_export_csv_accepts_metric_selection(self):
        import inspect
        sig = inspect.signature(ExportService.export_csv)
        assert "metric_selection" in sig.parameters
        assert "date_range" in sig.parameters

    def test_has_get_export_status_method(self):
        import inspect
        assert hasattr(ExportService, "get_export_status")
        assert inspect.iscoroutinefunction(ExportService.get_export_status)

    # ── PDF methods ─────────────────────────────────────

    def test_has_export_pdf_method(self):
        import inspect
        assert hasattr(ExportService, "export_pdf")
        assert inspect.iscoroutinefunction(ExportService.export_pdf)

    def test_export_pdf_accepts_brand_config(self):
        import inspect
        sig = inspect.signature(ExportService.export_pdf)
        assert "brand_config" in sig.parameters

    # ── Scheduling methods ──────────────────────────────

    def test_has_create_schedule_method(self):
        import inspect
        assert hasattr(ExportService, "create_schedule")
        assert inspect.iscoroutinefunction(ExportService.create_schedule)

    def test_has_delete_schedule_method(self):
        import inspect
        assert hasattr(ExportService, "delete_schedule")
        assert inspect.iscoroutinefunction(ExportService.delete_schedule)

    def test_has_list_schedules_method(self):
        import inspect
        assert hasattr(ExportService, "list_schedules")
        assert inspect.iscoroutinefunction(ExportService.list_schedules)

    def test_create_schedule_accepts_export_type_and_cadence(self):
        import inspect
        sig = inspect.signature(ExportService.create_schedule)
        assert "export_type" in sig.parameters
        assert "cadence" in sig.parameters

    def test_delete_schedule_accepts_schedule_id(self):
        import inspect
        sig = inspect.signature(ExportService.delete_schedule)
        assert "schedule_id" in sig.parameters


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — CSV Export (P1.3)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_SERVICE, reason="export_service.py not implemented yet")
class TestCsvExportBehavior:
    """Behavioral: CSV export produces valid CSV output."""

    async def test_export_csv_returns_string(self):
        svc = ExportService()
        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = datetime(2026, 1, 31, tzinfo=UTC)
        csv_data = await svc.export_csv(
            metric_selection=["reach", "impressions", "engagement_rate"],
            date_range=(start, end),
            platform_filter="linkedin",
        )
        assert isinstance(csv_data, str)
        assert len(csv_data) > 0

    async def test_export_csv_contains_header(self):
        svc = ExportService()
        csv_data = await svc.export_csv(
            metric_selection=["reach"],
            date_range=(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 31, tzinfo=UTC)),
        )
        assert "reach" in csv_data or csv_data.startswith("date")

    async def test_export_csv_without_platform_filter(self):
        svc = ExportService()
        csv_data = await svc.export_csv(
            metric_selection=["reach"],
            date_range=(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 31, tzinfo=UTC)),
        )
        assert isinstance(csv_data, str)

    async def test_export_status_returns_dict(self):
        svc = ExportService()
        status = await svc.get_export_status("export_123")
        assert isinstance(status, dict)
        assert "status" in status or "id" in status


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — PDF Export (P2.1)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_SERVICE, reason="export_service.py not implemented yet")
class TestPdfExportBehavior:
    """Behavioral: PDF export produces branded PDF."""

    async def test_export_pdf_returns_string_path(self):
        svc = ExportService()
        pdf_path = await svc.export_pdf(
            metric_selection=["reach", "engagement_rate"],
            date_range=(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 31, tzinfo=UTC)),
        )
        assert isinstance(pdf_path, str)
        assert pdf_path.endswith(".pdf") or len(pdf_path) > 0

    async def test_export_pdf_with_brand_config(self):
        svc = ExportService()
        brand = {"primary_color": "#1a73e8", "logo_url": "https://example.com/logo.png", "company_name": "TestCorp"}
        pdf_path = await svc.export_pdf(
            metric_selection=["reach"],
            date_range=(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 31, tzinfo=UTC)),
            brand_config=brand,
        )
        assert isinstance(pdf_path, str)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Scheduling
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_SERVICE, reason="export_service.py not implemented yet")
class TestScheduleBehavior:
    """Behavioral: Schedule management works correctly."""

    async def test_create_schedule_returns_id(self):
        svc = ExportService()
        schedule_id = await svc.create_schedule(
            export_type="csv",
            cadence="daily",
            metric_selection=["reach", "impressions"],
        )
        assert isinstance(schedule_id, str)
        assert len(schedule_id) > 0

    async def test_create_weekly_schedule(self):
        svc = ExportService()
        schedule_id = await svc.create_schedule(
            export_type="csv",
            cadence="weekly",
            metric_selection=["engagement_rate"],
        )
        assert isinstance(schedule_id, str)

    async def test_list_schedules_returns_list(self):
        svc = ExportService()
        schedules = await svc.list_schedules()
        assert isinstance(schedules, list)

    async def test_delete_schedule_removes_it(self):
        svc = ExportService()
        # Should not raise
        await svc.delete_schedule("schedule_123")
        schedules = await svc.list_schedules()
        remaining_ids = [s.get("id") for s in schedules]
        assert "schedule_123" not in remaining_ids

    async def test_delete_nonexistent_schedule_handled(self):
        svc = ExportService()
        # Should not raise for nonexistent
        await svc.delete_schedule("nonexistent_id")
