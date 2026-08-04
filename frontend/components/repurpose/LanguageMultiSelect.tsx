"use client";

import { AlertIcon, CheckIcon, ChevronDownIcon, CloseIcon } from "@/components/icons";
import { Spinner } from "@/components/ui";
import { cls } from "@/lib/format";
import type { Language } from "@/lib/repurpose";
import { useState } from "react";

/**
 * Target-language multi-select for the repurpose form.
 *
 * Populated from GET /api/v1/languages; each option shows the native name
 * with the English name alongside ("Español · Spanish"). Selected languages
 * render as removable chips. If the languages endpoint fails, an empty state
 * with a retry action is shown instead — repurposing still works in the
 * source language only.
 */
export function LanguageMultiSelect({
  languages,
  selected,
  onToggle,
  onClear,
  loading,
  error,
  onRetry,
  disabled,
}: {
  languages: Language[];
  selected: string[];
  onToggle: (id: string) => void;
  onClear: () => void;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const selectedSet = new Set(selected);
  const byId = new Map(languages.map((l) => [l.id, l]));

  const toggleOpen = () => {
    if (!disabled) setOpen((v) => !v);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-baseline gap-2">
          <span className="text-[13px] font-medium text-ink">Target languages</span>
          <span className="text-[11px] text-ink-faint">
            Optional · translate output into each selected market
          </span>
        </div>
        {selected.length > 0 ? (
          <button
            type="button"
            onClick={onClear}
            className="text-[11px] font-medium text-ink-faint transition-colors hover:text-ink-soft"
          >
            Clear ({selected.length})
          </button>
        ) : null}
      </div>

      {loading ? (
        <div className="flex items-center gap-2 rounded-[6px] border border-line bg-white/[0.02] px-3.5 py-3 text-[13px] text-ink-muted">
          <Spinner className="h-3.5 w-3.5" />
          Loading supported languages…
        </div>
      ) : error ? (
        /* Empty state — languages endpoint failed; single-language flow still works. */
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-[6px] border border-warning/30 bg-warning/5 px-3.5 py-3"
        >
          <div className="flex items-center gap-2 text-[13px] text-warning">
            <AlertIcon className="h-4 w-4 shrink-0" />
            <span>
              Couldn&apos;t load supported languages — output will be generated in the
              source language only.
            </span>
          </div>
          <button
            type="button"
            onClick={onRetry}
            className="text-[12px] font-medium text-ink-soft underline-offset-2 transition-colors hover:text-ink hover:underline"
          >
            Retry
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {selected.length > 0 ? (
            <div className="flex flex-wrap items-center gap-1.5">
              {selected.map((id) => {
                const lang = byId.get(id);
                return (
                  <span
                    key={id}
                    className="inline-flex items-center gap-1.5 rounded-full border border-brand/50 bg-brand/10 px-2.5 py-1 text-[12px] font-medium text-brand-bright"
                  >
                    {lang ? lang.native_name : id}
                    <button
                      type="button"
                      onClick={() => onToggle(id)}
                      aria-label={`Remove ${lang?.name ?? id}`}
                      className="text-brand-bright/70 transition-colors hover:text-brand-hover"
                    >
                      <CloseIcon className="h-3 w-3" />
                    </button>
                  </span>
                );
              })}
            </div>
          ) : (
            <p className="text-[12px] text-ink-faint">
              No languages selected — keep the current single-language output.
            </p>
          )}

          <div className="relative">
            <button
              type="button"
              onClick={toggleOpen}
              aria-expanded={open}
              disabled={disabled}
              className={cls(
                "flex w-full items-center justify-between gap-2 rounded-[6px] border border-line bg-white/[0.02] px-3.5 py-2.5",
                "text-[13px] text-ink-soft transition-colors hover:bg-white/[0.04]",
                "disabled:cursor-not-allowed disabled:opacity-50"
              )}
            >
              <span>{open ? "Hide languages" : "Choose languages"}</span>
              <ChevronDownIcon
                className={cls("h-3.5 w-3.5 text-ink-faint transition-transform", open && "rotate-180")}
              />
            </button>

            {open ? (
              <div className="absolute z-10 mt-1.5 max-h-56 w-full overflow-y-auto rounded-[6px] border border-line bg-panel p-1 shadow-dialog">
                {languages.map((lang) => {
                  const active = selectedSet.has(lang.id);
                  return (
                    <label
                      key={lang.id}
                      className={cls(
                        "flex cursor-pointer items-center gap-2.5 rounded-[4px] px-2.5 py-2 transition-colors",
                        "hover:bg-white/[0.04]"
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={active}
                        onChange={() => onToggle(lang.id)}
                        className="sr-only"
                      />
                      <span
                        aria-hidden
                        className={cls(
                          "flex h-4 w-4 items-center justify-center rounded-[4px] border transition-colors",
                          active
                            ? "border-brand bg-brand text-white"
                            : "border-line bg-white/[0.02] text-transparent"
                        )}
                      >
                        <CheckIcon className="h-3 w-3" />
                      </span>
                      <span className="flex items-baseline gap-2 text-[13px]">
                        <span className={active ? "text-ink" : "text-ink-soft"}>{lang.native_name}</span>
                        <span className="text-[11px] text-ink-faint">{lang.name}</span>
                      </span>
                    </label>
                  );
                })}
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
