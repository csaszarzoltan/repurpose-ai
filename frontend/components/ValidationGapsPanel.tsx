"use client";

import { useState } from "react";
import type { PostMetrics, ValidationReport } from "@/lib/api";
import { runValidation } from "@/lib/api";
import { Badge, Button, Card, CardHeader, ProgressBar, Spinner } from "@/components/ui";
import { AlertIcon, CheckIcon } from "@/components/icons";
import { cls } from "@/lib/format";

const SAMPLE_DRAFT = `AI is transforming how content teams work. This guide shows you how to turn one long-form piece into a week of social posts.`;

const SAMPLE_PUBLISHED = `Artificial intelligence is changing content marketing forever. In this guide, we show you exactly how to repurpose one long-form article into a full week of social media posts.`;

const SAMPLE_SOURCE = `AI transforms content teams by letting them reuse a single long-form asset across every platform.`;

function GapRow({ label, value }: { label: string; value: number | null | undefined }) {
  if (value === null || value === undefined) return null;
  const ok = value <= 0.25;
  return (
    <div className="flex items-center gap-3">
      <span className="w-36 shrink-0 text-[12px] text-ink-muted">{label}</span>
      <ProgressBar value={value * 100} color={ok ? "#10b981" : "#f5a524"} />
      <span className="w-14 shrink-0 text-right text-[12px] font-medium text-ink-soft">
        {(value * 100).toFixed(0)}%
      </span>
    </div>
  );
}

export function ValidationGapsPanel({ posts }: { posts: PostMetrics[] }) {
  const [draft, setDraft] = useState(SAMPLE_DRAFT);
  const [published, setPublished] = useState(SAMPLE_PUBLISHED);
  const [source, setSource] = useState(SAMPLE_SOURCE);
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Derived gap summary from real stored metrics: underperforming posts.
  const avgEngagement =
    posts.length > 0
      ? posts.reduce((a, p) => a + (p.engagement_rate ?? 0), 0) / posts.length
      : 0;
  const laggards = posts.filter((p) => (p.engagement_rate ?? 0) < avgEngagement * 0.6);

  async function run() {
    if (!draft.trim() || !published.trim()) {
      setError("Both the draft and the published version are required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await runValidation({
        draft,
        published,
        source_material: source.trim() || undefined,
        run_llm_judge: false,
      });
      setReport(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setLoading(false);
    }
  }

  const gapGood = report ? report.quality_delta <= 0.25 : null;

  return (
    <Card>
      <CardHeader
        title="Validation gaps"
        subtitle="Quality delta between AI draft and published content — computed by the validation API"
        right={
          <Badge tone={gapGood === null ? "neutral" : gapGood ? "success" : "warning"}>
            {gapGood === null ? "ready" : gapGood ? "aligned" : "gap detected"}
          </Badge>
        }
      />
      <div className="space-y-4 px-5 py-4">
        {posts.length > 0 ? (
          <div className="rounded-[6px] border border-line-subtle bg-white/[0.02] px-3.5 py-2.5 text-[12px] text-ink-muted">
            {laggards.length > 0 ? (
              <span className="inline-flex items-center gap-1.5">
                <AlertIcon className="h-3.5 w-3.5 text-warning" />
                {laggards.length} of {posts.length} posts are underperforming (engagement below 60% of the
                average).
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5">
                <CheckIcon className="h-3.5 w-3.5 text-success" />
                All tracked posts are performing at or above 60% of the average engagement.
              </span>
            )}
          </div>
        ) : null}

        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <label className="block">
            <span className="mb-1.5 block text-[12px] font-medium text-ink-soft">AI draft</span>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={5}
              className="w-full resize-y rounded-[6px] border border-line bg-white/[0.02] px-3 py-2.5 text-[13px] leading-relaxed text-ink-soft outline-none transition-colors placeholder:text-ink-faint focus:border-brand/50"
              placeholder="Paste the AI-generated draft…"
            />
          </label>
          <label className="block">
            <span className="mb-1.5 block text-[12px] font-medium text-ink-soft">Published version</span>
            <textarea
              value={published}
              onChange={(e) => setPublished(e.target.value)}
              rows={5}
              className="w-full resize-y rounded-[6px] border border-line bg-white/[0.02] px-3 py-2.5 text-[13px] leading-relaxed text-ink-soft outline-none transition-colors placeholder:text-ink-faint focus:border-brand/50"
              placeholder="Paste the version that went live…"
            />
          </label>
        </div>
        <label className="block">
          <span className="mb-1.5 block text-[12px] font-medium text-ink-soft">
            Source material <span className="font-normal text-ink-faint">(optional, for faithfulness)</span>
          </span>
          <input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="w-full rounded-[6px] border border-line bg-white/[0.02] px-3 py-2 text-[13px] text-ink-soft outline-none transition-colors placeholder:text-ink-faint focus:border-brand/50"
            placeholder="Original source text…"
          />
        </label>

        <div className="flex items-center gap-3">
          <Button onClick={run} disabled={loading} variant="primary">
            {loading ? <Spinner className="h-3.5 w-3.5 border-line border-t-white" /> : null}
            {loading ? "Validating…" : "Run validation"}
          </Button>
          {error ? <span className="text-[12px] text-danger">{error}</span> : null}
        </div>

        {report ? (
          <div className="space-y-3 rounded-[6px] border border-line-subtle bg-white/[0.02] p-4">
            <div className="flex items-center justify-between">
              <span className="text-[13px] font-medium text-ink">Quality delta</span>
              <span className={cls("text-[20px] font-medium", gapGood ? "text-success" : "text-warning")}>
                {(report.quality_delta * 100).toFixed(0)}%
              </span>
            </div>
            <ProgressBar value={report.quality_delta * 100} color={gapGood ? "#10b981" : "#f5a524"} />
            <div className="grid grid-cols-1 gap-2 pt-1 sm:grid-cols-2">
              <GapRow label="Faithfulness" value={report.faithfulness?.score} />
              <GapRow label="Tone consistency" value={report.tone_consistency?.similarity} />
              <GapRow label="LLM coherence" value={report.llm_judge?.coherence} />
            </div>
            {report.readability ? (
              <div className="pt-1 text-[12px] text-ink-muted">
                Readability — Flesch-Kincaid{" "}
                <span className="font-medium text-ink-soft">{report.readability.flesch_kincaid ?? "—"}</span>
                {" · "}Dale-Chall{" "}
                <span className="font-medium text-ink-soft">{report.readability.dale_chall ?? "—"}</span>
                {" · "}ARI{" "}
                <span className="font-medium text-ink-soft">{report.readability.ari ?? "—"}</span>
              </div>
            ) : null}
            {report.diff_blocks.length > 0 ? (
              <div className="pt-1">
                <div className="mb-1.5 text-[12px] font-medium text-ink-soft">
                  {report.diff_blocks.length} change{report.diff_blocks.length === 1 ? "" : "s"} detected
                </div>
                <div className="max-h-36 space-y-1 overflow-y-auto font-mono text-[11px] leading-relaxed">
                  {report.diff_blocks.map((b, i) => (
                    <div
                      key={i}
                      className={cls(
                        "rounded-[4px] px-2.5 py-1.5",
                        b.type === "insert"
                          ? "bg-success/10 text-success"
                          : b.type === "delete"
                            ? "bg-danger/10 text-danger"
                            : "bg-warning/10 text-warning"
                      )}
                    >
                      {b.type === "delete" ? "− " : b.type === "insert" ? "+ " : "≈ "}
                      {b.content?.trim() || b.original?.trim() || ""}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </Card>
  );
}
