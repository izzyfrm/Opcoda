/** Password hashing (PBKDF2-SHA256) and cookie sessions. */
import { HttpError, nowSeconds } from "./http";

// 100,000 is the maximum PBKDF2 iteration count supported by the Workers runtime.
const PBKDF2_ITERATIONS = 100_000;
const SESSION_DAYS = 30;
const SESSION_SECONDS = SESSION_DAYS * 24 * 60 * 60;
const encoder = new TextEncoder();

export interface UserRow {
  id: string;
  username: string;
  display_name: string;
  password_hash: string;
  password_salt: string;
  password_iterations: number;
  avatar_version: number | null;
  settings: string;
  created_at: number;
}

export interface Session {
  id: string;
  user: UserRow;
}

function toBase64(bytes: ArrayBuffer | Uint8Array): string {
  const view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let binary = "";
  for (const b of view) binary += String.fromCharCode(b);
  return btoa(binary);
}

function fromBase64(text: string): Uint8Array {
  return Uint8Array.from(atob(text), (c) => c.charCodeAt(0));
}

function toBase64Url(bytes: Uint8Array): string {
  return toBase64(bytes).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(text));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function pbkdf2(password: string, salt: Uint8Array, iterations: number): Promise<ArrayBuffer> {
  const key = await crypto.subtle.importKey("raw", encoder.encode(password), "PBKDF2", false, ["deriveBits"]);
  return crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations }, key, 256);
}

export async function hashPassword(password: string) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await pbkdf2(password, salt, PBKDF2_ITERATIONS);
  return { hash: toBase64(hash), salt: toBase64(salt), iterations: PBKDF2_ITERATIONS };
}

export async function verifyPassword(
  password: string,
  stored: Pick<UserRow, "password_hash" | "password_salt" | "password_iterations">,
): Promise<boolean> {
  const actual = new Uint8Array(await pbkdf2(password, fromBase64(stored.password_salt), stored.password_iterations));
  const expected = fromBase64(stored.password_hash);
  if (actual.byteLength !== expected.byteLength) return false;
  return crypto.subtle.timingSafeEqual(actual, expected);
}

/** Spend the same work as a real check so unknown usernames aren't distinguishable by timing. */
export async function burnPasswordCheck(password: string): Promise<void> {
  await pbkdf2(password, new Uint8Array(16), PBKDF2_ITERATIONS);
}

export function validateUsername(raw: unknown): string {
  const username = String(raw ?? "").trim().toLowerCase();
  if (!/^[a-z][a-z0-9_]{2,19}$/.test(username)) {
    throw new HttpError(400, "invalid_username",
      "Usernames are 3–20 characters: letters, numbers and underscores, starting with a letter.");
  }
  if (["admin", "root", "opcoda", "coda", "support", "system", "api", "null", "undefined"].includes(username)) {
    throw new HttpError(400, "invalid_username", "That username is reserved.");
  }
  return username;
}

export function validatePassword(raw: unknown, username?: string): string {
  const password = String(raw ?? "");
  if (password.length < 8) throw new HttpError(400, "weak_password", "Use at least 8 characters.");
  if (password.length > 128) throw new HttpError(400, "weak_password", "Use 128 characters or fewer.");
  if (username && password.toLowerCase().includes(username)) {
    throw new HttpError(400, "weak_password", "Your password can't contain your username.");
  }
  return password;
}

export function validateDisplayName(raw: unknown, fallback: string): string {
  const name = String(raw ?? "").replace(/\s+/g, " ").trim();
  if (!name) return fallback;
  if (name.length > 40) throw new HttpError(400, "invalid_name", "Display names are 40 characters or fewer.");
  return name;
}

// ---- sessions -------------------------------------------------------------

function cookieName(secure: boolean): string {
  // __Host- cookies must be Secure, host-only and Path=/. Local `wrangler dev` runs on plain http.
  return secure ? "__Host-opcoda_session" : "opcoda_session";
}

function readCookie(request: Request, name: string): string | null {
  const header = request.headers.get("cookie");
  if (!header) return null;
  for (const part of header.split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) return rest.join("=");
  }
  return null;
}

export function sessionCookie(token: string, secure: boolean): string {
  return [
    `${cookieName(secure)}=${token}`,
    "Path=/",
    "HttpOnly",
    "SameSite=Lax",
    `Max-Age=${SESSION_SECONDS}`,
    ...(secure ? ["Secure"] : []),
  ].join("; ");
}

export function clearSessionCookie(secure: boolean): string {
  return [`${cookieName(secure)}=`, "Path=/", "HttpOnly", "SameSite=Lax", "Max-Age=0", ...(secure ? ["Secure"] : [])].join("; ");
}

export async function createSession(db: D1Database, userId: string, userAgent: string | null): Promise<string> {
  const token = toBase64Url(crypto.getRandomValues(new Uint8Array(32)));
  const now = nowSeconds();
  await db
    .prepare("INSERT INTO sessions (id, user_id, created_at, last_seen_at, expires_at, user_agent) VALUES (?, ?, ?, ?, ?, ?)")
    .bind(await sha256Hex(token), userId, now, now, now + SESSION_SECONDS, (userAgent ?? "").slice(0, 200))
    .run();
  return token;
}

export async function getSession(request: Request, db: D1Database, secure: boolean, ctx: ExecutionContext): Promise<Session | null> {
  const token = readCookie(request, cookieName(secure));
  if (!token || token.length > 100) return null;
  const id = await sha256Hex(token);
  const now = nowSeconds();
  const row = await db
    .prepare(
      `SELECT s.last_seen_at AS session_last_seen, u.* FROM sessions s JOIN users u ON u.id = s.user_id
       WHERE s.id = ? AND s.expires_at > ?`,
    )
    .bind(id, now)
    .first<UserRow & { session_last_seen: number }>();
  if (!row) return null;
  // Sliding expiry, at most one write per hour per session.
  if (now - row.session_last_seen > 3600) {
    ctx.waitUntil(
      db.prepare("UPDATE sessions SET last_seen_at = ?, expires_at = ? WHERE id = ?").bind(now, now + SESSION_SECONDS, id).run(),
    );
  }
  const { session_last_seen: _ignored, ...user } = row;
  return { id, user };
}

export async function requireSession(request: Request, db: D1Database, secure: boolean, ctx: ExecutionContext): Promise<Session> {
  const session = await getSession(request, db, secure, ctx);
  if (!session) throw new HttpError(401, "unauthenticated", "Please sign in.");
  return session;
}
