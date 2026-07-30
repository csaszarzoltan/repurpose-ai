"""Example: P1.3 & P2.1 — CSV & PDF Export.

Demonstrates ExportService: CSV generation, PDF stubs, schedule management.
"""

import asyncio

from app.services.analytics.export_service import ExportService


async def main() -> None:
    svc = ExportService(data_store=None)

    # ── CSV export ──
    csv_content = await svc.export_csv(
        metric_selection=["engagement_rate", "reach", "follower_growth"],
        date_range=("2026-01-01", "2026-01-31"),
        platform_filter="linkedin",
    )
    print(f"CSV output:\n{csv_content}")

    # ── PDF export (stub) ──
    pdf_path = await svc.export_pdf(
        metric_selection=["engagement_rate"],
        date_range=("2026-01-01", "2026-01-31"),
        brand_config={"theme": "dark", "logo_url": "https://example.com/logo.png"},
    )
    print(f"PDF path: {pdf_path}")

    # ── Export status ──
    status = await svc.get_export_status(export_id="export_1")
    print(f"Export status: {status}")

    not_found = await svc.get_export_status(export_id="nonexistent")
    print(f"Not found: {not_found}")

    # ── Schedule management ──
    schedule_id = await svc.create_schedule(
        export_type="csv",
        cadence="daily",
        metric_selection=["engagement_rate", "reach"],
    )
    print(f"Created schedule: {schedule_id}")

    another = await svc.create_schedule(
        export_type="pdf",
        cadence="weekly",
        metric_selection=["follower_growth"],
    )
    print(f"Created schedule: {another}")

    schedules = await svc.list_schedules()
    print(f"Total schedules: {len(schedules)}")
    for s in schedules:
        print(f"  - {s['export_type']} / {s['cadence']}: {s['metric_selection']}")

    # Delete one
    await svc.delete_schedule(schedule_id=schedule_id)
    remaining = await svc.list_schedules()
    print(f"Schedules after delete: {len(remaining)}")


if __name__ == "__main__":
    asyncio.run(main())
