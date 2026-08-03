"use client";

import { useEffect, useState } from "react";
import { exportCsv, exportPdf } from "@/lib/api";
import { Button, Spinner } from "@/components/ui";
import { CloseIcon, DownloadIcon, FileTextIcon, CheckIcon } from "@/components/icons";
import { cls } from "@/lib/format";

const METRIC_OPTIONS = [
  { key: "reach", label: "Reach" },
  { key: "impressions", label: "Impressions" },
  { key: "engagement_rate", label: "Engagement rate" },
  { key: "completion_rate", label: "Completion rate" },
  { key: "share_rate", label: "Share rate" },
];

export function ExportDialog({
  open,
  onClose,
  platform,
  platforms,
}: {
  open: boolean;
  onClose: () => void;
  platform: string;
  platforms: string[];
}) {
  const [format, setFormat] = useState<"csv" | "pdf">("csv");
  const [metrics, setMetrics] = useState<string[]>(["reach", "impressions"]);
  const [platformFilter, setPlatformFilter] = useState<string>(platform === "all" ? "all" : platform);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Close on Escape for keyboard accessibility.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  function toggleMetric(key: string) {
    setMetrics((prev) =>
      prev.includes(key) ? prev.filter((m) => m !== key) : [...prev, key]
    );
    setDone(null);
  }

  async function run() {
    if (metrics.length === 0) {
      setError("Select at least one metric.");
      return;
    }
    setBusy(true);
    setError(null);
    setDone(null);
    const options = {
      metric_selection: metrics,
      platform_filter: platformFilter === "all" ? null : platformFilter,
    };
    try {
      if (format === "csv") {
        // The export endpoint returns JSON {export_id, status, content} — the
        // CSV text lives in `content`. Rebuild the file client-side so the
        // downloaded artifact is the real CSV, not a JSON wrapper.
        const data = await exportCsv(options);
        const blob = new Blob([data.content ?? ""], { type: "text/csv;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `repurpose-ai-analytics-${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        setDone(`CSV downloaded (${(blob.size / 1024).toFixed(1)} KB).`);
      } else {
        const data = await exportPdf(options);
        setDone(`PDF report generated — server path: ${data.file_path ?? data.export_id ?? "unknown"}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Export analytics"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-panel border border-line bg-panel shadow-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line-subtle px-5 py-4">
          <div>
            <h2 className="text-[15px] font-medium text-ink">Export analytics</h2>
            <p className="mt-0.5 text-[12px] text-ink-muted">
              Select platform → choose metrics → download the report
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-[6px] p-1.5 text-ink-faint transition-colors hover:bg-white/[0.05] hover:text-ink"
            aria-label="Close export dialog"
          >
            <CloseIcon className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4 px-5 py-4">
          {/* Format */}
          <div>
            <span className="mb-1.5 block text-[12px] font-medium text-ink-soft">Format</span>
            <div className="flex gap-1 rounded-[6px] border border-line bg-white/[0.02] p-0.5">
              {(["csv", "pdf"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => {
                    setFormat(f);
                    setDone(null);
                  }}
                  className={cls(
                    "flex-1 rounded-[4px] px-3 py-1.5 text-[12px] font-medium uppercase tracking-wide transition-colors",
                    format === f ? "bg-white/[0.06] text-ink" : "text-ink-faint hover:text-ink-soft"
                  )}
                  aria-pressed={format === f}
                >
                  {f === "csv" ? "CSV" : "PDF"}
                </button>
              ))}
            </div>
          </div>

          {/* Platform filter */}
          <div>
            <span className="mb-1.5 block text-[12px] font-medium text-ink-soft">Platform</span>
            <select
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value)}
              className="w-full appearance-none rounded-[6px] border border-line bg-white/[0.02] px-3 py-2 text-[13px] text-ink-soft outline-none focus:border-brand/50 [&>option]:bg-panel"
              aria-label="Platform filter for export"
            >
              <option value="all">All platforms</option>
              {platforms.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          {/* Metrics */}
          <div>
            <span className="mb-1.5 block text-[12px] font-medium text-ink-soft">Metrics</span>
            <div className="grid grid-cols-2 gap-1.5">
              {METRIC_OPTIONS.map((m) => {
                const active = metrics.includes(m.key);
                return (
                  <button
                    key={m.key}
                    onClick={() => toggleMetric(m.key)}
                    className={cls(
                      "flex items-center justify-between rounded-[6px] border px-3 py-2 text-[12px] transition-colors",
                      active
                        ? "border-brand/50 bg-brand/10 text-ink"
                        : "border-line bg-white/[0.02] text-ink-muted hover:text-ink-soft"
                    )}
                    aria-pressed={active}
                  >
                    {m.label}
                    {active ? <CheckIcon className="h-3.5 w-3.5 text-brand-bright" /> : null}
                  </button>
                );
              })}
            </div>
          </div>

          {error ? (
            <div className="rounded-[6px] border border-danger/30 bg-danger/5 px-3 py-2 text-[12px] text-danger">
              {error}
            </div>
          ) : null}
          {done ? (
            <div className="flex items-center gap-2 rounded-[6px] border border-success/30 bg-success/5 px-3 py-2 text-[12px] text-success">
              <CheckIcon className="h-3.5 w-3.5" />
              {done}
            </div>
          ) : null}
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-line-subtle px-5 py-3.5">
          <Button onClick={onClose} variant="ghost">
            Cancel
          </Button>
          <Button onClick={run} disabled={busy} variant="primary" ariaLabel="Start export">
            {busy ? <Spinner className="h-3.5 w-3.5 border-line border-t-white" /> : format === "csv" ? <DownloadIcon className="h-3.5 w-3.5" /> : <FileTextIcon className="h-3.5 w-3.5" />}
            {busy ? "Exporting…" : `Export ${format.toUpperCase()}`}
          </Button>
        </div>
      </div>
    </div>
  );
}
