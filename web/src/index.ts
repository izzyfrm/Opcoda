/**
 * opcoda.cc Worker.
 *
 * Static files in public/ are served by Workers Static Assets. This Worker only
 * handles /api/*: accounts, sessions, settings, avatars, conversations, and
 * chat, which it forwards to Coda: server.py on the owner's PC, reached
 * privately through a Cloudflare Tunnel via the Workers VPC binding
 * CODA_MODEL (or MODEL_URL in local dev), authenticated with MODEL_TOKEN.
 */
import {
  burnPasswordCheck,
  clearSessionCookie,
  createSession,
  hashPassword,
  requireSession,
  sessionCookie,
  validateDisplayName,
  validatePassword,
  validateUsername,
  verifyPassword,
  type Session,
  type UserRow,
} from "./auth";
import { projectFiles, projectPreview, extractWebsiteProject, type ProjectFile } from "./project";
import {
  assertSameOrigin,
  clientIp,
  errorResponse,
  HttpError,
  json,
  nextUtcMidnight,
  nowSeconds,
  rateLimit,
  readJson,
  tooManyRequests,
  utcDay,
} from "./http";

interface Settings {
  v: number;
  theme: "system" | "light" | "dark";
  temperature: number;
  maxTokens: number;
  drafts: number;
  usageMode: "light" | "medium" | "super" | "intense";
}

const SETTINGS_VERSION = 5;
const MODE_TOKENS = { light: 256, medium: 450, super: 650, intense: 900 } as const;
const DEFAULT_SETTINGS: Settings = { v: SETTINGS_VERSION, theme: "dark", temperature: 0.3, maxTokens: 450, drafts: 1, usageMode: "medium" };
const LANGUAGES = ["auto", "html", "css", "javascript", "python"] as const;
type Language = (typeof LANGUAGES)[number];
const MAX_MESSAGE_CHARS = 6000;
const MAX_AVATAR_BYTES = 300 * 1024;

interface Ctx {
  request: Request;
  env: Env;
  ctx: ExecutionContext;
  url: URL;
  secure: boolean;
  params: string[];
}

type Handler = (c: Ctx) => Promise<Response>;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function parseSettings(raw: string): Settings {
  try {
    const saved = JSON.parse(raw) as Partial<Settings>;
    if (saved.v !== SETTINGS_VERSION) {
      const oldLength = Number(saved.maxTokens ?? DEFAULT_SETTINGS.maxTokens);
      const usageMode = oldLength <= 320 ? "light" : oldLength <= 550 ? "medium" : oldLength <= 750 ? "super" : "intense";
      return { ...DEFAULT_SETTINGS, theme: saved.theme ?? DEFAULT_SETTINGS.theme,
        temperature: saved.temperature ?? DEFAULT_SETTINGS.temperature,
        usageMode, maxTokens: MODE_TOKENS[usageMode] };
    }
    return { ...DEFAULT_SETTINGS, ...saved };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

function dailyLimit(env: Env): number {
  const n = Number.parseInt(env.DAILY_MESSAGE_LIMIT ?? "25", 10);
  return Number.isFinite(n) && n > 0 ? n : 25;
}

async function usageFor(env: Env, userId: string) {
  const row = await env.DB.prepare("SELECT count FROM usage WHERE user_id = ? AND day = ?")
    .bind(userId, utcDay())
    .first<{ count: number }>();
  return { used: row?.count ?? 0, limit: dailyLimit(env), resetsAt: nextUtcMidnight() };
}

async function publicUser(env: Env, user: UserRow) {
  return {
    id: user.id,
    username: user.username,
    displayName: user.display_name,
    avatarVersion: user.avatar_version,
    settings: parseSettings(user.settings),
    createdAt: user.created_at,
    usage: await usageFor(env, user.id),
  };
}

function session(c: Ctx): Promise<Session> {
  return requireSession(c.request, c.env.DB, c.secure, c.ctx);
}

/** Reach server.py: directly via MODEL_URL in local dev, otherwise privately through Workers VPC. */
function modelFetch(env: Env, path: string, init?: RequestInit): Promise<Response> {
  if (env.MODEL_URL) return fetch(`${env.MODEL_URL}${path}`, init);
  return env.CODA_MODEL.fetch(`http://127.0.0.1:8000${path}`, init);
}

function withCookie(response: Response, cookie: string): Response {
  const res = new Response(response.body, response);
  res.headers.append("set-cookie", cookie);
  return res;
}

function sniffImage(bytes: Uint8Array): string | null {
  const b = bytes;
  if (b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47) return "image/png";
  if (b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return "image/jpeg";
  if (b[0] === 0x52 && b[1] === 0x49 && b[2] === 0x46 && b[3] === 0x46 &&
      b[8] === 0x57 && b[9] === 0x45 && b[10] === 0x42 && b[11] === 0x50) return "image/webp";
  return null;
}

function titleFrom(message: string): string {
  const line = message.replace(/\s+/g, " ").trim();
  return line.length > 48 ? `${line.slice(0, 47)}…` : line;
}

async function constantTimeEqual(a: string, b: string): Promise<boolean> {
  const enc = new TextEncoder();
  const [ha, hb] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(a)),
    crypto.subtle.digest("SHA-256", enc.encode(b)),
  ]);
  return crypto.subtle.timingSafeEqual(ha, hb);
}

