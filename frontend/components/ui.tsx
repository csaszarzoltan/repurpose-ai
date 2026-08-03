import type { ReactNode } from "react";
import { cls } from "@/lib/format";

/** Shared dashboard primitives: Card, Badge, Button, Spinner, Delta, bars. */

export function Card({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cls(
        "rounded-card border border-line bg-surface/60 shadow-card",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  subtitle,
  right,
}: {
  title: string;
  subtitle?: string;
  right?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-line-subtle px-5 py-4">
      <div>
        <h2 className="text-[15px] font-medium tracking-[-0.01em] text-ink">
          {title}
        </h2>
        {subtitle ? (
          <p className="mt-0.5 text-[13px] leading-relaxed text-ink-muted">
            {subtitle}
          </p>
        ) : null}
      </div>
      {right ? <div className="shrink-0">{right}</div> : null}
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger" | "brand";
  className?: string;
}) {
  const tones: Record<string, string> = {
    neutral: "border-line text-ink-soft",
    success: "border-success/40 text-success",
    warning: "border-warning/40 text-warning",
    danger: "border-danger/40 text-danger",
    brand: "border-brand/50 text-brand-bright",
  };
  return (
    <span
      className={cls(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium",
        tones[tone],
        className
      )}
    >
      {children}
    </span>
  );
}

export function Button({
  children,
  onClick,
  variant = "ghost",
  disabled,
  type = "button",
  className,
  ariaLabel,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "ghost" | "subtle";
  disabled?: boolean;
  type?: "button" | "submit";
  className?: string;
  ariaLabel?: string;
}) {
  const variants: Record<string, string> = {
    primary:
      "bg-brand text-white hover:bg-brand-hover border border-transparent",
    ghost:
      "bg-white/[0.02] text-ink-soft hover:text-ink border border-line",
    subtle: "bg-white/[0.04] text-ink-soft hover:text-ink",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      className={cls(
        "inline-flex items-center gap-1.5 rounded-[6px] px-3.5 py-2 text-[13px] font-medium transition-colors",
        "disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
    >
      {children}
    </button>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cls(
        "inline-block h-4 w-4 animate-spin rounded-full border-2 border-line border-t-brand-bright",
        className
      )}
    />
  );
}

export function Delta({
  value,
  suffix = "%",
  className,
}: {
  value: number | null | undefined;
  suffix?: string;
  className?: string;
}) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return <span className={cls("text-[12px] text-ink-faint", className)}>—</span>;
  }
  const up = value >= 0;
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return (
    <span
      className={cls(
        "inline-flex items-center gap-1 text-[12px] font-medium",
        value === 0 ? "text-ink-faint" : up ? "text-success" : "text-danger",
        className
      )}
      aria-label={`${up ? "up" : "down"} ${Math.abs(value).toFixed(1)} percent`}
    >
      {up ? "▲" : "▼"}
      {sign}
      {Math.abs(value).toFixed(1)}
      {suffix}
    </span>
  );
}

export function ProgressBar({
  value,
  max = 100,
  color = "#7170ff",
  className,
}: {
  value: number;
  max?: number;
  color?: string;
  className?: string;
}) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(pct)}
      aria-valuemin={0}
      aria-valuemax={100}
      className={cls("h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]", className)}
    >
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  );
}

export function Stat({
  label,
  value,
  sub,
  icon,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5 text-[12px] font-medium uppercase tracking-wide text-ink-faint">
        {icon}
        {label}
      </div>
      <div className="text-[26px] font-medium leading-none tracking-[-0.02em] text-ink">
        {value}
      </div>
      {sub ? <div className="text-[12px] text-ink-faint">{sub}</div> : null}
    </div>
  );
}
