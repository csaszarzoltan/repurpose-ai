"use client";

import { ChevronDownIcon, DownloadIcon, RefreshIcon, SparkleIcon } from "@/components/icons";
import { Button } from "@/components/ui";
import { cls } from "@/lib/format";

export interface PlatformOption {
  value: string;
  label: string;
  color: string;
}

export const PLATFORM_OPTIONS: PlatformOption[] = [
  { value: "all", label: "All platforms", color: "#8a8f98" },
  { value: "twitter", label: "X / Twitter", color: "#8a8f98" },
  { value: "linkedin", label: "LinkedIn", color: "#0a66c2" },
  { value: "medium", label: "Medium", color: "#d0d6e0" },
];

export function PlatformSelect({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        aria-label="Filter by platform"
        className={cls(
          "appearance-none rounded-[6px] border border-line bg-white/[0.02] py-2 pl-3.5 pr-9",
          "text-[13px] font-medium text-ink-soft outline-none transition-colors",
          "hover:bg-white/[0.04] focus:border-brand/50 disabled:opacity-50",
          "[&>option]:bg-panel [&>option]:text-ink-soft"
        )}
      >
        {PLATFORM_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <ChevronDownIcon className="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-faint" />
    </div>
  );
}

export function Header({
  platform,
  onPlatformChange,
  onExport,
  onRefresh,
  loading,
  platformCounts,
}: {
  platform: string;
  onPlatformChange: (value: string) => void;
  onExport: () => void;
  onRefresh: () => void;
  loading: boolean;
  platformCounts: Record<string, number>;
}) {
  const countsLabel =
    platform === "all"
      ? Object.entries(platformCounts)
          .filter(([, n]) => n > 0)
          .map(([p, n]) => `${p} ${n}`)
          .join(" · ")
      : undefined;

  return (
    <header className="sticky top-0 z-20 border-b border-line-subtle bg-panel/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1280px] flex-wrap items-center gap-x-6 gap-y-3 px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-[7px] bg-brand text-white">
            <SparkleIcon className="h-4.5 w-4.5" />
          </div>
          <div className="leading-tight">
            <div className="text-[13px] font-semibold tracking-[-0.01em] text-ink">
              Repurpose AI
            </div>
            <div className="text-[11px] text-ink-faint">Analytics</div>
          </div>
        </div>

        <div className="hidden h-6 w-px bg-line-subtle md:block" />

        <div className="flex items-center gap-2.5">
          <PlatformSelect value={platform} onChange={onPlatformChange} disabled={loading} />
          {countsLabel ? (
            <span className="hidden text-[11px] text-ink-faint sm:inline">{countsLabel}</span>
          ) : null}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <Button onClick={onRefresh} disabled={loading} variant="subtle" ariaLabel="Refresh data">
            <RefreshIcon className={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
            <span className="hidden sm:inline">Refresh</span>
          </Button>
          <Button onClick={onExport} variant="primary" ariaLabel="Export analytics">
            <DownloadIcon className="h-4 w-4" />
            Export
          </Button>
        </div>
      </div>
    </header>
  );
}
