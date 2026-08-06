"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertIcon, ChartIcon, SparkleIcon } from "@/components/icons";
import { Spinner } from "@/components/ui";
import { PlatformConnectionList } from "@/components/publish/PlatformConnection";
import { fetchPlatforms } from "@/lib/publish";
import type { PlatformInfo } from "@/lib/publish";

export default function ConnectionsPage() {
  const [platforms, setPlatforms] = useState<PlatformInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchPlatforms()
      .then((list) => {
        if (!cancelled) setPlatforms(list);
      })
      .catch((err) => {
        if (!cancelled)
          setError(
            err instanceof Error ? err.message : "Failed to load platforms."
          );
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="min-h-screen bg-canvas pb-12">
      <header className="sticky top-0 z-20 border-b border-line-subtle bg-panel/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1100px] flex-wrap items-center gap-x-6 gap-y-3 px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-[7px] bg-brand text-white">
              <SparkleIcon className="h-4.5 w-4.5" />
            </div>
            <div className="leading-tight">
              <div className="text-[13px] font-semibold tracking-[-0.01em] text-ink">
                Repurpose AI
              </div>
              <div className="text-[11px] text-ink-faint">Connections</div>
            </div>
          </div>

          <nav className="ml-auto flex items-center gap-1" aria-label="Primary">
            <Link
              href="/repurpose"
              className="rounded-[6px] px-3 py-1.5 text-[13px] font-medium text-ink-muted transition-colors hover:text-ink-soft"
            >
              Repurpose
            </Link>
            <Link
              href="/"
              className="rounded-[6px] px-3 py-1.5 text-[13px] font-medium text-ink-muted transition-colors hover:text-ink-soft"
            >
              <span className="inline-flex items-center gap-1.5">
                <ChartIcon className="h-3.5 w-3.5" />
                Analytics
              </span>
            </Link>
          </nav>
        </div>
      </header>

      <div className="mx-auto max-w-[1100px] space-y-4 px-5 pt-6">
        <div>
          <h1 className="text-[20px] font-medium tracking-[-0.02em] text-ink">
            Platform connections
          </h1>
          <p className="mt-1 text-[13px] text-ink-muted">
            Connect publishing platforms to enable them as publish destinations.
            Your content can then be published to LinkedIn, Twitter/X, Medium,
            and Instagram.
          </p>
        </div>

        {error ? (
          <div
            role="alert"
            className="flex items-center gap-2 rounded-[6px] border border-danger/30 bg-danger/5 px-4 py-2.5 text-[13px] text-danger"
          >
            <AlertIcon className="h-4 w-4 shrink-0" />
            {error}
          </div>
        ) : platforms ? (
          <div className="rounded-card border border-line bg-surface/60">
            <div className="border-b border-line-subtle px-5 py-4">
              <h2 className="text-[15px] font-medium tracking-[-0.01em] text-ink">
                Publishing destinations
              </h2>
              <p className="mt-0.5 text-[13px] leading-relaxed text-ink-muted">
                Authorize each platform with OAuth2 to start publishing there.
              </p>
            </div>
            <div className="p-5">
              <PlatformConnectionList />
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-[13px] text-ink-muted">
            <Spinner className="h-3.5 w-3.5" />
            Loading platforms…
          </div>
        )}
      </div>
    </main>
  );
}
