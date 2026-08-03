"""Export service — CSV and PDF report generation (P1.3, P2.1).

Source of truth: analysis/analysis-brief.md §4 P1.3 (CSV), §4 P2.1 (PDF).

CSV exports read rows from the injected ``data_store`` (a MetricsRepository)
so the exported values match what is persisted. PDF exports render a real
(valid, self-contained) one-page PDF document with the selected metrics.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from uuid import uuid4


class ExportService:
    """Generates CSV and PDF exports of analytics data."""

    def __init__(self, data_store=None) -> None:
        self._data_store = data_store
        self._schedules: dict[str, dict] = {}
        self._exports: dict[str, dict] = {}
        self._export_counter: int = 0

    async def _rows(
        self,
        date_range: tuple | list | None,
        platform_filter: str | None,
    ) -> list[dict]:
        """Rows from the data store, filtered by platform and date window."""
        if self._data_store is None:
            return []
        rows = await self._data_store.list_all()
        if platform_filter:
            rows = [r for r in rows if r.get("platform") == platform_filter]
        start, end = self._parse_range(date_range)
        if start is not None or end is not None:
            rows = [r for r in rows if self._in_range(r.get("post_date"), start, end)]
        return rows

    @staticmethod
    def _parse_range(date_range: tuple | list | None) -> tuple:
        if not date_range:
            return None, None
        values = list(date_range)
        start = values[0] if len(values) > 0 else None
        end = values[1] if len(values) > 1 else None
        return start, end

    @staticmethod
    def _in_range(post_date: object, start: object, end: object) -> bool:
        if post_date is None:
            return True
        if start is not None and post_date < start:
            return False
        return not (end is not None and post_date > end)

    @staticmethod
    def _day(post_date: object) -> str:
        if isinstance(post_date, datetime):
            return post_date.date().isoformat()
        return str(post_date)[:10]

    async def export_csv(
        self,
        metric_selection: list[str],
        date_range: tuple,
        platform_filter: str | None = None,
    ) -> str:
        """Generate CSV export of selected metrics over a date range."""
        output = io.StringIO()
        writer = csv.writer(output)
        header = ["date"] + list(metric_selection)
        writer.writerow(header)
        rows = await self._rows(date_range, platform_filter)
        for row in rows:
            values = [row.get(m) if row.get(m) is not None else 0 for m in metric_selection]
            writer.writerow([self._day(row.get("post_date")), *values])
        csv_content = output.getvalue()
        self._export_counter += 1
        export_id = f"export_{self._export_counter}"
        self._exports[export_id] = {"status": "completed", "id": export_id}
        return csv_content

    async def get_export_status(self, export_id: str) -> dict:
        """Get the status of a previously started export."""
        return self._exports.get(export_id, {"status": "not_found", "id": export_id})

    async def export_pdf(
        self,
        metric_selection: list[str],
        date_range: tuple,
        brand_config: dict | None = None,
    ) -> str:
        """Generate a real PDF report and return its file path."""
        self._export_counter += 1
        export_id = f"export_{self._export_counter}"
        self._exports[export_id] = {"status": "completed", "id": export_id}
        rows = await self._rows(date_range, None)
        file_path = f"/tmp/report_{export_id}.pdf"
        _write_pdf(file_path, metric_selection, rows, brand_config)
        return file_path

    async def create_schedule(
        self,
        export_type: str,
        cadence: str,
        metric_selection: list[str],
    ) -> str:
        """Create an export schedule and return its ID."""
        schedule_id = str(uuid4())
        self._schedules[schedule_id] = {
            "id": schedule_id,
            "export_type": export_type,
            "cadence": cadence,
            "metric_selection": metric_selection,
        }
        return schedule_id

    async def delete_schedule(self, schedule_id: str) -> None:
        """Delete an export schedule by ID (no-op if not found)."""
        self._schedules.pop(schedule_id, None)

    async def list_schedules(self) -> list[dict]:
        """List all export schedules."""
        return list(self._schedules.values())


# ── Minimal dependency-free PDF writer ────────────────────────────────────────


def _pdf_text(text: str) -> bytes:
    """Escape a string for a PDF text-showing operator."""
    escaped = (
        text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
    )
    return escaped.encode("latin-1", "replace")


def _write_pdf(
    path: str,
    metric_selection: list[str],
    rows: list[dict],
    brand_config: dict | None = None,
) -> None:
    """Write a small but valid one-page PDF listing the exported rows."""
    lines = [f"Analytics Export — {', '.join(metric_selection) or 'all metrics'}"]
    for row in rows[:50]:
        parts = [str(row.get("post_id", ""))]
        parts.extend(f"{m}={row.get(m, 0)}" for m in metric_selection)
        lines.append("  ".join(parts))
    if not rows:
        lines.append("(no data in range)")

    # Content stream: one text line per report line.
    stream = bytearray(b"BT /F1 10 Tf 72 720 Td\n")
    for line in lines:
        stream += b"(" + _pdf_text(line) + b") Tj\n0 -14 Td\n"
    stream += b"ET"
    content = bytes(stream)

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
            b" /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number
        out += obj
        out += b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += (
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objects) + 1, xref_pos)
    )
    with open(path, "wb") as handle:
        handle.write(bytes(out))
