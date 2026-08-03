"use client";

import { useMemo, useState } from "react";
import type { TrendData } from "@/lib/api";
import { compact, shortDay, signedPct } from "@/lib/format";
import { Badge, Card, CardHeader, Spinner } from "@/components/ui";
import { cls } from "@/lib/format";

const METRICS = [
  { key: "reach", label: "Reach", color: "#7170ff" },
  { key: "impressions", label: "Impressions", color: "#10b981" },
  { key: "engagement_rate", label: "Engagement", color: "#f5a524" },
] as const;

type MetricKey = (typeof METRICS)[number]["key"];

const W = 720;
const H = 240;
const PAD = { top: 16, right: 12, bottom: 28, left: 46 };

function buildPath(points: { date: string; value: number }[]) {
  if (points.length === 0) return null;
  const values = points.map((p) => p.value);
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const x = (i: number) =>
    PAD.left + (i / Math.max(points.length - 1, 1)) * (W - PAD.left - PAD.right);
  const y = (v: number) => PAD.top + (1 - (v - min) / range) * (H - PAD.top - PAD.bottom);
  const line = points.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
  const area = `${line} L${x(points.length - 1).toFixed(1)},${H - PAD.bottom} L${x(0).toFixed(1)},${H - PAD.bottom} Z`;
  const ticks = 4;
  const grid = Array.from({ length: ticks + 1 }, (_, i) => {
    const v = min + (range * i) / ticks;
    const yy = y(v);
    return (
      <g key={i}>
        <line x1={PAD.left} x2={W - PAD.right} y1={yy} y2={yy} stroke="rgba(255,255,255,0.05)" strokeWidth={1} />
        <text x={PAD.left - 8} y={yy + 3} textAnchor="end" fontSize={10} fill="#62666d">
          {compact(v)}
        </text>
      </g>
    );
  });
  const xTicks = points.filter((_, i) => i % Math.max(1, Math.ceil(points.length / 8)) === 0);
  return { line, area, grid, xTicks, x, y };
}

export function TrendChart({
  trend,
  loading,
  onMetricChange,
  metric,
}: {
  trend: TrendData | null;
  loading: boolean;
  onMetricChange: (m: MetricKey) => void;
  metric: MetricKey;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const active = METRICS.find((m) => m.key === metric) ?? METRICS[0];
  const shape = useMemo(() => (trend ? buildPath(trend.points) : null), [trend]);

  // The API's period_over_period_delta is a raw mean difference; the badge
  // shows it as a percentage change of the first half of the window.
  const deltaPct = useMemo(() => {
    if (!trend || trend.points.length < 2) return null;
    const mid = Math.floor(trend.points.length / 2);
    const cur = trend.points.slice(mid).map((p) => p.value);
    const prev = trend.points.slice(0, mid).map((p) => p.value);
    const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;
    const prevMean = mean(prev);
    if (prevMean === 0) return null;
    return ((mean(cur) - prevMean) / prevMean) * 100;
  }, [trend]);

  const valueAt = (i: number) => trend?.points[i]?.value ?? null;

  return (
    <Card>
      <CardHeader
        title="Performance trends"
        subtitle="Daily totals from the analytics store — tap a metric to switch series"
        right={
          <div className="flex items-center gap-1 rounded-[6px] border border-line bg-white/[0.02] p-0.5">
            {METRICS.map((m) => (
              <button
                key={m.key}
                onClick={() => onMetricChange(m.key)}
                className={cls(
                  "rounded-[4px] px-2.5 py-1 text-[12px] font-medium transition-colors",
                  metric === m.key ? "bg-white/[0.06] text-ink" : "text-ink-faint hover:text-ink-soft"
                )}
                aria-pressed={metric === m.key}
              >
                {m.label}
              </button>
            ))}
          </div>
        }
      />
      <div className="px-5 pb-4 pt-4">
        <div className="mb-3 flex flex-wrap items-center gap-3">
          <span className="text-[22px] font-medium tracking-[-0.02em] text-ink">
            {trend ? compact(valueAt(trend.points.length - 1)) : "—"}
          </span>
          <Badge tone={deltaPct === null ? "neutral" : deltaPct >= 0 ? "success" : "danger"}>
            {deltaPct === null ? "—" : signedPct(deltaPct)} vs prior period
          </Badge>
          <span className="text-[12px] text-ink-faint">
            {active.label} · {trend?.granularity ?? "daily"}
          </span>
        </div>

        <div className="relative" style={{ minHeight: H }}>
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Spinner />
            </div>
          ) : !trend || trend.points.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
              <div className="text-[13px] text-ink-muted">No trend data for this period yet.</div>
              <div className="text-[12px] text-ink-faint">
                Publish content and it will appear here once collected.
              </div>
            </div>
          ) : shape ? (
            <svg
              viewBox={`0 0 ${W} ${H}`}
              className="w-full"
              role="img"
              aria-label={`${active.label} trend chart`}
              onMouseLeave={() => setHover(null)}
            >
              <defs>
                <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={active.color} stopOpacity={0.28} />
                  <stop offset="100%" stopColor={active.color} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              {shape.grid}
              <path d={shape.area} fill="url(#areaFill)" />
              <path d={shape.line} fill="none" stroke={active.color} strokeWidth={2} strokeLinecap="round" />
              {shape.xTicks.map((p, i) => {
                const xi = shape.x(trend.points.indexOf(p));
                return (
                  <text key={i} x={xi} y={H - 8} textAnchor="middle" fontSize={10} fill="#62666d">
                    {shortDay(p.date)}
                  </text>
                );
              })}
              {hover !== null && trend.points[hover] ? (
                <g>
                  <line
                    x1={shape.x(hover)}
                    x2={shape.x(hover)}
                    y1={PAD.top}
                    y2={H - PAD.bottom}
                    stroke={active.color}
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    opacity={0.6}
                  />
                  <circle cx={shape.x(hover)} cy={shape.y(trend.points[hover].value)} r={4} fill={active.color} />
                </g>
              ) : null}
              {trend.points.map((p, i) => (
                <rect
                  key={i}
                  x={shape.x(i) - (W / trend.points.length / 2)}
                  y={PAD.top}
                  width={W / trend.points.length}
                  height={H - PAD.top - PAD.bottom}
                  fill="transparent"
                  onMouseEnter={() => setHover(i)}
                />
              ))}
            </svg>
          ) : null}
        </div>

        {hover !== null && trend?.points[hover] ? (
          <div className="mt-2 flex items-center gap-3 text-[12px] text-ink-muted">
            <span className="font-medium text-ink">{shortDay(trend.points[hover].date)}</span>
            <span>
              {active.label}: <span className="font-medium text-ink">{compact(trend.points[hover].value)}</span>
            </span>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
