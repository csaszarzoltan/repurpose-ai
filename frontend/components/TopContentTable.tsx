"use client";

import type { PostMetrics, TopContentItem } from "@/lib/api";
import { compact, pct, platformColor, platformLabel, shortDate } from "@/lib/format";
import { Card, CardHeader } from "@/components/ui";

function PlatformDot({ platform }: { platform: string }) {
  return (
    <span
      className="inline-block h-2 w-2 shrink-0 rounded-full"
      style={{ backgroundColor: platformColor(platform) }}
      aria-hidden
    />
  );
}

export function TopContentTable({
  items,
  metric,
  postsById,
  onSelect,
  selectedId,
}: {
  items: TopContentItem[];
  metric: "reach" | "impressions" | "engagement_rate";
  postsById: Map<string, PostMetrics>;
  onSelect: (postId: string) => void;
  selectedId: string | null;
}) {
  return (
    <Card>
      <CardHeader
        title="Top content"
        subtitle={`Ranked by ${metric === "engagement_rate" ? "engagement rate" : metric} — click a row to score it`}
      />
      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] text-left">
          <thead>
            <tr className="border-b border-line-subtle text-[11px] uppercase tracking-wide text-ink-faint">
              <th className="px-5 py-2.5 font-medium">#</th>
              <th className="px-3 py-2.5 font-medium">Post</th>
              <th className="px-3 py-2.5 font-medium">Platform</th>
              <th className="px-3 py-2.5 text-right font-medium">{metric}</th>
              <th className="px-3 py-2.5 text-right font-medium">Engagement</th>
              <th className="px-5 py-2.5 text-right font-medium">Posted</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center text-[13px] text-ink-muted">
                  No content tracked yet.
                </td>
              </tr>
            ) : (
              items.map((item, idx) => {
                const post = postsById.get(item.post_id);
                const selected = selectedId === item.post_id;
                return (
                  <tr
                    key={item.post_id}
                    onClick={() => onSelect(item.post_id)}
                    className={[
                      "cursor-pointer border-b border-line-subtle/60 transition-colors last:border-0",
                      selected ? "bg-brand/10" : "hover:bg-white/[0.03]",
                    ].join(" ")}
                    aria-selected={selected}
                  >
                    <td className="px-5 py-3 text-[12px] text-ink-faint">{idx + 1}</td>
                    <td className="max-w-[260px] px-3 py-3">
                      <div className="truncate font-mono text-[12px] text-ink-soft">
                        {item.post_id}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <span className="inline-flex items-center gap-1.5 text-[12px] text-ink-muted">
                        <PlatformDot platform={post?.platform ?? ""} />
                        {platformLabel(post?.platform ?? "")}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-right text-[13px] font-medium text-ink">
                      {compact(item[metric] as number | undefined)}
                    </td>
                    <td className="px-3 py-3 text-right text-[12px] text-ink-muted">
                      {pct(post?.engagement_rate ?? null)}
                    </td>
                    <td className="px-5 py-3 text-right text-[12px] text-ink-faint">
                      {shortDate(post?.post_date ?? null)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
