/**
 * Analytics API client — typed access to the real /api/v1/analytics endpoints.
 *
 * The base URL is configurable at build/run time via NEXT_PUBLIC_API_BASE
 * (e.g. http://localhost:8000/api/v1/analytics for local dev against the
 * FastAPI backend). When unset it defaults to the same-origin path, which is
 * how the dashboard is served behind the backend in production.
 */

export const ANALYTICS_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "/api/v1/analytics";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${ANALYTICS_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      ...init,
    });
  } catch (err) {
    throw new ApiError(
      0,
      `Cannot reach the analytics service (${ANALYTICS_BASE}). Is the backend running?`
    );
  }
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* non-JSON error body — keep HTTP status */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

/** POST helpers that return raw (possibly non-JSON) responses, e.g. downloads. */
async function postRaw(path: string, body: unknown): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${ANALYTICS_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Cannot reach the analytics service.");
  }
  return res;
}

// ── Domain types (mirror src/app/models/analytics.py) ───────────────────────

export interface PostMetrics {
  reach: number | null;
  impressions: number | null;
  engagement_rate: number | null;
  completion_rate: number | null;
  share_rate: number | null;
  send_rate: number | null;
  growth_rate: number | null;
  post_date: string | null;
  platform: string;
  post_id: string;
}

export interface AnalyticsSummary {
  total_reach: number;
  avg_engagement_rate: number;
  follower_growth: number;
  period_start: string | null;
  period_end: string | null;
}

export interface DataPoint {
  date: string;
  value: number;
}

export interface TrendData {
  points: DataPoint[];
  period_over_period_delta: number;
  metric: string;
  granularity: string;
}

export interface TopContentItem {
  post_id: string;
  reach?: number;
  impressions?: number;
  engagement_rate?: number;
  [key: string]: number | string | undefined;
}

export interface OptimizationScore {
  overall_score: number;
  signals: Record<string, number>;
  platform: string;
  calculated_at: string | null;
}

export interface ValidationReport {
  quality_delta: number;
  readability: Record<string, number>;
  tone_consistency: Record<string, number>;
  faithfulness: Record<string, number>;
  llm_judge: Record<string, number>;
  diff_blocks: Array<{
    type: "insert" | "delete" | "replace";
    content?: string;
    original?: string;
  }>;
}

export interface ExportResult {
  export_id: string;
  status: string;
  content?: string;
  file_path?: string;
}

// ── Endpoint functions ───────────────────────────────────────────────────────

export function fetchPosts(): Promise<PostMetrics[]> {
  return request<PostMetrics[]>("/posts");
}

export function fetchSummary(fromDate?: string, toDate?: string): Promise<AnalyticsSummary> {
  const params = new URLSearchParams();
  if (fromDate) params.set("from_date", fromDate);
  if (toDate) params.set("to_date", toDate);
  const qs = params.toString();
  return request<AnalyticsSummary>(`/summary${qs ? `?${qs}` : ""}`);
}

export function fetchTrend(
  metric: string,
  granularity = "daily",
  fromDate?: string,
  toDate?: string
): Promise<TrendData> {
  const params = new URLSearchParams({ metric, granularity });
  if (fromDate) params.set("from_date", fromDate);
  if (toDate) params.set("to_date", toDate);
  return request<TrendData>(`/trends/${metric}?${params.toString()}`);
}

export function fetchTopContent(
  metric = "reach",
  limit = 8
): Promise<TopContentItem[]> {
  const params = new URLSearchParams({ metric, limit: String(limit) });
  return request<TopContentItem[]>(`/trends/top-content?${params.toString()}`);
}

export function fetchTrendsSummary(): Promise<{
  total_posts: number;
  total_reach: number;
  avg_engagement_rate: number;
  top_platform: string;
}> {
  return request("/trends/summary");
}

export function calculateOptimizationScore(
  platform: string,
  metrics: Record<string, number>
): Promise<OptimizationScore> {
  return request<OptimizationScore>("/optimization-score/calculate", {
    method: "POST",
    body: JSON.stringify({ platform, metrics }),
  });
}

export function fetchOptimizationScore(postId: string): Promise<OptimizationScore> {
  return request<OptimizationScore>(`/optimization-score/${postId}`);
}

export function runValidation(payload: {
  draft: string;
  published: string;
  source_material?: string;
  run_llm_judge?: boolean;
}): Promise<ValidationReport> {
  return request<ValidationReport>("/validate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface ExportOptions {
  metric_selection: string[];
  date_range?: [string, string] | null;
  platform_filter?: string | null;
}

export function exportCsv(options: ExportOptions): Promise<ExportResult> {
  return request<ExportResult>("/export/csv", {
    method: "POST",
    body: JSON.stringify(options),
  });
}

export function exportPdf(options: ExportOptions): Promise<ExportResult> {
  return request<ExportResult>("/export/pdf", {
    method: "POST",
    body: JSON.stringify(options),
  });
}

export function exportCsvRaw(options: ExportOptions): Promise<Response> {
  return postRaw("/export/csv", options);
}

export function exportPdfRaw(options: ExportOptions): Promise<Response> {
  return postRaw("/export/pdf", options);
}
