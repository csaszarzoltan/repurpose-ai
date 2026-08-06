"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckIcon } from "@/components/icons";
import { Spinner } from "@/components/ui";
import { cls } from "@/lib/format";
import {
  fetchPlatforms,
  isPlatformConnected,
  type PlatformInfo,
} from "@/lib/publish";

interface DestinationSelectorProps {
  selected: string[];
  onToggle: (platform: string) => void;
  loading?: boolean;
  error?: string | null;
}

/**
 * Destination selector for publishing content to platforms.
 * Renders a list of available platforms with checkboxes for selection.
 * Shows connection status (connected/disconnected) for each platform.
 * Instagram is included alongside LinkedIn, Twitter, and Medium.
 */
export function DestinationSelector({
  selected,
  onToggle,
  loading: externalLoading,
  error: externalError,
}: DestinationSelectorProps) {
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [connections, setConnections] = useState<Record<string, boolean>>({});
  const [loadingPlatforms, setLoadingPlatforms] = useState(true);
  const [loadingConnections, setLoadingConnections] = useState(true);

  // Load platforms on mount
  useEffect(() => {
    let cancelled = false;
    async function loadPlatforms() {
      try {
        const list = await fetchPlatforms();
        if (!cancelled) setPlatforms(list);
      } catch {
        if (!cancelled) setPlatforms([]);
      } finally {
        if (!cancelled) setLoadingPlatforms(false);
      }
    }
    void loadPlatforms();
    return () => {
      cancelled = true;
    };
  }, []);

  // Load connection status for each platform
  useEffect(() => {
    let cancelled = false;
    async function loadConnections() {
      if (platforms.length === 0) return;

      const connMap: Record<string, boolean> = {};
      await Promise.all(
        platforms.map(async (p) => {
          try {
            connMap[p.name] = await isPlatformConnected(p.name);
          } catch {
            connMap[p.name] = false;
          }
        })
      );

      if (!cancelled) {
        setConnections(connMap);
        setLoadingConnections(false);
      }
    }
    void loadConnections();
    return () => {
      cancelled = true;
    };
  }, [platforms]);

  const loading = externalLoading || loadingPlatforms;
  const error = externalError;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-baseline gap-2">
          <span className="text-[13px] font-medium text-ink">
            Publish destinations
          </span>
          <span className="text-[11px] text-ink-faint">
            Where should this content be published?
          </span>
        </div>
        {selected.length > 0 ? (
          <span className="text-[12px] font-medium text-ink-soft">
            {selected.length} selected
          </span>
        ) : null}
      </div>

      {loading ? (
        <div className="flex items-center gap-2 rounded-[6px] border border-line bg-white/[0.02] px-3.5 py-3 text-[13px] text-ink-muted">
          <Spinner className="h-3.5 w-3.5" />
          Loading platforms…
        </div>
      ) : error ? (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-[6px] border border-danger/30 bg-danger/5 px-3.5 py-3 text-[13px] text-danger"
        >
          {error}
        </div>
      ) : platforms.length === 0 ? (
        <div className="text-[13px] text-ink-faint">
          No platforms available. Connect at least one platform to start publishing.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
          {platforms.map((platform) => {
            const active = selected.includes(platform.name);
            const connected = connections[platform.name] ?? false;

            return (
              <label
                key={platform.name}
                className={cls(
                  "flex cursor-pointer items-start gap-2.5 rounded-[6px] border px-3.5 py-2.5 transition-colors",
                  active
                    ? "border-brand/50 bg-brand/5"
                    : "border-line bg-white/[0.02] hover:bg-white/[0.04]"
                )}
              >
                <input
                  type="checkbox"
                  checked={active}
                  onChange={() => onToggle(platform.name)}
                  disabled={!connected}
                  className="sr-only"
                />
                <span
                  aria-hidden
                  className={cls(
                    "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-[4px] border transition-colors",
                    active
                      ? "border-brand bg-brand text-white"
                      : "border-line bg-white/[0.02] text-transparent"
                  )}
                >
                  <CheckIcon className="h-3 w-3" />
                </span>
                <span className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={
                        active ? "text-[13px] font-medium text-ink" : "text-[13px] text-ink-soft"
                      }
                    >
                      {platform.display_name}
                    </span>
                    {!connected && (
                      <span className="rounded-full bg-warning/10 px-1.5 py-0.5 text-[10px] font-medium text-warning">
                        Not connected
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] leading-relaxed text-ink-faint">
                    {platform.post_type}
                  </span>
                </span>
              </label>
            );
          })}
        </div>
      )}

      {selected.length > 0 && (
        <p className="text-[11px] text-ink-faint">
          Only connected platforms can be selected. Connect platforms in Settings → Connections.
        </p>
      )}
    </div>
  );
}
