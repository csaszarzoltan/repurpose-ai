"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertIcon, ChartIcon, CheckIcon, SparkleIcon } from "@/components/icons";
import { Button, Card, CardHeader, Spinner } from "@/components/ui";
import { LanguageMultiSelect } from "@/components/repurpose/LanguageMultiSelect";
import { RepurposeOutput } from "@/components/repurpose/RepurposeOutput";
import { cls } from "@/lib/format";
import {
  ApiError,
  fetchFormats,
  fetchLanguages,
  repurposeContent,
  type BrandVoice,
  type FormatInfo,
  type Language,
  type RepurposePayload,
  type RepurposeResult,
} from "@/lib/repurpose";

/** Source formats the user can mark their input as (mirrors ContentFormat enum). */
const SOURCE_FORMATS = [
  "blog_post",
  "twitter_thread",
  "linkedin_post",
  "newsletter",
  "video_script",
  "podcast_outline",
  "email_sequence",
  "social_media",
  "medium_article",
  "reddit_post",
  "landing_page",
  "press_release",
  "case_study",
].map((id) => ({ id, label: humanizeId(id) }));

const BRAND_VOICES: Array<{ id: BrandVoice; label: string }> = [
  { id: "professional", label: "Professional" },
  { id: "casual", label: "Casual" },
  { id: "humorous", label: "Humorous" },
  { id: "authoritative", label: "Authoritative" },
  { id: "friendly", label: "Friendly" },
  { id: "technical", label: "Technical" },
];

