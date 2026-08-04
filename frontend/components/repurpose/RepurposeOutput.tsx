"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, Badge } from "@/components/ui";
import { CheckIcon, FileTextIcon } from "@/components/icons";
import { cls } from "@/lib/format";
import {
  isMultiLanguageOutput,
  type Language,
  type RepurposeResult,
} from "@/lib/repurpose";

/**
 * Renders the repurpose response.
 *
 * - No target languages requested → legacy single-language view: one card per
 *   format with the plain content (unchanged behavior).
 * - Target languages requested → per-format cards, each with per-language
 *   tabs (format → language → content).
 */
export function RepurposeOutput({
  result,
  languages,
}: {
  result: RepurposeResult;
  languages: Language[];
}) {
  const entries = Object.entries(result.repurposed);
  if (entries.length === 0) {
    return (
      <p className="rounded-[6px] border border-line bg-white/[0.02] px-4 py-3 text-[13px] text-ink-muted">
        No output was generated. Try again or pick at least one target format.
      </p>
    );
  }

  const byId = new Map(languages.map((l) => [l.id, l]));
  const multi = isMultiLanguageOutput(result.repurposed);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="brand">{multi ? "Multi-language" : "Single language"}</Badge>
        {multi ? (
          <span className="text-[12px] text-ink-faint">
            {entries.length} format{entries.length === 1 ? "" : "s"} · per-language output
          </span>
        ) : (
          <span className="text-[12px] text-ink-faint">
            {entries.length} format{entries.length === 1 ? "" : "s"}
          </span>
        )}
      </div>

      {entries.map(([formatId, value]) => {
        const formatName = humanizeId(formatId);
        if (multi && typeof value === "object" && value !== null) {
          return (
            <FormatCard
              key={formatId}
              formatName={formatName}
              langs={Object.entries(value as Record<string, string>)}
              byId={byId}
            />
          );
        }
        return (
          <FormatCard
            key={formatId}
            formatName={formatName}
            langs={[["source", String(value)]]}
            byId={byId}
          />
        );
      })}

      {result.warnings.length > 0 ? (
        <ul className="space-y-1.5 rounded-[6px] border border-line bg-white/[0.02] px-4 py-3 text-[12px] text-ink-muted">
          {result.warnings.map((w) => (
            <li key={w} className="flex items-start gap-2">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-ink-faint" />
              {w}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function FormatCard({
  formatName,
  langs,
  byId,
}: {
  formatName: string;
  langs: Array<[string, string]>;
  byId: Map<string, Language>;
}) {
  const [active, setActive] = useState(langs[0]?.[0] ?? "source");
  const activeContent = langs.find(([id]) => id === active)?.[1] ?? "";

  // The same FormatCard instance is reused across submits (React keys by
  // format id), so a previously active language can outlive the current
  // langs list — e.g. switching from multi-language output back to the
  // single-language view. Reset to the first available language whenever
  // the active id is no longer present.
  useEffect(() => {
    if (!langs.some(([id]) => id === active)) {
      setActive(langs[0]?.[0] ?? "source");
    }
  }, [langs, active]);

  return (
    <Card className="overflow-hidden">
      <CardHeader
        title={formatName}
        right={
          langs.length > 1 ? (
            <Badge tone="neutral">
              {langs.length} language{langs.length === 1 ? "" : "s"}
            </Badge>
          ) : undefined
        }
      />

      {langs.length > 1 ? (
        <div
          role="tablist"
          aria-label={`Languages for ${formatName}`}
          className="flex flex-wrap gap-1 border-b border-line-subtle px-4 pt-3"
        >
          {langs.map(([id]) => {
            const label = id === "source" ? "Source" : byId.get(id)?.native_name ?? id;
            return (
              <button
                key={id}
                role="tab"
                aria-selected={active === id}
                onClick={() => setActive(id)}
                className={cls(
                  "rounded-t-[4px] border-b-2 px-3 py-1.5 text-[12px] font-medium transition-colors",
                  active === id
                    ? "border-brand-bright text-ink"
                    : "border-transparent text-ink-muted hover:text-ink-soft"
                )}
              >
                {label}
              </button>
            );
          })}
        </div>
      ) : null}

      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <pre className="max-h-96 flex-1 overflow-y-auto whitespace-pre-wrap break-words font-sans text-[13px] leading-relaxed text-ink-soft">
            {activeContent}
          </pre>
          <CopyButton text={activeContent} />
        </div>
      </div>
    </Card>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        void navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1600);
        });
      }}
      aria-label="Copy content"
      className={cls(
        "inline-flex shrink-0 items-center gap-1.5 rounded-[6px] border px-2.5 py-1.5 text-[12px] font-medium transition-colors",
        copied
          ? "border-success/40 text-success"
          : "border-line text-ink-faint hover:text-ink-soft"
      )}
    >
      {copied ? <CheckIcon className="h-3.5 w-3.5" /> : <FileTextIcon className="h-3.5 w-3.5" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

/** "twitter_thread" → "Twitter thread", "blog_post" → "Blog post". */
function humanizeId(id: string): string {
  return id
    .split("_")
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(" ");
}
