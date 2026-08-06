"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { AlertIcon, CheckIcon } from "@/components/icons";
import { Spinner } from "@/components/ui";
import { exchangeCode } from "@/lib/publish";

export default function OAuthCallbackPage() {
  const params = useParams<{ platform: string }>();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [message, setMessage] = useState("");

  const handleCallback = useCallback(async () => {
    const platform = params.platform;
    const code = searchParams.get("code");
    const error = searchParams.get("error");
    const errorDescription = searchParams.get("error_description");

    // Meta returns errors like "access_denied" or "user_cancelled"
    if (error) {
      setStatus("error");
      setMessage(
        errorDescription ||
          (error === "access_denied"
            ? "You denied the Instagram connection request."
            : `Authorization failed: ${error}`)
      );
      return;
    }

    if (!platform || !code) {
      setStatus("error");
      setMessage("Missing platform or authorization code in the callback URL.");
      return;
    }

    try {
      // Reconstruct the exact redirect_uri used to initiate the flow.
      // Providers require the token-exchange redirect_uri to match the
      // authorize request byte for byte, so rebuild the query-free URL
      // (the platform lives in the route segment).
      const origin = window.location.origin;
      const redirectUri = `${origin}/publish/${platform}/callback`;
      await exchangeCode(
        platform,
        code,
        searchParams.get("state") ?? undefined,
        redirectUri
      );
      setStatus("success");
      setMessage(`${platform} connected successfully.`);
    } catch (err) {
      setStatus("error");
      setMessage(
        err instanceof Error ? err.message : "Failed to exchange the authorization code."
      );
    }
  }, [params.platform, searchParams]);

  useEffect(() => {
    void handleCallback();
  }, [handleCallback]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-6">
      <div className="w-full max-w-sm rounded-card border border-line bg-surface p-8 text-center">
        {status === "loading" ? (
          <div className="flex flex-col items-center gap-4">
            <Spinner className="h-6 w-6" />
            <p className="text-[14px] text-ink-muted">
              Exchanging the authorization code…
            </p>
          </div>
        ) : status === "success" ? (
          <div className="flex flex-col items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500">
              <CheckIcon className="h-6 w-6" />
            </div>
            <h1 className="text-[18px] font-medium text-ink">Connected!</h1>
            <p className="text-[13px] text-ink-muted">
              {message} You can now publish content to this platform.
            </p>
            <div className="mt-4 flex flex-col gap-2">
              <Link
                href="/repurpose"
                className="inline-flex items-center justify-center gap-1.5 rounded-[6px] bg-brand px-3.5 py-2 text-[13px] font-medium text-white transition-colors hover:bg-brand-hover"
              >
                Back to Repurpose
              </Link>
              <Link
                href="/connections"
                className="inline-flex items-center justify-center gap-1.5 rounded-[6px] border border-line bg-white/[0.02] px-3.5 py-2 text-[13px] font-medium text-ink-soft transition-colors hover:text-ink"
              >
                View connections
              </Link>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-danger/10 text-danger">
              <AlertIcon className="h-6 w-6" />
            </div>
            <h1 className="text-[18px] font-medium text-ink">
              Connection failed
            </h1>
            <p className="text-[13px] text-ink-muted">{message}</p>
            <div className="mt-4 flex flex-col gap-2">
              <Link
                href="/repurpose"
                className="inline-flex items-center justify-center gap-1.5 rounded-[6px] bg-brand px-3.5 py-2 text-[13px] font-medium text-white transition-colors hover:bg-brand-hover"
              >
                Back to Repurpose
              </Link>
              <Link
                href="/connections"
                className="inline-flex items-center justify-center gap-1.5 rounded-[6px] border border-line bg-white/[0.02] px-3.5 py-2 text-[13px] font-medium text-ink-soft transition-colors hover:text-ink"
              >
                Retry connection
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
