"use client";

import { SparkleIcon, ChartIcon, LinkIcon, ZapIcon, DownloadIcon } from "@/components/icons";
import { Button } from "@/components/ui";

const STEPS = [
  {
    icon: <LinkIcon className="h-4 w-4" />,
    title: "Connect a platform",
    body: "Authorize X / Twitter, LinkedIn, or Medium to start collecting your post metrics.",
  },
  {
    icon: <ChartIcon className="h-4 w-4" />,
    title: "Watch your content perform",
    body: "Reach, impressions, engagement, and trends land here automatically as posts publish.",
  },
  {
    icon: <ZapIcon className="h-4 w-4" />,
    title: "Score and validate",
    body: "Get an algorithm-readiness score per post and check drafts against what actually shipped.",
  },
  {
    icon: <DownloadIcon className="h-4 w-4" />,
    title: "Export whenever you need",
    body: "One-click CSV or PDF reports for your team, your client, or your own archive.",
  },
];

export function EmptyState({ onExplore }: { onExplore: () => void }) {
  return (
    <div className="flex flex-col items-center px-6 py-16 text-center sm:py-24">
      <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-panel border border-brand/40 bg-brand/10 text-brand-bright">
        <SparkleIcon className="h-6 w-6" />
      </div>
      <h1 className="max-w-xl text-[28px] font-medium leading-tight tracking-[-0.02em] text-ink sm:text-[32px]">
        Your content analytics, in one place
      </h1>
      <p className="mt-3 max-w-lg text-[15px] leading-relaxed text-ink-muted">
        Repurpose AI tracks how your repurposed content performs across platforms — reach, impressions,
        engagement, optimization scores, and validation quality — so you can double down on what works.
      </p>

      <div className="mt-10 grid w-full max-w-3xl grid-cols-1 gap-3 sm:grid-cols-2">
        {STEPS.map((step, i) => (
          <div
            key={step.title}
            className="flex gap-3.5 rounded-card border border-line bg-surface/60 px-5 py-4 text-left"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[7px] border border-line bg-white/[0.03] text-ink-soft">
              {step.icon}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] text-ink-faint">0{i + 1}</span>
                <h3 className="text-[14px] font-medium text-ink">{step.title}</h3>
              </div>
              <p className="mt-1 text-[12px] leading-relaxed text-ink-muted">{step.body}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
        <Button variant="primary" onClick={onExplore} ariaLabel="Connect a platform">
          <LinkIcon className="h-4 w-4" />
          Connect a platform
        </Button>
        <Button variant="ghost" onClick={onExplore} ariaLabel="View demo data">
          <ChartIcon className="h-4 w-4" />
          View demo data
        </Button>
      </div>
      <p className="mt-6 max-w-md text-[12px] leading-relaxed text-ink-faint">
        No data is needed to get started — the dashboard lights up as soon as your first post is collected
        by the analytics pipeline.
      </p>
    </div>
  );
}
