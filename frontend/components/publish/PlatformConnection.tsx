"use client";

import { useCallback, useEffect, useState } from "react";
import { LinkIcon, CheckIcon, CloseIcon, AlertIcon } from "@/components/icons";
import { Spinner } from "@/components/ui";
import { cls } from "@/lib/format";
import {
  fetchPlatforms,
  getAuthUrl,
  revokeCredentials,
  isPlatformConnected,
  type PlatformInfo,
} from "@/lib/publish";

interface PlatformConnectionProps {
  platform: PlatformInfo;
  onConnect?: (platform: string) => void;
  onDisconnect?: (platform: string) => void;
  disabled?: boolean;
}

export function PlatformConnection({
  platform,
  onConnect,
  onDisconnect,
  disabled,
}: PlatformConnectionProps) {
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check connection status on mount
  useEffect(() => {
    let cancelled = false;
    async function checkConnection() {
      try {
        const isConnected = await isPlatformConnected(platform.name);
        if (!cancelled) setConnected(isConnected);
      } catch {
        if (!cancelled) setConnected(false);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void checkConnection();
    return () => {
      cancelled = true;
    };
  }, [platform.name]);

  const handleConnect = useCallback(async () => {
    if (disabled) return;
    setError(null);
    setConnecting(true);

    // Build callback URL — this is where the OAuth redirect will land.
    // Keep it query-free: the platform lives in the route segment
    // (/publish/<platform>/callback), and the backend auth-url builder
    // does not URL-encode redirect_uri params.
    const origin = window.location.origin;
    const redirectUri = `${origin}/publish/${platform.name}/callback`;

    try {
      const { auth_url } = await getAuthUrl(platform.name, redirectUri);
      // Redirect to the OAuth authorization page
      window.location.href = auth_url;
    } catch (err) {
      const detail =
        err instanceof Error ? err.message : "Failed to start the OAuth flow.";
      setError(
        platform.name === "instagram" && /client_id/i.test(detail)
          ? "Instagram OAuth requires Meta app credentials. Set INSTAGRAM_CLIENT_ID / INSTAGRAM_CLIENT_SECRET on the backend, then retry."
          : detail
      );
    } finally {
      setConnecting(false);
    }
  }, [disabled, platform.name]);

  const handleDisconnect = useCallback(async () => {
    setDisconnecting(true);
    try {
      await revokeCredentials(platform.name);
      setConnected(false);
      onDisconnect?.(platform.name);
    } catch {
      // Ignore errors — assume disconnected
      setConnected(false);
    } finally {
      setDisconnecting(false);
    }
  }, [platform.name, onDisconnect]);

  return (
    <div
      className={cls(
        "flex flex-col rounded-[8px] border px-4 py-3",
        connected
          ? "border-emerald-500/30 bg-emerald-500/5"
          : "border-line bg-white/[0.02]"
      )}
    >
      <div className="flex items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        <div
          className={cls(
            "flex h-8 w-8 items-center justify-center rounded-[6px]",
            connected ? "bg-emerald-500/10" : "bg-white/[0.04]"
          )}
        >
          <PlatformIcon name={platform.name} />
        </div>
        <div>
          <div className="text-[13px] font-medium text-ink">
            {platform.display_name}
          </div>
          <div className="text-[11px] text-ink-faint">
            {platform.post_type}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {loading ? (
          <Spinner className="h-4 w-4" />
        ) : connected ? (
          <>
            <span className="flex items-center gap-1.5 text-[12px] font-medium text-emerald-500">
              <CheckIcon className="h-3.5 w-3.5" />
              Connected
            </span>
            <button
              type="button"
              onClick={() => void handleDisconnect()}
              disabled={disconnecting}
              className="flex items-center gap-1.5 rounded-[6px] border border-danger/30 bg-danger/5 px-2.5 py-1.5 text-[12px] font-medium text-danger transition-colors hover:bg-danger/10 disabled:opacity-50"
            >
              {disconnecting ? (
                <Spinner className="h-3 w-3" />
              ) : (
                <CloseIcon className="h-3 w-3" />
              )}
              Disconnect
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={() => void handleConnect()}
            disabled={disabled || connecting}
            className="flex items-center gap-1.5 rounded-[6px] border border-brand/30 bg-brand/5 px-3 py-1.5 text-[12px] font-medium text-brand transition-colors hover:bg-brand/10 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {connecting ? (
              <Spinner className="h-3 w-3" />
            ) : (
              <LinkIcon className="h-3.5 w-3.5" />
            )}
            {connecting ? "Starting…" : "Connect"}
          </button>
        )}
      </div>
      </div>

      {error ? (
        <div
          role="alert"
          className="col-span-full mt-2 flex items-start gap-2 rounded-[6px] border border-danger/30 bg-danger/5 px-3 py-2 text-[12px] leading-relaxed text-danger"
        >
          <AlertIcon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          {error}
        </div>
      ) : null}
    </div>
  );
}

/**
 * Simple platform icon — returns initials or a styled icon.
 */
function PlatformIcon({ name }: { name: string }) {
  const bgClass = {
    linkedin: "bg-[#0a66c2]/10 text-[#0a66c2]",
    twitter: "bg-white/[0.06] text-ink-soft",
    medium: "bg-[#d0d6e0]/10 text-[#d0d6e0]",
    instagram: "bg-[#E4405F]/10 text-[#E4405F]",
  }[name] ?? "bg-white/[0.04] text-ink-faint";

  const initials = {
    linkedin: "Li",
    twitter: "X",
    medium: "M",
    instagram: "IG",
  }[name] ?? name.charAt(0).toUpperCase();

  return (
    <span
      className={cls(
        "flex h-5 w-5 items-center justify-center rounded-[4px] text-[10px] font-semibold",
        bgClass
      )}
    >
      {initials}
    </span>
  );
}

/**
 * Platform connection list — renders all platforms with connect/disconnect buttons.
 * Used on the settings or connections page.
 */
export function PlatformConnectionList() {
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadPlatforms() {
      try {
        const list = await fetchPlatforms();
        if (!cancelled) setPlatforms(list);
      } catch (err) {
        if (!cancelled)
          setError(
            err instanceof Error ? err.message : "Failed to load platforms."
          );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadPlatforms();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[13px] text-ink-muted">
        <Spinner className="h-3.5 w-3.5" />
        Loading platforms…
      </div>
    );
  }

  if (error) {
    return (
      <div
        role="alert"
        className="flex items-center gap-2 rounded-[6px] border border-danger/30 bg-danger/5 px-3.5 py-3 text-[13px] text-danger"
      >
        {error}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {platforms.map((platform) => (
        <PlatformConnection key={platform.name} platform={platform} />
      ))}
    </div>
  );
}
