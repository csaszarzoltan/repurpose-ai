/** Formatting helpers shared across dashboard components. */

const nf = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });
const nfFull = new Intl.NumberFormat("en-US");

/** 12.4K, 1.2M … */
export function compact(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return nf.format(value);
}

/** 12,483 */
export function full(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return nfFull.format(value);
}

/** 3.35% — input is a ratio (0.0335), rendered as a percentage */
export function pct(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

/** +12.4% / −3.1% with explicit sign */
export function signedPct(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${Math.abs(value).toFixed(digits)}%`;
}

/** 2026-07-03T10:00:00+00:00 → "Jul 3, 2026" */
export function shortDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value.slice(0, 10);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

/** 2026-07-03 → "Jul 3" */
export function shortDay(isoDate: string): string {
  const d = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function platformLabel(platform: string): string {
  const map: Record<string, string> = {
    twitter: "X / Twitter",
    x: "X / Twitter",
    linkedin: "LinkedIn",
    medium: "Medium",
    instagram: "Instagram",
    facebook: "Facebook",
    youtube: "YouTube",
    tiktok: "TikTok",
  };
  return map[platform.toLowerCase()] ?? platform;
}

export function platformColor(platform: string): string {
  const map: Record<string, string> = {
    twitter: "#8a8f98",
    x: "#8a8f98",
    linkedin: "#0a66c2",
    medium: "#d0d6e0",
    instagram: "#e1306c",
    facebook: "#1877f2",
    youtube: "#ff0033",
    tiktok: "#69c9d0",
  };
  return map[platform.toLowerCase()] ?? "#7170ff";
}

export function scoreTone(score: number): { label: string; color: string } {
  if (score >= 75) return { label: "Strong", color: "#27a644" };
  if (score >= 50) return { label: "Room to grow", color: "#f5a524" };
  return { label: "Needs work", color: "#f2646a" };
}

export function cls(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}