// ---------------------------------------------------------------------------
// Public
// ---------------------------------------------------------------------------

const getConfig: Handler = async ({ env }) =>
  json({ inviteRequired: Boolean(env.INVITE_CODE), dailyLimit: dailyLimit(env), maxMessageChars: MAX_MESSAGE_CHARS, languages: LANGUAGES });

const getStatus: Handler = async ({ env, ctx }) => {
  const cache = caches.default;
  const key = new Request("https://opcoda.internal/model-status");
  const hit = await cache.match(key);
  if (hit) return json(await hit.json());

  let status: Record<string, unknown> = { online: false };
  try {
    const res = await modelFetch(env, "/health", { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      const data = (await res.json()) as { step?: number; parameters?: number; model?: string; backend?: string; context_tokens?: number };
      status = { online: true, step: data.step ?? null, parameters: data.parameters ?? null,
        model: data.model ?? null, backend: data.backend ?? null, contextTokens: data.context_tokens ?? null };
    }
  } catch {
    // offline: PC asleep, server.py stopped, or tunnel down
  }
  ctx.waitUntil(cache.put(key, json(status, { headers: { "cache-control": "max-age=20" } })));
  return json(status);
};

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

const signup: Handler = async (c) => {
  const { request, env } = c;
  const body = await readJson<{ username?: string; password?: string; displayName?: string; inviteCode?: string }>(request);
  if (env.INVITE_CODE && !(await constantTimeEqual(String(body.inviteCode ?? ""), env.INVITE_CODE))) {
    throw new HttpError(403, "invalid_invite", "That invite code isn't valid.");
  }
  const username = validateUsername(body.username);
  const password = validatePassword(body.password, username);
  const displayName = validateDisplayName(body.displayName, username);

  const taken = await env.DB.prepare("SELECT 1 FROM users WHERE username = ?").bind(username).first();
  if (taken) throw new HttpError(409, "username_taken", "That username is taken.");

  // Limit actual account creation (the expensive part), not typos.
  if (!(await rateLimit(env.DB, `signup:${clientIp(request)}`, 10, 3600))) {
    throw tooManyRequests("Too many new accounts from this network. Try again in an hour.");
  }

  const { hash, salt, iterations } = await hashPassword(password);
  const id = crypto.randomUUID();
  const now = nowSeconds();
  try {
    await env.DB.prepare(
      `INSERT INTO users (id, username, display_name, password_hash, password_salt, password_iterations, settings, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    )
      .bind(id, username, displayName, hash, salt, iterations, JSON.stringify(DEFAULT_SETTINGS), now, now)
      .run();
  } catch (err) {
    if (String(err).includes("UNIQUE")) throw new HttpError(409, "username_taken", "That username is taken.");
    throw err;
  }
  console.log(JSON.stringify({ message: "signup", userId: id }));

  const token = await createSession(env.DB, id, request.headers.get("user-agent"));
  const user = await env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(id).first<UserRow>();
  return withCookie(json({ user: await publicUser(env, user!) }, { status: 201 }), sessionCookie(token, c.secure));
};

const login: Handler = async (c) => {
  const { request, env } = c;
  const body = await readJson<{ username?: string; password?: string }>(request);
  const username = String(body.username ?? "").trim().toLowerCase().slice(0, 40);
  const password = String(body.password ?? "").slice(0, 128);

  const ipOk = await rateLimit(env.DB, `login-ip:${clientIp(request)}`, 20, 900);
  const userOk = await rateLimit(env.DB, `login-user:${username}`, 8, 900);
  if (!ipOk || !userOk) throw tooManyRequests("Too many sign-in attempts. Wait 15 minutes and try again.");

  const user = username
    ? await env.DB.prepare("SELECT * FROM users WHERE username = ?").bind(username).first<UserRow>()
    : null;
  const ok = user ? await verifyPassword(password, user) : (await burnPasswordCheck(password), false);
  if (!user || !ok) throw new HttpError(401, "invalid_credentials", "Username or password is incorrect.");

  const token = await createSession(env.DB, user.id, request.headers.get("user-agent"));
  return withCookie(json({ user: await publicUser(env, user) }), sessionCookie(token, c.secure));
};

const logout: Handler = async (c) => {
  try {
    const s = await session(c);
    await c.env.DB.prepare("DELETE FROM sessions WHERE id = ?").bind(s.id).run();
  } catch (err) {
    if (!(err instanceof HttpError)) throw err;
  }
  return withCookie(json({ ok: true }), clearSessionCookie(c.secure));
};

// ---------------------------------------------------------------------------
// Account
// ---------------------------------------------------------------------------

const getMe: Handler = async (c) => {
  const s = await session(c);
  return json({ user: await publicUser(c.env, s.user) });
};

const updateMe: Handler = async (c) => {
  const s = await session(c);
  const body = await readJson<{ displayName?: string; settings?: Partial<Settings> }>(c.request);
  const current = parseSettings(s.user.settings);
  const next: Settings = { ...current };
  if (body.settings) {
    const { theme, temperature, maxTokens, drafts, usageMode } = body.settings;
    if (theme !== undefined) {
      if (!["system", "light", "dark"].includes(theme)) throw new HttpError(400, "invalid_setting", "Unknown theme.");
      next.theme = theme;
    }
    if (temperature !== undefined) {
      const t = Number(temperature);
      if (!(t >= 0.1 && t <= 1)) throw new HttpError(400, "invalid_setting", "Creativity must be between 0.1 and 1.");
      next.temperature = Math.round(t * 100) / 100;
    }
    if (maxTokens !== undefined) {
      const m = Math.round(Number(maxTokens));
      if (!(m >= 128 && m <= 1000)) throw new HttpError(400, "invalid_setting", "Response length must be 128–1000.");
      next.maxTokens = m;
    }
    if (drafts !== undefined) {
      const d = Math.round(Number(drafts));
      if (!(d >= 1 && d <= 6)) throw new HttpError(400, "invalid_setting", "Drafts must be between 1 and 6.");
      next.drafts = d;
    }
    if (usageMode !== undefined) {
      if (typeof usageMode !== "string" || !Object.hasOwn(MODE_TOKENS, usageMode)) throw new HttpError(400, "invalid_setting", "Unknown usage mode.");
      next.usageMode = usageMode;
      next.maxTokens = MODE_TOKENS[usageMode];
      next.drafts = 1;
    }
  }
  const displayName = body.displayName !== undefined
    ? validateDisplayName(body.displayName, s.user.username)
    : s.user.display_name;

  await c.env.DB.prepare("UPDATE users SET display_name = ?, settings = ?, updated_at = ? WHERE id = ?")
    .bind(displayName, JSON.stringify(next), nowSeconds(), s.user.id)
    .run();
  return json({ user: await publicUser(c.env, { ...s.user, display_name: displayName, settings: JSON.stringify(next) }) });
};

const changePassword: Handler = async (c) => {
  const s = await session(c);
  if (!(await rateLimit(c.env.DB, `password:${s.user.id}`, 5, 900))) throw tooManyRequests("Too many attempts. Try again later.");
  const body = await readJson<{ currentPassword?: string; newPassword?: string }>(c.request);
  if (!(await verifyPassword(String(body.currentPassword ?? ""), s.user))) {
    throw new HttpError(400, "invalid_credentials", "Your current password is incorrect.");
  }
  const password = validatePassword(body.newPassword, s.user.username);
  const { hash, salt, iterations } = await hashPassword(password);
  await c.env.DB.batch([
    c.env.DB.prepare("UPDATE users SET password_hash = ?, password_salt = ?, password_iterations = ?, updated_at = ? WHERE id = ?")
      .bind(hash, salt, iterations, nowSeconds(), s.user.id),
    // Changing the password signs out every other device.
    c.env.DB.prepare("DELETE FROM sessions WHERE user_id = ? AND id != ?").bind(s.user.id, s.id),
  ]);
  return json({ ok: true });
};

const revokeOtherSessions: Handler = async (c) => {
  const s = await session(c);
  const result = await c.env.DB.prepare("DELETE FROM sessions WHERE user_id = ? AND id != ?").bind(s.user.id, s.id).run();
  return json({ ok: true, revoked: result.meta.changes ?? 0 });
};

const deleteMe: Handler = async (c) => {
  const s = await session(c);
  const body = await readJson<{ password?: string }>(c.request);
  if (!(await verifyPassword(String(body.password ?? ""), s.user))) {
    throw new HttpError(400, "invalid_credentials", "Password is incorrect.");
  }
  await c.env.DB.prepare("DELETE FROM users WHERE id = ?").bind(s.user.id).run();
  console.log(JSON.stringify({ message: "account deleted", userId: s.user.id }));
  return withCookie(json({ ok: true }), clearSessionCookie(c.secure));
};

const getAvatar: Handler = async (c) => {
  const s = await session(c);
  const row = await c.env.DB.prepare("SELECT content_type, data FROM avatars WHERE user_id = ?")
    .bind(s.user.id)
    .first<{ content_type: string; data: ArrayBuffer | number[] }>();
  if (!row) throw new HttpError(404, "not_found", "No profile picture.");
  const bytes = row.data instanceof ArrayBuffer ? new Uint8Array(row.data) : Uint8Array.from(row.data);
  return new Response(bytes, {
    headers: {
      "content-type": row.content_type,
      // The client requests ?v=<avatar_version>, so a new upload gets a new URL.
      "cache-control": "private, max-age=31536000, immutable",
      "x-content-type-options": "nosniff",
    },
  });
};

const putAvatar: Handler = async (c) => {
  const s = await session(c);
  if (!(await rateLimit(c.env.DB, `avatar:${s.user.id}`, 20, 3600))) throw tooManyRequests("Too many uploads. Try again later.");
  if (Number(c.request.headers.get("content-length") ?? 0) > MAX_AVATAR_BYTES) {
    throw new HttpError(413, "too_large", "Images must be under 300 KB.");
  }
  const bytes = new Uint8Array(await c.request.arrayBuffer());
  if (bytes.byteLength === 0 || bytes.byteLength > MAX_AVATAR_BYTES) {
    throw new HttpError(413, "too_large", "Images must be under 300 KB.");
  }
  const type = sniffImage(bytes);
  if (!type) throw new HttpError(415, "bad_image", "Use a PNG, JPEG or WebP image.");
  const version = Date.now();
  await c.env.DB.batch([
    c.env.DB.prepare(
      `INSERT INTO avatars (user_id, content_type, data, updated_at) VALUES (?, ?, ?, ?)
       ON CONFLICT(user_id) DO UPDATE SET content_type = excluded.content_type, data = excluded.data, updated_at = excluded.updated_at`,
    ).bind(s.user.id, type, bytes, nowSeconds()),
    c.env.DB.prepare("UPDATE users SET avatar_version = ?, updated_at = ? WHERE id = ?").bind(version, nowSeconds(), s.user.id),
  ]);
  return json({ avatarVersion: version });
};

const deleteAvatar: Handler = async (c) => {
  const s = await session(c);
  await c.env.DB.batch([
    c.env.DB.prepare("DELETE FROM avatars WHERE user_id = ?").bind(s.user.id),
    c.env.DB.prepare("UPDATE users SET avatar_version = NULL, updated_at = ? WHERE id = ?").bind(nowSeconds(), s.user.id),
  ]);
  return json({ avatarVersion: null });
};

// ---------------------------------------------------------------------------
// Conversations + chat
// ---------------------------------------------------------------------------

interface MessageRow {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta: string | null;
  created_at: number;
}

function publicMessage(m: MessageRow) {
  return { id: m.id, role: m.role, content: m.content, meta: m.meta ? JSON.parse(m.meta) : null, createdAt: m.created_at };
}

async function ownedConversation(env: Env, userId: string, id: string) {
  const conv = await env.DB.prepare("SELECT id, title, created_at, updated_at FROM conversations WHERE id = ? AND user_id = ?")
    .bind(id, userId)
    .first<{ id: string; title: string; created_at: number; updated_at: number }>();
  if (!conv) throw new HttpError(404, "not_found", "Conversation not found.");
  return conv;
}

const listConversations: Handler = async (c) => {
  const s = await session(c);
  const { results } = await c.env.DB.prepare(
    "SELECT id, title, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT 200",
  )
    .bind(s.user.id)
    .all<{ id: string; title: string; updated_at: number }>();
  return json({ conversations: results.map((r) => ({ id: r.id, title: r.title, updatedAt: r.updated_at })) });
};

const getConversation: Handler = async (c) => {
  const s = await session(c);
  const conv = await ownedConversation(c.env, s.user.id, c.params[0]);
  const { results } = await c.env.DB.prepare(
    "SELECT id, role, content, meta, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at, rowid",
  )
    .bind(conv.id)
    .all<MessageRow>();
  return json({
    conversation: { id: conv.id, title: conv.title, updatedAt: conv.updated_at },
    messages: results.map(publicMessage),
  });
};

const deleteConversation: Handler = async (c) => {
  const s = await session(c);
  const conv = await ownedConversation(c.env, s.user.id, c.params[0]);
  await c.env.DB.prepare("DELETE FROM conversations WHERE id = ?").bind(conv.id).run();
  return json({ ok: true });
};

interface ModelCheck {
  name: string;
  ok: boolean;
  detail?: string;
}

interface ModelReply {
  files?: ProjectFile[];
  text: string;
  lang?: string;
  tokens?: number;
  ms?: number;
  step?: number;
  model?: string;
  prompt_tokens?: number;
  context_tokens?: number;
  finished?: boolean;
  syntax_ok?: boolean;
  checks?: { ok: boolean; checks: ModelCheck[]; stats?: Record<string, unknown> };
  drafts?: { total: number; passed: number };
}

async function askCoda(env: Env, prompt: string, language: Language, settings: Settings): Promise<ModelReply> {
  let res: Response;
  try {
    res = await modelFetch(env, "/api/generate", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(env.MODEL_TOKEN ? { authorization: `Bearer ${env.MODEL_TOKEN}` } : {}),
      },
      body: JSON.stringify({
        prompt,
        language,
        temperature: settings.temperature,
        max_tokens: settings.maxTokens,
        drafts: settings.drafts,
      }),
      // Styled HTML pages get a larger output budget on the local CPU.
      signal: AbortSignal.timeout(600_000),
    });
  } catch (err) {
    console.error(JSON.stringify({ message: "model unreachable", error: String(err) }));
    throw new HttpError(503, "model_offline", "Coda is offline right now. Your message wasn't sent.");
  }
  if (res.status === 503) throw new HttpError(503, "model_busy", "Coda is busy with another request. Try again in a moment.");
  if (!res.ok) {
    console.error(JSON.stringify({ message: "model error", status: res.status }));
    throw new HttpError(502, "model_error", "Coda couldn't answer that one. Try again.");
  }
  const data = (await res.json()) as ModelReply;
  if (typeof data.text !== "string") throw new HttpError(502, "model_error", "Coda returned an unexpected reply.");
  return { ...data, text: data.text.slice(0, 100_000) };
}

function replyMeta(reply: ModelReply) {
  const checks = (reply.checks?.checks ?? []).slice(0, 12).map((c) => ({
    name: String(c.name).slice(0, 60),
    ok: Boolean(c.ok),
    detail: String(c.detail ?? "").slice(0, 160),
  }));
  return {
    files: projectFiles(reply.files).length ? projectFiles(reply.files) : reply.lang === "html" ? projectFiles(extractWebsiteProject(reply.text)) : [],
    model: reply.model ?? null,
    promptTokens: reply.prompt_tokens ?? null,
    contextTokens: reply.context_tokens ?? null,
    lang: LANGUAGES.includes(reply.lang as Language) ? reply.lang : reply.lang === "text" ? "text" : "python",
    tokens: reply.tokens ?? null,
    ms: reply.ms ?? null,
    finished: reply.finished ?? null,
    syntaxOk: reply.syntax_ok ?? null,
    checks,
    stats: reply.checks?.stats ?? null,
    drafts: reply.drafts ?? null,
  };
}

const chat: Handler = async (c) => {
  const s = await session(c);
  const { env } = c;
  if (!(await rateLimit(env.DB, `chat:${s.user.id}`, 10, 60))) throw tooManyRequests("You're sending messages too quickly.");

  const body = await readJson<{ conversationId?: string | null; message?: string; language?: string }>(c.request);
  const message = String(body.message ?? "").replace(/\r\n/g, "\n").trim();
  if (!message) throw new HttpError(400, "empty_message", "Write a message first.");
  if (message.length > MAX_MESSAGE_CHARS) {
    throw new HttpError(400, "message_too_long", `Keep messages under ${MAX_MESSAGE_CHARS} characters.`);
  }
  const language = (body.language ?? "auto") as Language;
  if (!LANGUAGES.includes(language)) throw new HttpError(400, "invalid_language", "Unknown language.");

  const usage = await usageFor(env, s.user.id);
  if (usage.used >= usage.limit) {
    throw new HttpError(429, "daily_limit", "You've used today's messages. They reset at midnight UTC.", { usage });
  }

  const existing = body.conversationId ? await ownedConversation(env, s.user.id, body.conversationId) : null;
  const reply = await askCoda(env, message, language, parseSettings(s.user.settings));

  const now = nowSeconds();
  const conversationId = existing?.id ?? crypto.randomUUID();
  const title = existing?.title ?? titleFrom(message);
  const userMeta = JSON.stringify({ language });
  const userMsg: MessageRow = { id: crypto.randomUUID(), role: "user", content: message, meta: userMeta, created_at: now };
  const meta = JSON.stringify(replyMeta(reply));
  const botMsg: MessageRow = { id: crypto.randomUUID(), role: "assistant", content: reply.text, meta, created_at: now };

  const insertMessage = (m: MessageRow) =>
    env.DB.prepare("INSERT INTO messages (id, conversation_id, role, content, meta, created_at) VALUES (?, ?, ?, ?, ?, ?)")
      .bind(m.id, conversationId, m.role, m.content, m.meta, m.created_at);

  await env.DB.batch([
    existing
      ? env.DB.prepare("UPDATE conversations SET updated_at = ? WHERE id = ?").bind(now, conversationId)
      : env.DB.prepare("INSERT INTO conversations (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)")
          .bind(conversationId, s.user.id, title, now, now),
    insertMessage(userMsg),
    insertMessage(botMsg),
    env.DB.prepare(
      `INSERT INTO usage (user_id, day, count) VALUES (?, ?, 1)
       ON CONFLICT(user_id, day) DO UPDATE SET count = count + 1`,
    ).bind(s.user.id, utcDay()),
  ]);

  return json({
    conversation: { id: conversationId, title, updatedAt: now },
    messages: [publicMessage(userMsg), publicMessage(botMsg)],
    usage: { ...usage, used: usage.used + 1 },
  });
};

// ---------------------------------------------------------------------------
// Live preview of generated HTML/CSS (sandboxed: opaque origin, no network, no cookies)
// ---------------------------------------------------------------------------

const PREVIEW_CSP = [
  "sandbox allow-scripts allow-forms allow-modals",
  "default-src 'none'",
  "style-src 'unsafe-inline'",
  "script-src 'unsafe-inline'",
  "img-src data: blob: https:",
  "font-src data: https:",
  "media-src data: https:",
  "connect-src 'none'",
  "form-action 'none'",
  "base-uri 'none'",
  "frame-ancestors 'self'",
].join("; ");

// Sandboxed pages have no storage; give generated apps an in-memory stand-in so they still run.
const PREVIEW_SHIM =
  "<script>(function(){function mem(){var d={};return{getItem:function(k){return Object.prototype.hasOwnProperty.call(d,k)?d[k]:null}," +
  "setItem:function(k,v){d[k]=String(v)},removeItem:function(k){delete d[k]},clear:function(){d={}},key:function(i){return Object.keys(d)[i]||null}," +
  "get length(){return Object.keys(d).length}}}['localStorage','sessionStorage'].forEach(function(n){try{window[n].getItem('x')}catch(e){" +
  "Object.defineProperty(window,n,{value:mem(),configurable:true})}})})();</script>";

const CSS_PLAYGROUND = (css: string) => `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CSS preview</title>
<style>body{margin:0;font-family:system-ui,sans-serif}.demo{padding:24px;display:grid;gap:24px}</style>
<style>
${css}
</style>
</head>
<body>
<nav class="navbar nav"><a class="brand logo" href="#">Brand</a><ul><li><a class="active" href="#">Home</a></li><li><a href="#">About</a></li><li><a href="#">Contact</a></li></ul></nav>
<section class="hero"><h1>Preview heading</h1><p>This page shows common elements so you can see your CSS.</p></section>
<main class="demo container">
<div><button class="btn btn-primary button button-primary">Primary</button> <button class="btn btn-secondary button button-secondary">Secondary</button> <button class="btn btn-primary" disabled>Disabled</button></div>
<div class="grid"><article class="card"><h3 class="card-title">Card title</h3><p class="card-text">Some supporting text for this card.</p></article><article class="card"><h3 class="card-title">Second card</h3><p class="card-text">More text here.</p></article><article class="card"><h3 class="card-title">Third card</h3><p class="card-text">And a little more.</p></article></div>
<div><div class="alert alert-success">Saved successfully.</div><div class="alert alert-warning">Check your input.</div><div class="alert alert-error">Something went wrong.</div><div class="alert alert-info">Heads up.</div></div>
<div><span class="badge badge-gray">Draft</span> <span class="badge badge-green">Live</span> <span class="badge badge-blue">New</span> <span class="badge badge-red">Error</span></div>
<form class="form"><label>Name <input type="text" placeholder="Ada Lovelace"></label><label>Topic <select><option>Question</option></select></label><label>Message <textarea rows="3"></textarea></label><button type="button">Send</button></form>
<table class="table"><thead><tr><th>Name</th><th>Role</th></tr></thead><tbody><tr><td>Ada</td><td>Engineer</td></tr><tr><td>Grace</td><td>Admiral</td></tr><tr><td>Linus</td><td>Maintainer</td></tr></tbody></table>
<div class="progress"><div class="progress-bar" style="width: 60%"></div></div>
<div><span class="spinner"></span> <label class="switch"><input type="checkbox" checked><span class="slider"></span></label></div>
<div class="center"><div class="box">Centered box</div></div>
</main>
</body>
</html>`;

const previewMessage: Handler = async (c) => {
  const s = await session(c);
  const row = await c.env.DB.prepare(
    `SELECT m.content, m.meta FROM messages m JOIN conversations c ON c.id = m.conversation_id
     WHERE m.id = ? AND c.user_id = ? AND m.role = 'assistant'`,
  )
    .bind(c.params[0], s.user.id)
    .first<{ content: string; meta: string | null }>();
  if (!row) throw new HttpError(404, "not_found", "Not found.");
  const lang = row.meta ? (JSON.parse(row.meta) as { lang?: string }).lang : "python";
  let html: string;
  if (lang === "html") {
    const files = projectFiles(row.meta ? JSON.parse(row.meta).files : []);
    html = projectPreview(files.find(file => file.path === "index.html")?.content ?? row.content, files);
  }
  else if (lang === "css") html = CSS_PLAYGROUND(row.content.replace(/<\/style/gi, "<\\/style"));
  else throw new HttpError(415, "not_previewable", "Only HTML and CSS can be previewed.");
  const page = /<head[^>]*>/i.test(html) ? html.replace(/<head[^>]*>/i, (tag) => tag + PREVIEW_SHIM) : PREVIEW_SHIM + html;
  return new Response(page, {
    headers: {
      "content-type": "text/html; charset=utf-8",
      "content-security-policy": PREVIEW_CSP,
      "x-frame-options": "SAMEORIGIN",
      "cache-control": "private, no-store",
      "referrer-policy": "no-referrer",
    },
  });
};

// ---------------------------------------------------------------------------
// Routing
// ---------------------------------------------------------------------------

const ID = "([0-9a-f-]{36})";
const routes: [string, RegExp, Handler][] = [
  ["GET", /^\/api\/config$/, getConfig],
  ["GET", /^\/api\/status$/, getStatus],
  ["POST", /^\/api\/auth\/signup$/, signup],
  ["POST", /^\/api\/auth\/login$/, login],
  ["POST", /^\/api\/auth\/logout$/, logout],
  ["GET", /^\/api\/me$/, getMe],
  ["PATCH", /^\/api\/me$/, updateMe],
  ["DELETE", /^\/api\/me$/, deleteMe],
  ["POST", /^\/api\/me\/password$/, changePassword],
  ["POST", /^\/api\/me\/sessions\/revoke-others$/, revokeOtherSessions],
  ["GET", /^\/api\/me\/avatar$/, getAvatar],
  ["PUT", /^\/api\/me\/avatar$/, putAvatar],
  ["DELETE", /^\/api\/me\/avatar$/, deleteAvatar],
  ["GET", /^\/api\/conversations$/, listConversations],
  ["GET", new RegExp(`^/api/conversations/${ID}$`), getConversation],
  ["DELETE", new RegExp(`^/api/conversations/${ID}$`), deleteConversation],
  ["POST", /^\/api\/chat$/, chat],
  ["GET", new RegExp(`^/api/messages/${ID}/preview$`), previewMessage],
];

async function cleanup(db: D1Database): Promise<void> {
  const now = nowSeconds();
  await db.batch([
    db.prepare("DELETE FROM sessions WHERE expires_at < ?").bind(now),
    db.prepare("DELETE FROM rate_limits WHERE window_start < ?").bind(now - 86_400),
  ]);
}

export default {
  async fetch(request, env, ctx): Promise<Response> {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) {
      if (request.method !== "GET" && request.method !== "HEAD") return new Response("Method not allowed", { status: 405 });
      if (url.pathname === "/info" || url.pathname === "/info/") {
        return env.ASSETS.fetch(request);
      }
      if (url.pathname === "/" || /^\/c\/[0-9a-f-]{36}$/.test(url.pathname) || /^\/(?:app\.css|app\.js|theme\.js|project\.js|favicon\.png|info\.html|404\.html|sandbox\/run\.html)$/.test(url.pathname)) {
        return env.ASSETS.fetch(request);
      }
      const asset = await env.ASSETS.fetch(new Request(new URL("/404", url), request));
      const headers = new Headers(asset.headers);
      headers.set("content-type", "text/html; charset=utf-8");
      headers.set("cache-control", "no-store");
      headers.set("x-content-type-options", "nosniff");
      return new Response(asset.body, { status: 404, headers });
    }

    const secure = url.protocol === "https:";
    try {
      assertSameOrigin(request, url);
      let pathMatched = false;
      for (const [method, pattern, handler] of routes) {
        const match = pattern.exec(url.pathname);
        if (!match) continue;
        pathMatched = true;
        if (method !== request.method) continue;
        const response = await handler({ request, env, ctx, url, secure, params: match.slice(1) });
        if (Math.random() < 0.01) ctx.waitUntil(cleanup(env.DB));
        response.headers.set("x-content-type-options", "nosniff");
        return response;
      }
      throw pathMatched
        ? new HttpError(405, "method_not_allowed", "Method not allowed.")
        : new HttpError(404, "not_found", "Not found.");
    } catch (err) {
      if (err instanceof HttpError) return errorResponse(err);
      console.error(JSON.stringify({ message: "unhandled error", path: url.pathname, error: err instanceof Error ? err.stack : String(err) }));
      return errorResponse(new HttpError(500, "internal", "Something went wrong on our side."));
    }
  },
} satisfies ExportedHandler<Env>;
