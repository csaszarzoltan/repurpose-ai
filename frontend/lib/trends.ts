import type { DataPoint, PostMetrics, TrendData } from "@/lib/api";

/**
 * Client-side trend aggregation, mirroring TrendService.get_trend on the
 * backend (group by day, sum the metric, half-window delta). Used when the
 * dashboard filters the view to a single platform — the API's trend routes
 * are platform-agnostic, so the series is derived from the real post data
 * the API already returned.
 */
export function aggregateTrend(posts: PostMetrics[], metric: string): TrendData {
  const byDay = new Map<string, number>();
  for (const p of posts) {
    const value = p[metric as keyof PostMetrics];
    if (typeof value !== "number" || Number.isNaN(value)) continue;
    const day = (p.post_date ?? "").slice(0, 10) || "unknown";
    byDay.set(day, (byDay.get(day) ?? 0) + value);
  }
  const points: DataPoint[] = [...byDay.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, value]) => ({ date, value }));

  let delta = 0;
  if (points.length >= 2) {
    const mid = Math.floor(points.length / 2);
    const cur = points.slice(mid).map((p) => p.value);
    const prev = points.slice(0, mid).map((p) => p.value);
    const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;
    delta = mean(cur) - mean(prev);
  }
  return { points, period_over_period_delta: delta, metric, granularity: "daily" };
}
