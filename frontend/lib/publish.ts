/**
 * Publish API client — typed access to the /publish endpoints
 * for platform connections, OAuth flows, and credential management.
 *
 * Mirrors the analytics/repurpose client pattern: the base URL is
 * configurable via NEXT_PUBLIC_API_BASE (e.g. http://localhost:8000
 * for local dev). When unset it defaults to the same-origin path.
 */

export const PUBLISH_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "";

export class PublishApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "PublishApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${PUBLISH_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      ...init,
    });
  } catch {
    throw new PublishApiError(
      0,
      `Cannot reach the publish service. Is the backend running?`
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
    throw new PublishApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

// ── Domain types ───────────────────────────────────────────────────────────

export interface PlatformInfo {
  name: string;
  display_name: string;
  post_type: string;
}

export interface PlatformCredentials {
  platform: string;
  access_token: string;
  refresh_token?: string;
  token_expiry?: string;
  platform_user_id?: string;
  is_active: boolean;
}

export interface AuthUrlResponse {
  url: string;
  auth_url: string;
  platform: string;
}

export interface CallbackResponse {
  status: string;
  platform: string;
  access_token?: string;
}

// ── Endpoint functions ──────────────────────────────────────────────────────

/**
 * Fetch all supported publishing platforms with capabilities.
 */
export function fetchPlatforms(): Promise<PlatformInfo[]> {
  return request<PlatformInfo[]>("/api/v1/publish/platforms");
}

/**
 * Get OAuth2 authorization URL for a platform.
 * The redirect_uri should point to the frontend callback page.
 */
export function getAuthUrl(
  platform: string,
  redirectUri: string
): Promise<AuthUrlResponse> {
  const params = new URLSearchParams({ redirect_uri: redirectUri });
  return request<AuthUrlResponse>(
    `/publish/${platform}/auth-url?${params.toString()}`
  );
}

/**
 * Exchange authorization code for platform credentials.
 */
export function exchangeCode(
  platform: string,
  code: string,
  state?: string,
  redirectUri?: string
): Promise<CallbackResponse> {
  const params = new URLSearchParams({ code });
  if (state) params.set("state", state);
  if (redirectUri) params.set("redirect_uri", redirectUri);
  return request<CallbackResponse>(
    `/publish/${platform}/callback?${params.toString()}`,
    { method: "POST" }
  );
}

/**
 * Get stored credentials for a platform.
 */
export function getCredentials(
  platform: string
): Promise<PlatformCredentials[]> {
  return request<PlatformCredentials[]>(
    `/publish/${platform}/credentials`
  );
}

/**
 * Store or update platform credentials.
 */
export function storeCredentials(
  platform: string,
  credentials: PlatformCredentials
): Promise<{ status: string; platform: string }> {
  return request(`/publish/${platform}/credentials`, {
    method: "PUT",
    body: JSON.stringify(credentials),
  });
}

/**
 * Revoke and remove stored credentials for a platform.
 */
export function revokeCredentials(
  platform: string
): Promise<{ status: string; platform: string }> {
  return request(`/publish/${platform}/credentials`, {
    method: "DELETE",
  });
}

/**
 * Check if a platform has active credentials (is connected).
 */
export async function isPlatformConnected(
  platform: string
): Promise<boolean> {
  try {
    const creds = await getCredentials(platform);
    return Array.isArray(creds) && creds.some((c) => c.is_active);
  } catch {
    return false;
  }
}
