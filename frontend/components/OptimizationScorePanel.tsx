"use client";

import { useState } from "react";
import type { OptimizationScore, PostMetrics } from "@/lib/api";
import { calculateOptimizationScore } from "@/lib/api";
import { full, platformLabel, pct, scoreTone } from "@/lib/format";
import { Badge, Button, Card, CardHeader, ProgressBar, Spinner } from "@/components/ui";
import { ZapIcon } from "@/components/icons";

const SIGNAL_LABELS: Record<string, string> = {
  engagement_rate: "Engagement rate",
  completion_rate: "Completion rate",
  share_rate: "Share rate",
};

export function OptimizationScorePanel({
  posts,
  selectedId,
  onSelectPost,
}: {
  posts: PostMetrics[];
  selectedId: string | null;
  onSelectPost: (id: string) => void;
}) {
  const [score, setScore] = useState<OptimizationScore | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selected = posts.find((p) => p.post_id === selectedId) ?? null;

  async function run() {
    if (!selected) return;
    setLoading(true);
    setError(null);
    setScore(null);
    try {
      const metrics: Record<string, number> = {
        engagement_rate: selected.engagement_rate ?? 0,
        completion_rate: selected.completion_rate ?? 0,
        share_rate: selected.share_rate ?? 0,
      };
      const result = await calculateOptimizationScore(selected.platform || "linkedin", metrics);
      setScore(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scoring failed");
    } finally {
      setLoading(false);
    }
  }

  const tone = score ? scoreTone(score.overall_score) : null;

  return (
    <Card>
      <CardHeader
        title="Optimization score"
        subtitle="Algorithm-readiness 0–100, computed live via the optimization-score API"
        right={
          <div className="flex items-center gap-2">
            <select
              value={selectedId ?? ""}
              onChange={(e) => {
                onSelectPost(e.target.value);
                setScore(null);
              }}
              aria-label="Choose a post to score"
              className="max-w-[180px] appearance-none rounded-[6px] border border-line bg-white/[0.02] px-2.5 py-1.5 text-[12px] text-ink-soft outline-none hover:bg-white/[0.04] focus:border-brand/50 [&>option]:bg-panel"
            >
              <option value="" disabled>
                Select a post…
              </option>
              {posts.slice(0, 12).map((p) => (
                <option key={p.post_id} value={p.post_id}>
                  {p.post_id}
                </option>
              ))}
            </select>
            <Button onClick={run} disabled={!selected || loading} variant="primary" ariaLabel="Calculate score">
              <ZapIcon className="h-3.5 w-3.5" />
              {loading ? <Spinner className="h-3.5 w-3.5 border-line border-t-white" /> : "Score it"}
            </Button>
          </div>
        }
      />
      <div className="px-5 py-4">
        {!selected ? (
          <div className="py-6 text-center text-[13px] text-ink-muted">
            Pick a post from top content (or the dropdown) to calculate its optimization score.
          </div>
        ) : error ? (
          <div className="rounded-[6px] border border-danger/30 bg-danger/5 px-3.5 py-3 text-[13px] text-danger">
            {error}
          </div>
        ) : !score ? (
          <div className="py-6 text-center text-[13px] text-ink-muted">
            <div className="mb-1 font-mono text-[12px] text-ink-soft">{selected.post_id}</div>
            {platformLabel(selected.platform)} · engagement {pct(selected.engagement_rate)} · completion{" "}
            {pct(selected.completion_rate)}
            <div className="mt-1 text-[12px] text-ink-faint">Press “Score it” to run the live calculation.</div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[32px] font-medium leading-none tracking-[-0.03em] text-ink">
                  {full(Math.round(score.overall_score))}
                  <span className="text-[16px] text-ink-faint">/100</span>
                </div>
                {tone ? (
                  <div className="mt-1.5">
                    <Badge tone={tone.color === "#27a644" ? "success" : tone.color === "#f5a524" ? "warning" : "danger"}>
                      {tone.label}
                    </Badge>
                  </div>
                ) : null}
              </div>
              <div className="text-right text-[12px] text-ink-faint">
                <div>{platformLabel(score.platform)}</div>
                <div>{score.calculated_at ? new Date(score.calculated_at).toLocaleTimeString() : ""}</div>
              </div>
            </div>
            <div className="space-y-2.5">
              {Object.entries(score.signals ?? {})
                .filter(([k]) => k in SIGNAL_LABELS)
                .map(([key, value]) => (
                  <div key={key} className="flex items-center gap-3">
                    <span className="w-32 shrink-0 text-[12px] text-ink-muted">{SIGNAL_LABELS[key]}</span>
                    <ProgressBar value={typeof value === "number" ? value * 100 : 0} />
                    <span className="w-12 shrink-0 text-right text-[12px] font-medium text-ink-soft">
                      {typeof value === "number" ? `${(value * 100).toFixed(0)}%` : "—"}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
