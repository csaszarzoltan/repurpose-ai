/**
 * Repurpose API client — typed access to the /api/v1 repurpose endpoints
 * (formats, languages, repurpose).
 *
 * Mirrors the analytics client pattern in ./api.ts: the base URL is
 * configurable at build/run time via NEXT_PUBLIC_REPURPOSE_BASE (e.g.
 * http://localhost:8000/api/v1 for local dev against the FastAPI backend).
 * When unset it defaults to the same-origin path, which is how the UI is
 * served behind the backend in production.
 *
 * API contract (multi-language repurposing, v1.7.0):
 * - GET  /api/v1/languages  → [{id, name, native_name}] (ISO 639-1 ids)
 * - GET  /api/v1/formats    → [{format_id, name, description, ...}]
 * - POST /api/v1/repurpose  → RepurposeResult
 *   When `target_languages` is non-empty the `repurposed` map is
 *   `{format: {lang_code: content}}`; when empty it stays `{format: content}`
 *   (legacy single-language shape).
 */

export const REPURPOSE_BASE =
  process.env.NEXT_PUBLIC_REPURPOSE_BASE ?? "/api/v1";

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
    res = await fetch(`${REPURPOSE_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      ...init,
    });
  } catch {
    throw new ApiError(
      0,
      `Cannot reach the repurpose service (${REPURPOSE_BASE}). Is the backend running?`
    );
  }
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (Array.isArray(body?.detail) && body.detail.length > 0) {
        // Pydantic 422 detail: [{loc, msg, type}, ...]
        detail = body.detail
          .map((d: { msg?: string; loc?: unknown[] }) => {
            const loc = Array.isArray(d.loc) ? d.loc.join(".") : "";
            return loc ? `${loc}: ${d.msg ?? "invalid"}` : (d.msg ?? "invalid");
          })
          .join("; ");
      }
    } catch {
      /* non-JSON error body — keep HTTP status */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

// ── Domain types (mirror src/app/models/content.py + languages registry) ──

export interface Language {
  /** ISO 639-1 code, e.g. "es" */
  id: string;
  /** English name, e.g. "Spanish" */
  name: string;
  /** Native name, e.g. "Español" */
  native_name: string;
}

export interface FormatInfo {
  format_id: string;
  name: string;
  description: string;
  max_length: number;
  supports_images: boolean;
  supports_links: boolean;
  tone_guidance?: string;
  structure_hints?: string;
  target_audience?: string;
}

export type BrandVoice =
  | "professional"
  | "casual"
  | "humorous"
  | "authoritative"
  | "friendly"
  | "technical";

export interface RepurposePayload {
  content: {
    title: string;
    body: string;
    source_format: string;
    tags?: string[];
  };
  target_formats: string[];
  brand_voice?: BrandVoice;
  custom_instructions?: string;
  llm_strategy?: string;
  /** ISO 639-1 codes; omitted entirely when no languages are selected. */
  target_languages?: string[];
  /** Optional publish destinations (platform names); only connected platforms. */
  destinations?: string[];
}

/** Legacy single-language shape: {format: content}. */
export type SingleLanguageOutput = Record<string, string>;

/** Multi-language shape: {format: {lang_code: content}}. */
export type MultiLanguageOutput = Record<string, Record<string, string>>;

/** Either output shape — discriminate with isMultiLanguageOutput(). */
export type RepurposedOutput = Record<
  string,
  string | Record<string, string>
>;

export interface RepurposeResult {
  original_id: string;
  repurposed: RepurposedOutput;
  warnings: string[];
  created_at: string;
}

/** True when the response used the per-language shape (target_languages set). */
export function isMultiLanguageOutput(
  repurposed: RepurposedOutput
): repurposed is MultiLanguageOutput {
  const first = Object.values(repurposed)[0];
  return typeof first === "object" && first !== null;
}

// ── Endpoint functions ──────────────────────────────────────────────────────

export function fetchLanguages(): Promise<Language[]> {
  return request<Language[]>("/languages");
}

export function fetchFormats(): Promise<FormatInfo[]> {
  return request<FormatInfo[]>("/formats");
}

export function repurposeContent(payload: RepurposePayload): Promise<RepurposeResult> {
  return request<RepurposeResult>("/repurpose", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
