"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { AnalyticsSummary, PostMetrics, TopContentItem, TrendData } from "@/lib/api";
import {
  fetchPosts,
  fetchSummary,
  fetchTopContent,
  fetchTrend,
  fetchTrendsSummary,
} from "@/lib/api";
import { aggregateTrend } from "@/lib/trends";
import { Header } from "@/components/Header";
import { SummaryCards, deriveSummary } from "@/components/SummaryCards";
import { TrendChart } from "@/components/TrendChart";
import { TopContentTable } from "@/components/TopContentTable";
import { OptimizationScorePanel } from "@/components/OptimizationScorePanel";
import { ValidationGapsPanel } from "@/components/ValidationGapsPanel";
import { ExportDialog } from "@/components/ExportDialog";
import { EmptyState } from "@/components/EmptyState";
import { Spinner } from "@/components/ui";
import { AlertIcon } from "@/components/icons";

type MetricKey = "reach" | "impressions" | "engagement_rate";

interface Loaded {
  posts: PostMetrics[];
  summary: AnalyticsSummary;
  trendsSummary: { total_posts: number; total_reach: number; avg_engagement_rate: number; top_platform: string };
  topContent: TopContentItem[];
  trend: TrendData;
}

export default function AnalyticsDashboard() {
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [platform, setPlatform] = useState("all");
  const [metric, setMetric] = useState<MetricKey>("reach");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [exportOpen, setExportOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [posts, summary, trendsSummary, topContent, trend] = await Promise.all([
        fetchPosts(),
        fetchSummary(),
        fetchTrendsSummary(),
        fetchTopContent("reach", 8),
        fetchTrend("reach", "daily"),
      ]);
      setLoaded({ posts, summary, trendsSummary, topContent, trend });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analytics data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // Platform-filtered view — the API itself is platform-agnostic on the list
  // routes, so filtering happens client-side over the real fetched data.
  const filteredPosts = useMemo(() => {
    if (!loaded) return [];
    return platform === "all"
      ? loaded.posts
      : loaded.posts.filter((p) => p.platform.toLowerCase() === platform.toLowerCase());
  }, [loaded, platform]);

  const postsById = useMemo(() => {
    const map = new Map<string, PostMetrics>();
    for (const p of filteredPosts) map.set(p.post_id, p);
    return map;
  }, [filteredPosts]);

  const derived = useMemo(
    () =>
      deriveSummary(
        filteredPosts,
        platform === "all" ? loaded?.trendsSummary ?? null : null
      ),
    [filteredPosts, loaded, platform]
  );

  const displayTrend = useMemo<TrendData | null>(() => {
    if (!loaded) return null;
    if (platform === "all") return loaded.trend; // refetched from the API on metric change
    return aggregateTrend(filteredPosts, metric);
  }, [loaded, platform, metric, filteredPosts]);

  const displayTopContent = useMemo<TopContentItem[]>(() => {
    // Default view uses the live /trends/top-content ranking; filtered or
    // re-metriced views rank the real fetched posts client-side.
    if (platform === "all" && metric === "reach" && loaded) {
      return loaded.topContent;
    }
    const ranked = [...filteredPosts].sort(
      (a, b) => (b[metric as keyof PostMetrics] as number) - (a[metric as keyof PostMetrics] as number)
    );
    return ranked.slice(0, 8).map((p) => ({
      post_id: p.post_id,
      [metric]: (p[metric as keyof PostMetrics] as number | null) ?? 0,
    }));
  }, [platform, metric, filteredPosts, loaded]);

  const platformCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const p of loaded?.posts ?? []) {
      const key = p.platform || "unknown";
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return counts;
  }, [loaded]);

  const availablePlatforms = useMemo(
    () => [...new Set((loaded?.posts ?? []).map((p) => p.platform).filter(Boolean))],
    [loaded]
  );

  async function onMetricChange(next: MetricKey) {
    setMetric(next);
    if (!loaded) return;
    // Re-fetch the server series for the default (all-platforms) view.
    try {
      const trend = await fetchTrend(next, "daily");
      setLoaded((prev) => (prev ? { ...prev, trend } : prev));
    } catch {
      // keep current data; the client-derived series covers filtered views
    }
  }

  if (loading && !loaded) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-canvas">
        <Spinner className="h-6 w-6" />
        <div className="text-[13px] text-ink-muted">Loading analytics…</div>
      </div>
    );
  }

  if (error && !loaded) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 bg-canvas">
        <div className="flex items-center gap-2 rounded-[6px] border border-danger/30 bg-danger/5 px-4 py-3 text-[13px] text-danger">
          <AlertIcon className="h-4 w-4" />
          {error}
        </div>
        <button
          onClick={() => void load()}
          className="text-[13px] font-medium text-brand-bright hover:text-brand-hover"
        >
          Try again
        </button>
      </div>
    );
  }

  if (loaded && loaded.posts.length === 0) {
    return (
      <main className="min-h-screen bg-canvas">
        <Header
          platform={platform}
          onPlatformChange={setPlatform}
          onExport={() => setExportOpen(true)}
          onRefresh={() => void load()}
          loading={loading}
          platformCounts={platformCounts}
        />
        <EmptyState onExplore={() => void load()} />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-canvas pb-12">
      <Header
        platform={platform}
        onPlatformChange={setPlatform}
        onExport={() => setExportOpen(true)}
        onRefresh={() => void load()}
        loading={loading}
        platformCounts={platformCounts}
      />

      <div className="mx-auto max-w-[1280px] space-y-4 px-5 pt-5">
        {error ? (
          <div className="flex items-center gap-2 rounded-[6px] border border-danger/30 bg-danger/5 px-4 py-2.5 text-[13px] text-danger">
            <AlertIcon className="h-4 w-4" />
            {error} — showing last known data.
          </div>
        ) : null}

        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <h1 className="text-[20px] font-medium tracking-[-0.02em] text-ink">Analytics overview</h1>
            <p className="text-[12px] text-ink-faint">
              {platform === "all" ? "All platforms" : platform} · {derived.totalPosts}{" "}
              {derived.totalPosts === 1 ? "post" : "posts"} · live from the analytics API
            </p>
          </div>
        </div>

        <SummaryCards posts={filteredPosts} summary={loaded?.summary ?? null} derived={derived} />

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
          <div className="space-y-4 xl:col-span-3">
            <TrendChart
              trend={displayTrend}
              loading={loading}
              metric={metric}
              onMetricChange={(m) => void onMetricChange(m)}
            />
            <ValidationGapsPanel posts={filteredPosts} />
          </div>
          <div className="space-y-4 xl:col-span-2">
            <OptimizationScorePanel posts={filteredPosts} selectedId={selectedId} onSelectPost={setSelectedId} />
            <TopContentTable
              items={displayTopContent}
              metric={metric}
              postsById={postsById}
              onSelect={setSelectedId}
              selectedId={selectedId}
            />
          </div>
        </div>
      </div>

      <ExportDialog
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        platform={platform}
        platforms={availablePlatforms}
      />
    </main>
  );
}
