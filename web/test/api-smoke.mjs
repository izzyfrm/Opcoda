// API smoke test for a local `wrangler dev` (default http://127.0.0.1:8787).
// Creates throwaway accounts with random names and deletes them at the end.
//   node test/api-smoke.mjs [baseUrl]
import { randomBytes } from "node:crypto";

const BASE = process.argv[2] ?? "http://127.0.0.1:8787";
const ORIGIN = new URL(BASE).origin;
let failures = 0;

function check(label, condition, detail = "") {
  console.log(`${condition ? "ok  " : "FAIL"} ${label}${detail && !condition ? ` — ${detail}` : ""}`);
  if (!condition) failures++;
}

function client() {
  let cookie = "";
  return async function call(path, { method = "GET", body, headers = {}, raw, origin = ORIGIN } = {}) {
    const h = { ...headers };
    if (origin) h.origin = origin;
    if (cookie) h.cookie = cookie;
    let payload;
    if (raw !== undefined) payload = raw;
    else if (body !== undefined) {
      payload = JSON.stringify(body);
      h["content-type"] = "application/json";
    }
    const res = await fetch(BASE + path, { method, headers: h, body: payload, redirect: "manual" });
    const setCookie = res.headers.get("set-cookie");
    if (setCookie) cookie = setCookie.split(";")[0];
    const type = res.headers.get("content-type") ?? "";
    const data = type.includes("json") ? await res.json() : null;
    return { status: res.status, data, setCookie };
  };
}

const name = () => `t_${randomBytes(4).toString("hex")}`;
const password = () => randomBytes(12).toString("base64url");

const alice = client();
const bob = client();
const anon = client();
const aliceName = name();
const alicePass = password();
const bobName = name();
const bobPass = password();

// --- sign-up and cookies
let r = await alice("/api/auth/signup", { method: "POST", body: { username: aliceName, password: alicePass, displayName: "Alice" } });
check("signup succeeds", r.status === 201, JSON.stringify(r.data));
check("session cookie is HttpOnly + SameSite=Lax", /HttpOnly/i.test(r.setCookie ?? "") && /SameSite=Lax/i.test(r.setCookie ?? ""));
check("password hash never returned", !JSON.stringify(r.data).includes("password"));

r = await anon("/api/auth/signup", { method: "POST", body: { username: aliceName.toUpperCase(), password: password() } });
check("duplicate username (case-insensitive) rejected", r.status === 409, r.status);
r = await anon("/api/auth/signup", { method: "POST", body: { username: name(), password: "short" } });
check("weak password rejected", r.status === 400 && r.data?.error?.code === "weak_password");
r = await anon("/api/auth/signup", { method: "POST", body: { username: "x", password: password() } });
check("invalid username rejected", r.status === 400 && r.data?.error?.code === "invalid_username");

// --- CSRF / origin
r = await anon("/api/auth/login", { method: "POST", body: { username: aliceName, password: alicePass }, origin: "https://evil.example" });
check("cross-site POST blocked", r.status === 403);
r = await anon("/api/auth/login", { method: "POST", body: { username: aliceName, password: alicePass }, origin: null });
check("POST without Origin blocked", r.status === 403);

// --- auth required
for (const path of ["/api/me", "/api/conversations", "/api/me/avatar"]) {
  r = await anon(path);
  check(`anonymous GET ${path} -> 401`, r.status === 401);
}

// --- login
r = await anon("/api/auth/login", { method: "POST", body: { username: aliceName, password: "wrong-password" } });
check("wrong password -> 401 generic message", r.status === 401 && r.data?.error?.message === "Username or password is incorrect.");
r = await anon("/api/auth/login", { method: "POST", body: { username: "nobody_here", password: "whatever123" } });
check("unknown user -> same 401 message", r.status === 401 && r.data?.error?.message === "Username or password is incorrect.");
r = await bob("/api/auth/signup", { method: "POST", body: { username: bobName, password: bobPass } });
check("second account created", r.status === 201);

// --- settings validation
r = await alice("/api/me", { method: "PATCH", body: { settings: { temperature: 5 } } });
check("out-of-range setting rejected", r.status === 400);
r = await alice("/api/me", { method: "PATCH", body: { displayName: "Alice B", settings: { theme: "dark", maxTokens: 128 } } });
check("settings saved", r.status === 200 && r.data.user.settings.theme === "dark" && r.data.user.displayName === "Alice B");

// --- avatar validation
r = await alice("/api/me/avatar", { method: "PUT", raw: "not an image at all", headers: { "content-type": "image/png" } });
check("non-image avatar rejected", r.status === 415);
const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==", "base64");
r = await alice("/api/me/avatar", { method: "PUT", raw: png, headers: { "content-type": "image/png" } });
check("PNG avatar accepted", r.status === 200 && r.data.avatarVersion);

// --- chat + ownership (works only while the model server is running)
r = await alice("/api/chat", { method: "POST", body: { message: "Return the square of x." } });
if (r.status === 200) {
  check("chat returns user + assistant messages", r.data.messages.length === 2 && r.data.messages[1].role === "assistant");
  const convId = r.data.conversation.id;
  r = await bob(`/api/conversations/${convId}`);
  check("other users can't read a conversation", r.status === 404);
  r = await bob(`/api/conversations/${convId}`, { method: "DELETE" });
  check("other users can't delete a conversation", r.status === 404);
  r = await alice(`/api/conversations/${convId}`);
  check("owner can read the conversation", r.status === 200 && r.data.messages.length === 2);
} else {
  check("chat reports the model as offline (model server not running)", r.status === 503, `${r.status} ${JSON.stringify(r.data)}`);
}
r = await alice("/api/chat", { method: "POST", body: { message: "x".repeat(501) } });
check("over-long message rejected", r.status === 400);

// --- password change signs out other sessions
const alice2 = client();
await alice2("/api/auth/login", { method: "POST", body: { username: aliceName, password: alicePass } });
const newPass = password();
r = await alice("/api/me/password", { method: "POST", body: { currentPassword: "nope-nope", newPassword: newPass } });
check("password change needs the current password", r.status === 400);
r = await alice("/api/me/password", { method: "POST", body: { currentPassword: alicePass, newPassword: newPass } });
check("password changed", r.status === 200);
r = await alice2("/api/me");
check("other session signed out after password change", r.status === 401);
r = await alice("/api/me");
check("current session still valid", r.status === 200);

// --- logout + delete
r = await bob("/api/auth/logout", { method: "POST", body: {} });
check("logout ok", r.status === 200);
r = await bob("/api/me");
check("session gone after logout", r.status === 401);
await bob("/api/auth/login", { method: "POST", body: { username: bobName, password: bobPass } });
r = await bob("/api/me", { method: "DELETE", body: { password: "wrong" } });
check("account deletion needs the password", r.status === 400);
for (const [who, pass] of [[bob, bobPass], [alice, newPass]]) {
  r = await who("/api/me", { method: "DELETE", body: { password: pass } });
  check("account deleted", r.status === 200);
}
r = await alice("/api/auth/login", { method: "POST", body: { username: aliceName, password: newPass } });
check("deleted account can't sign in", r.status === 401);

console.log(failures ? `\n${failures} check(s) failed` : "\nall checks passed");
process.exit(failures ? 1 : 0);