export default function RepurposePage() {
  // Reference data from the API
  const [formats, setFormats] = useState<FormatInfo[] | null>(null);
  const [formatsError, setFormatsError] = useState<string | null>(null);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [languagesLoading, setLanguagesLoading] = useState(true);
  const [languagesError, setLanguagesError] = useState<string | null>(null);

  // Form state
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [sourceFormat, setSourceFormat] = useState("blog_post");
  const [targetFormats, setTargetFormats] = useState<string[]>(["twitter_thread"]);
  const [brandVoice, setBrandVoice] = useState<BrandVoice>("professional");
  const [customInstructions, setCustomInstructions] = useState("");
  const [targetLanguages, setTargetLanguages] = useState<string[]>([]);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<RepurposeResult | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const loadFormats = useCallback(async () => {
    setFormatsError(null);
    try {
      const list = await fetchFormats();
      setFormats(list);
    } catch (err) {
      setFormatsError(err instanceof Error ? err.message : "Failed to load formats.");
    }
  }, []);

  const loadLanguages = useCallback(async () => {
    setLanguagesLoading(true);
    setLanguagesError(null);
    try {
      setLanguages(await fetchLanguages());
    } catch (err) {
      setLanguagesError(err instanceof Error ? err.message : "Failed to load languages.");
    } finally {
      setLanguagesLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadFormats();
    void loadLanguages();
  }, [loadFormats, loadLanguages]);

  const formatNames = useMemo(() => {
    const map = new Map<string, string>();
    for (const f of formats ?? []) map.set(f.format_id, f.name);
    return map;
  }, [formats]);

  function toggleTargetFormat(id: string) {
    setTargetFormats((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    );
  }

  function toggleLanguage(id: string) {
    setTargetLanguages((prev) =>
      prev.includes(id) ? prev.filter((l) => l !== id) : [...prev, id]
    );
  }

  async function onSubmit() {
    setFormError(null);
    setSubmitError(null);
    if (!body.trim() || body.trim().length < 10) {
      setFormError("Source content must be at least 10 characters.");
      return;
    }
    if (targetFormats.length === 0) {
      setFormError("Pick at least one target format.");
      return;
    }
    if ((formats?.length ?? 0) === 0) {
      setFormError("Target formats are not available — try reloading the page.");
      return;
    }

    const payload: RepurposePayload = {
      content: {
        title: title.trim() || "Untitled content",
        body: body.trim(),
        source_format: sourceFormat,
        tags: [],
      },
      target_formats: targetFormats,
      brand_voice: brandVoice,
      custom_instructions: customInstructions.trim() || undefined,
      // Omit entirely when no languages selected → backend keeps the legacy
      // single-language shape.
      ...(targetLanguages.length > 0 ? { target_languages: targetLanguages } : {}),
    };

    setSubmitting(true);
    try {
      const res = await repurposeContent(payload);
      setResult(res);
    } catch (err) {
      setSubmitError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Repurposing failed."
      );
    } finally {
      setSubmitting(false);
    }
  }

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
              <div className="text-[11px] text-ink-faint">Content studio</div>
            </div>
          </div>

          <nav className="ml-auto flex items-center gap-1" aria-label="Primary">
            <Link
              href="/repurpose"
              aria-current="page"
              className="rounded-[6px] bg-white/[0.04] px-3 py-1.5 text-[13px] font-medium text-ink"
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
          <h1 className="text-[20px] font-medium tracking-[-0.02em] text-ink">Repurpose content</h1>
          <p className="mt-1 text-[13px] text-ink-muted">
            Turn one piece of content into platform-optimized formats — and optionally into
            multiple target languages, generated natively by the LLM.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
          <div className="space-y-4 lg:col-span-3">
            {/* ── Source content ─────────────────────────────────────────── */}
            <Card>
              <CardHeader title="Source content" subtitle="What are you repurposing?" />
              <div className="space-y-3.5 p-5">
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="source-title" className="text-[12px] font-medium text-ink-soft">
                    Title <span className="font-normal text-ink-faint">(optional)</span>
                  </label>
                  <input
                    id="source-title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. AI in Healthcare"
                    className="rounded-[6px] border border-line bg-white/[0.02] px-3.5 py-2.5 text-[13px] text-ink outline-none transition-colors placeholder:text-ink-faint hover:bg-white/[0.04] focus:border-brand/50"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="source-body" className="text-[12px] font-medium text-ink-soft">
                    Content <span className="text-danger">*</span>
                  </label>
                  <textarea
                    id="source-body"
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    rows={8}
                    placeholder="Paste the article, post, or script you want to repurpose…"
                    className="resize-y rounded-[6px] border border-line bg-white/[0.02] px-3.5 py-2.5 text-[13px] leading-relaxed text-ink outline-none transition-colors placeholder:text-ink-faint hover:bg-white/[0.04] focus:border-brand/50"
                  />
                  <p className="text-[11px] text-ink-faint">
                    {body.trim().length} characters · at least 10 required
                  </p>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="source-format" className="text-[12px] font-medium text-ink-soft">
                    Source format
                  </label>
                  <select
                    id="source-format"
                    value={sourceFormat}
                    onChange={(e) => setSourceFormat(e.target.value)}
                    className="rounded-[6px] border border-line bg-panel px-3.5 py-2.5 text-[13px] text-ink-soft outline-none transition-colors hover:bg-white/[0.04] focus:border-brand/50 [&>option]:bg-panel"
                  >
                    {SOURCE_FORMATS.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </Card>

            {/* ── Target formats ─────────────────────────────────────────── */}
            <Card>
              <CardHeader
                title="Target formats"
                subtitle="Where should this content be published?"
                right={
                  targetFormats.length > 0 ? (
                    <span className="text-[12px] font-medium text-ink-soft">
                      {targetFormats.length} selected
                    </span>
                  ) : undefined
                }
              />
              <div className="p-5">
                {formatsError && !formats ? (
                  <div
                    role="alert"
                    className="flex flex-wrap items-center justify-between gap-3 rounded-[6px] border border-danger/30 bg-danger/5 px-3.5 py-3 text-[13px] text-danger"
                  >
                    <span className="flex items-center gap-2">
                      <AlertIcon className="h-4 w-4" /> Couldn&apos;t load target formats.
                    </span>
                    <button
                      type="button"
                      onClick={() => void loadFormats()}
                      className="text-[12px] font-medium underline-offset-2 hover:underline"
                    >
                      Retry
                    </button>
                  </div>
                ) : formats ? (
                  <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
                    {formats.map((f) => {
                      const active = targetFormats.includes(f.format_id);
                      return (
                        <label
                          key={f.format_id}
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
                            onChange={() => toggleTargetFormat(f.format_id)}
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
                            <span className={active ? "text-[13px] font-medium text-ink" : "text-[13px] text-ink-soft"}>
                              {f.name}
                            </span>
                            <span className="text-[11px] leading-relaxed text-ink-faint">
                              {f.description}
                            </span>
                          </span>
                        </label>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-[13px] text-ink-muted">
                    <Spinner className="h-3.5 w-3.5" /> Loading target formats…
                  </div>
                )}
              </div>
            </Card>

            {/* ── Options + languages ────────────────────────────────────── */}
            <Card>
              <CardHeader title="Options" subtitle="Tone, instructions, and target languages." />
              <div className="space-y-4 p-5">
                <div className="flex flex-col gap-1.5 sm:max-w-xs">
                  <label htmlFor="brand-voice" className="text-[12px] font-medium text-ink-soft">
                    Brand voice
                  </label>
                  <select
                    id="brand-voice"
                    value={brandVoice}
                    onChange={(e) => setBrandVoice(e.target.value as BrandVoice)}
                    className="rounded-[6px] border border-line bg-panel px-3.5 py-2.5 text-[13px] text-ink-soft outline-none transition-colors hover:bg-white/[0.04] focus:border-brand/50 [&>option]:bg-panel"
                  >
                    {BRAND_VOICES.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="custom-instructions" className="text-[12px] font-medium text-ink-soft">
                    Custom instructions <span className="font-normal text-ink-faint">(optional)</span>
                  </label>
                  <textarea
                    id="custom-instructions"
                    value={customInstructions}
                    onChange={(e) => setCustomInstructions(e.target.value)}
                    rows={3}
                    placeholder="e.g. Keep it under 280 characters, include a call to action…"
                    className="resize-y rounded-[6px] border border-line bg-white/[0.02] px-3.5 py-2.5 text-[13px] leading-relaxed text-ink outline-none transition-colors placeholder:text-ink-faint hover:bg-white/[0.04] focus:border-brand/50"
                  />
                </div>
                <LanguageMultiSelect
                  languages={languages}
                  selected={targetLanguages}
                  onToggle={toggleLanguage}
                  onClear={() => setTargetLanguages([])}
                  loading={languagesLoading}
                  error={languagesError}
                  onRetry={() => void loadLanguages()}
                  disabled={submitting}
                />
              </div>
            </Card>

            {formError ? (
              <div
                role="alert"
                className="flex items-center gap-2 rounded-[6px] border border-danger/30 bg-danger/5 px-4 py-2.5 text-[13px] text-danger"
              >
                <AlertIcon className="h-4 w-4 shrink-0" />
                {formError}
              </div>
            ) : null}

            <div className="flex items-center gap-3">
              <Button
                variant="primary"
                onClick={() => void onSubmit()}
                disabled={submitting}
                ariaLabel="Generate repurposed content"
              >
                {submitting ? <Spinner className="h-4 w-4" /> : <SparkleIcon className="h-4 w-4" />}
                {submitting ? "Generating…" : "Generate"}
              </Button>
              {targetLanguages.length > 0 ? (
                <span className="text-[12px] text-ink-faint">
                  Output will be generated in {targetLanguages.length} language
                  {targetLanguages.length === 1 ? "" : "s"} per format.
                </span>
              ) : (
                <span className="text-[12px] text-ink-faint">
                  Output stays in the source language.
                </span>
              )}
            </div>

            {submitError ? (
              <div
                role="alert"
                className="flex items-start gap-2 rounded-[6px] border border-danger/30 bg-danger/5 px-4 py-2.5 text-[13px] text-danger"
              >
                <AlertIcon className="mt-0.5 h-4 w-4 shrink-0" />
                <span className="break-words">{submitError}</span>
              </div>
            ) : null}
          </div>

          {/* ── Output ───────────────────────────────────────────────────── */}
          <div className="space-y-4 lg:col-span-2">
            {result ? (
              <div className="animate-fade-in-up space-y-3">
                <div className="flex items-baseline justify-between gap-2">
                  <h2 className="text-[15px] font-medium tracking-[-0.01em] text-ink">Output</h2>
                  <button
                    type="button"
                    onClick={() => setResult(null)}
                    className="text-[12px] font-medium text-ink-faint transition-colors hover:text-ink-soft"
                  >
                    Clear
                  </button>
                </div>
                <RepurposeOutput result={result} languages={languages} />
              </div>
            ) : (
              <div className="flex h-full min-h-64 flex-col items-center justify-center rounded-card border border-dashed border-line px-6 py-10 text-center">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[8px] border border-line bg-white/[0.02] text-ink-faint">
                  <SparkleIcon className="h-5 w-5" />
                </div>
                <p className="max-w-xs text-[13px] leading-relaxed text-ink-muted">
                  Generated formats appear here — with a language tab per target language when you
                  select any.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

/** "twitter_thread" → "Twitter thread". */
function humanizeId(id: string): string {
  return id
    .split("_")
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(" ");
}
