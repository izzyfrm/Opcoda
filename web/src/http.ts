/** Small HTTP helpers shared by the API handlers. */

export class HttpError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly extra: Record<string, unknown> = {},
  ) {
    super(message);
  }
}

export function json(data: unknown, init: ResponseInit = {}): Response {
  const headers = new Headers(init.headers);
  headers.set("content-type", "application/json; charset=utf-8");
  if (!headers.has("cache-control")) headers.set("cache-control", "no-store");
  return new Response(JSON.stringify(data), { ...init, headers });
}

export function errorResponse(err: HttpError): Response {
  return json({ error: { code: err.code, message: err.message, ...err.extra } }, { status: err.status });
}

export async function readJson<T>(request: Request, maxBytes = 16_384): Promise<T> {
  if (!(request.headers.get("content-type") ?? "").includes("application/json")) {
    throw new HttpError(415, "bad_content_type", "Expected a JSON body.");
  }
  if (Number(request.headers.get("content-length") ?? 0) > maxBytes) {
    throw new HttpError(413, "too_large", "Request body is too large.");
  }
  const text = await request.text();
  if (text.length > maxBytes) throw new HttpError(413, "too_large", "Request body is too large.");
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new HttpError(400, "bad_json", "Request body is not valid JSON.");
  }
}

/** Reject cross-site state-changing requests (defence in depth on top of SameSite cookies). */
export function assertSameOrigin(request: Request, url: URL): void {
  if (request.method === "GET" || request.method === "HEAD") return;
  const origin = request.headers.get("origin");
  if (!origin) throw new HttpError(403, "bad_origin", "Missing Origin header.");
  let host: string;
  try {
    host = new URL(origin).host;
  } catch {
    throw new HttpError(403, "bad_origin", "Invalid Origin header.");
  }
  if (host !== url.host) throw new HttpError(403, "bad_origin", "Cross-site request blocked.");
}

export const nowSeconds = (): number => Math.floor(Date.now() / 1000);

export function utcDay(date = new Date()): string {
  return date.toISOString().slice(0, 10);
}

export function nextUtcMidnight(date = new Date()): number {
  const next = Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() + 1);
  return Math.floor(next / 1000);
}

export function clientIp(request: Request): string {
  return request.headers.get("cf-connecting-ip") ?? "local";
}

/** Fixed-window counter in D1. Returns false when the caller is over the limit. */
export async function rateLimit(db: D1Database, key: string, limit: number, windowSeconds: number): Promise<boolean> {
  const now = nowSeconds();
  const row = await db
    .prepare(
      `INSERT INTO rate_limits (key, count, window_start) VALUES (?1, 1, ?2)
       ON CONFLICT(key) DO UPDATE SET
         count = CASE WHEN window_start <= ?3 THEN 1 ELSE count + 1 END,
         window_start = CASE WHEN window_start <= ?3 THEN ?2 ELSE window_start END
       RETURNING count`,
    )
    .bind(key, now, now - windowSeconds)
    .first<{ count: number }>();
  return (row?.count ?? 0) <= limit;
}

export function tooManyRequests(message: string): HttpError {
  return new HttpError(429, "rate_limited", message);
}
