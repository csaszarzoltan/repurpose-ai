"use client";

import type { AnalyticsSummary, PostMetrics } from "@/lib/api";
import { compact, full, pct } from "@/lib/format";
import { Card, Stat } from "@/components/ui";
import { EyeIcon, FileTextIcon, HeartIcon, TargetIcon } from "@/components/icons";

export interface SummaryDerived {
  totalImpressions: number;
  totalEngagement: number;
  totalPosts: number;
  platforms: number;
  topPlatform: string;
}

export function deriveSummary(
  posts: PostMetrics[],
  trendsSummary: { top_platform: string } | null
): SummaryDerived {
  const totalImpressions = posts.reduce((acc, p) => acc + (p.impressions ?? 0), 0);
  const totalEngagement = posts.reduce(
    (acc, p) => acc + (p.impressions ?? 0) * (p.engagement_rate ?? 0),
    0
  );
  const platforms = new Set(posts.map((p) => p.platform).filter(Boolean));
  return {
    totalImpressions,
    totalEngagement,
    totalPosts: posts.length,
    platforms: platforms.size,
    topPlatform: trendsSummary?.top_platform ?? "",
  };
}

export function SummaryCards({
  posts,
  summary,
  derived,
}: {
  posts: PostMetrics[];
  summary: AnalyticsSummary | null;
  derived: SummaryDerived;
}) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <Card className="px-5 py-4">
        <Stat
          label="Total reach"
          icon={<EyeIcon className="h-3.5 w-3.5" />}
          value={compact(summary?.total_reach ?? derived.totalImpressions)}
          sub={
            <span className="text-ink-faint">
              {summary?.period_start ? `since ${summary.period_start.slice(0, 10)}` : "all time"}
            </span>
          }
        />
      </Card>
      <Card className="px-5 py-4">
        <Stat
          label="Impressions"
          icon={<FileTextIcon className="h-3.5 w-3.5" />}
          value={full(derived.totalImpressions)}
          sub={
            <span className="text-ink-faint">
              across {derived.platforms} {derived.platforms === 1 ? "platform" : "platforms"}
            </span>
          }
        />
      </Card>
      <Card className="px-5 py-4">
        <Stat
          label="Engagement rate"
          icon={<HeartIcon className="h-3.5 w-3.5" />}
          value={pct(summary?.avg_engagement_rate ?? 0)}
          sub={
            <span className="text-ink-faint">
              avg across {derived.totalPosts} {derived.totalPosts === 1 ? "post" : "posts"}
            </span>
          }
        />
      </Card>
      <Card className="px-5 py-4">
        <Stat
          label="Posts tracked"
          icon={<TargetIcon className="h-3.5 w-3.5" />}
          value={full(derived.totalPosts)}
          sub={
            <span className="text-ink-faint">
              {derived.topPlatform
                ? `top platform: ${derived.topPlatform}`
                : `${derived.platforms} ${derived.platforms === 1 ? "platform" : "platforms"} tracked`}
            </span>
          }
        />
      </Card>
    </div>
  );
}
