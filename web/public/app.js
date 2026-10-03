// Opcoda web client. No framework, no build step.
import { projectZip } from "./project.js";
const $ = (id) => document.getElementById(id);

const LANG_LABEL = { html: "HTML", css: "CSS", javascript: "JavaScript", python: "Python", text: "Text" };
const FILE_NAME = { html: "index.html", css: "styles.css", javascript: "script.js", python: "main.py", text: "output.txt" };
const CAN_PREVIEW = new Set(["html", "css"]);
const CAN_RUN = new Set(["python", "javascript"]);
const WIDE = "(min-width: 1181px)";

const state = {
  config: { inviteRequired: false, dailyLimit: 25, maxMessageChars: 6000 },
  me: null,
  conversations: [],
  activeId: null,
  messages: new Map(), // id -> assistant message shown in this chat
  artifactId: null, // message open in the workspace
  selectedFile: null,
  sending: false,
  authMode: "login",
  statusTimer: null,
  modelStatus: null,
  warnedText: null,
  attachment: null,
  prefs: {}, // loaded in boot()
  skills: { catalog: [], online: null, applies: true, loading: null },
  autoFixed: new Set(), // answers that already had their one automatic fix
};

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

class ApiError extends Error {
  constructor(status, code, message, extra = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.extra = extra;
  }
}

async function api(path, { method = "GET", body, blob } = {}) {
  const init = { method, headers: {}, credentials: "same-origin" };
  if (blob) {
    init.body = blob;
    init.headers["content-type"] = blob.type;
  } else if (body !== undefined) {
    init.body = JSON.stringify(body);
    init.headers["content-type"] = "application/json";
  }
  let res;
  try {
    res = await fetch(path, init);
  } catch {
    throw new ApiError(0, "network", "Can't reach Opcoda. Check your connection and try again.");
  }
  const data = (res.headers.get("content-type") || "").includes("json") ? await res.json() : null;
  if (!res.ok) {
    const err = data?.error ?? {};
    const error = new ApiError(res.status, err.code ?? "error", err.message ?? "Something went wrong.", err);
    if (res.status === 401 && state.me && path !== "/api/auth/login") sessionEnded();
    throw error;
  }
  return data;
}

// ---------------------------------------------------------------------------
// Small UI helpers
// ---------------------------------------------------------------------------

let toastTimer;
function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.hidden = true), 3200);
}

function setBusy(button, busy) {
  button.disabled = busy;
  button.classList.toggle("is-loading", busy);
  button.setAttribute("aria-busy", String(busy));
}

function showError(el, message) {
  el.textContent = message || "";
  el.hidden = !message;
}

function icon(name) {
  return `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function initials(name) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const letters = parts.length > 1 ? parts[0][0] + parts[parts.length - 1][0] : (parts[0] || "?").slice(0, 2);
  return letters.toUpperCase();
}

function renderAvatar(target, user) {
  target.replaceChildren();
  if (user.avatarVersion) {
    const img = document.createElement("img");
    img.alt = "";
    img.src = `/api/me/avatar?v=${user.avatarVersion}`;
    img.addEventListener("error", () => { target.textContent = initials(user.displayName); }, { once: true });
    target.append(img);
  } else {
    target.textContent = initials(user.displayName);
  }
}

function applyTheme(theme) {
  if (theme === "light" || theme === "dark") document.documentElement.dataset.theme = theme;
  else delete document.documentElement.dataset.theme;
  try {
    localStorage.setItem("opcoda-theme", theme);
  } catch {
    // ignore
  }
}

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.max(1, Math.round((seconds % 3600) / 60));
  return h ? `${h}h ${m}m` : `${m}m`;
}

function lineCount(code) {
  return code.replace(/\n+$/, "").split("\n").length;
}

// ---------------------------------------------------------------------------
// Syntax highlighting (every emitted character is escaped)
// ---------------------------------------------------------------------------

const escapeHtml = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const tok = (kind, text) => (text ? `<span class="tok-${kind}">${escapeHtml(text)}</span>` : "");

const PY_KEYWORDS = new Set(
  "False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda match case nonlocal not or pass raise return try while with yield self".split(" "),
);
const PY_TOKEN = /(#[^\n]*)|([rbfu]{0,2}"""[\s\S]*?(?:"""|$)|[rbfu]{0,2}'''[\s\S]*?(?:'''|$)|[rbfu]{0,2}"(?:\\.|[^"\\\n])*"?|[rbfu]{0,2}'(?:\\.|[^'\\\n])*'?)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)/g;

function highlightPython(code) {
  let out = "";
  let last = 0;
  let prev = "";
  for (const m of code.matchAll(PY_TOKEN)) {
    const [text, comment, string, number, word] = m;
    out += escapeHtml(code.slice(last, m.index));
    if (comment) out += tok("com", text);
    else if (string) out += tok("str", text);
    else if (number) out += tok("num", text);
    else if (PY_KEYWORDS.has(word)) out += tok("kw", text);
    else if (prev === "def" || prev === "class" || code[m.index + text.length] === "(") out += tok("fn", text);
    else out += escapeHtml(text);
    prev = word || "";
    last = m.index + text.length;
  }
  return out + escapeHtml(code.slice(last));
}

const JS_KEYWORDS = new Set(
  "async await break case catch class const continue debugger default delete do else export extends false finally for function if import in instanceof let new null of return static super switch this throw true try typeof undefined var void while with yield".split(" "),
);
const JS_TOKEN = /(\/\/[^\n]*|\/\*[\s\S]*?(?:\*\/|$))|(`(?:\\[\s\S]|[^`\\])*`?|"(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_$][\w$]*)/g;

function highlightJs(code) {
  let out = "";
  let last = 0;
  for (const m of code.matchAll(JS_TOKEN)) {
    const [text, comment, string, number, word] = m;
    out += escapeHtml(code.slice(last, m.index));
    if (comment) out += tok("com", text);
    else if (string) out += tok("str", text);
    else if (number) out += tok("num", text);
    else if (JS_KEYWORDS.has(word)) out += tok("kw", text);
    else if (code[m.index + text.length] === "(") out += tok("fn", text);
    else out += escapeHtml(text);
    last = m.index + text.length;
  }
  return out + escapeHtml(code.slice(last));
}

const CSS_VALUE = /("[^"]*"|'[^']*')|(#[0-9a-fA-F]{3,8}\b)|(-?\d*\.?\d+(?:px|rem|em|%|vh|vw|s|ms|deg|fr|ch)?\b)|([\w-]+)(?=\()/g;

function highlightCssValue(value) {
  let out = "";
  let last = 0;
  for (const m of value.matchAll(CSS_VALUE)) {
    out += escapeHtml(value.slice(last, m.index));
    if (m[1]) out += tok("str", m[0]);
    else if (m[2] || m[3]) out += tok("num", m[0]);
    else out += tok("fn", m[0]);
    last = m.index + m[0].length;
  }
  return out + escapeHtml(value.slice(last));
}

function highlightCss(code) {
  let out = "";
  let i = 0;
  const stack = [];
  while (i < code.length) {
    if (code.startsWith("/*", i)) {
      const end = code.indexOf("*/", i + 2);
      const stop = end === -1 ? code.length : end + 2;
      out += tok("com", code.slice(i, stop));
      i = stop;
      continue;
    }
    let j = i;
    const inRule = stack[stack.length - 1] === "rule";
    while (j < code.length && !"{};".includes(code[j]) && !code.startsWith("/*", j)) j++;
    const text = code.slice(i, j);
    if (inRule) {
      const m = text.match(/^(\s*)(-{0,2}[A-Za-z][\w-]*)(\s*:)([\s\S]*)$/);
      out += m ? escapeHtml(m[1]) + tok("prop", m[2]) + escapeHtml(m[3]) + highlightCssValue(m[4]) : escapeHtml(text);
    } else {
      const lead = text.match(/^\s*/)[0];
      const body = text.slice(lead.length).replace(/\s+$/, "");
      const trail = text.slice(lead.length + body.length);
      out += escapeHtml(lead) + (body.startsWith("@") ? tok("at", body) : tok("sel", body)) + escapeHtml(trail);
    }
    if (j >= code.length) break;
    const ch = code[j];
    if (ch === "{") stack.push(!inRule && text.trim().startsWith("@") && !/^@(font-face|page)/.test(text.trim()) ? "group" : "rule");
    else if (ch === "}") stack.pop();
    if (!code.startsWith("/*", j)) {
      out += escapeHtml(ch);
      i = j + 1;
    } else {
      i = j;
    }
  }
  return out;
}

function highlightTag(tag) {
  const m = tag.match(/^(<\/?)([A-Za-z][\w-]*)([\s\S]*?)(\/?>)$/);
  if (!m) return escapeHtml(tag);
  let attrs = "";
  let last = 0;
  for (const a of m[3].matchAll(/([^\s=/>]+)(\s*=\s*)?("[^"]*"|'[^']*'|[^\s"'>]+)?/g)) {
    attrs += escapeHtml(m[3].slice(last, a.index)) + tok("attr", a[1]) + escapeHtml(a[2] || "") + tok("str", a[3] || "");
    last = a.index + a[0].length;
  }
  attrs += escapeHtml(m[3].slice(last));
  return escapeHtml(m[1]) + tok("tag", m[2]) + attrs + escapeHtml(m[4]);
}

const HTML_TOKEN = /(<!--[\s\S]*?(?:-->|$))|(<!DOCTYPE[^>]*>)|(<style\b[^>]*>)([\s\S]*?)(?=<\/style>|$)|(<script\b[^>]*>)([\s\S]*?)(?=<\/script>|$)|(<\/?[A-Za-z][\w-]*(?:\s[^>]*)?>)/gi;

function highlightHtml(code) {
  let out = "";
  let last = 0;
  for (const m of code.matchAll(HTML_TOKEN)) {
    out += escapeHtml(code.slice(last, m.index));
    if (m[1]) out += tok("com", m[1]);
    else if (m[2]) out += tok("kw", m[2]);
    else if (m[3] !== undefined) out += highlightTag(m[3]) + highlightCss(m[4] || "");
    else if (m[5] !== undefined) out += highlightTag(m[5]) + highlightJs(m[6] || "");
    else out += highlightTag(m[7]);
    last = m.index + m[0].length;
  }
  return out + escapeHtml(code.slice(last));
}

function highlight(code, lang) {
  if (lang === "html") return highlightHtml(code);
  if (lang === "css") return highlightCss(code);
  if (lang === "javascript") return highlightJs(code);
  if (lang === "python") return highlightPython(code);
  return escapeHtml(code);
}

// ---------------------------------------------------------------------------
// Auth screen
// ---------------------------------------------------------------------------

function setAuthMode(mode) {
  state.authMode = mode;
  const signup = mode === "signup";
  $("tab-login").setAttribute("aria-selected", String(!signup));
  $("tab-signup").setAttribute("aria-selected", String(signup));
  $("auth-title").textContent = signup ? "Create your account" : "Sign in";
  $("auth-submit").textContent = signup ? "Create account" : "Sign in";
  $("auth-password").autocomplete = signup ? "new-password" : "current-password";
  document.querySelectorAll("#auth-form [data-signup]").forEach((node) => (node.hidden = !signup));
  $("invite-field").hidden = !(signup && state.config.inviteRequired);
  showError($("auth-error"), "");
  document.querySelectorAll("#auth-form input").forEach((i) => i.removeAttribute("aria-invalid"));
}

function showAuth(message = "") {
  stopStatusPolling();
  closeWorkspace();
  state.me = null;
  state.conversations = [];
  state.activeId = null;
  state.messages.clear();
  $("app").hidden = true;
  $("auth").hidden = false;
  $("boot").hidden = true;
  setAuthMode(state.authMode);
  showError($("auth-error"), message);
  $("auth-username").focus();
}

function sessionEnded() {
  for (const d of document.querySelectorAll("dialog[open]")) d.close();
  history.replaceState(null, "", "/");
  showAuth("Your session ended. Sign in again.");
}

async function submitAuth(event) {
  event.preventDefault();
  const signup = state.authMode === "signup";
  const username = $("auth-username").value.trim();
  const password = $("auth-password").value;
  const fail = (input, message) => {
    input?.setAttribute("aria-invalid", "true");
    showError($("auth-error"), message);
    input?.focus();
  };
  document.querySelectorAll("#auth-form input").forEach((i) => i.removeAttribute("aria-invalid"));

  if (!username) return fail($("auth-username"), "Enter your username.");
  if (signup && !/^[a-zA-Z][a-zA-Z0-9_]{2,19}$/.test(username)) {
    return fail($("auth-username"), "Usernames are 3–20 characters: letters, numbers and underscores, starting with a letter.");
  }
  if (!password) return fail($("auth-password"), "Enter your password.");
  if (signup && password.length < 8) return fail($("auth-password"), "Use at least 8 characters.");

  const button = $("auth-submit");
  setBusy(button, true);
  showError($("auth-error"), "");
  try {
    const body = signup
      ? { username, password, displayName: $("auth-display").value, inviteCode: $("auth-invite").value }
      : { username, password };
    const { user } = await api(signup ? "/api/auth/signup" : "/api/auth/login", { method: "POST", body });
    $("auth-password").value = "";
    await enterApp(user);
  } catch (err) {
    const field = {
      invalid_username: $("auth-username"),
      username_taken: $("auth-username"),
      weak_password: $("auth-password"),
      invalid_credentials: $("auth-password"),
      invalid_invite: $("auth-invite"),
    }[err.code];
    fail(field, err.message);
  } finally {
    setBusy(button, false);
  }
}

// ---------------------------------------------------------------------------
// Device preferences (this browser only)
// ---------------------------------------------------------------------------

const PREF_DEFAULTS = { enterToSend: true, autoOpen: true, autoRun: false, autoFix: false, wrap: false, sidebar: "open" };

function loadPrefs() {
  try {
    return { ...PREF_DEFAULTS, ...JSON.parse(localStorage.getItem("opcoda-prefs") || "{}") };
  } catch {
    return { ...PREF_DEFAULTS };
  }
}

function setPref(key, value) {
  state.prefs[key] = value;
  try {
    localStorage.setItem("opcoda-prefs", JSON.stringify(state.prefs));
  } catch {
    // ignore
  }
  applyPrefs();
}

function applyPrefs() {
  document.documentElement.dataset.wrap = String(Boolean(state.prefs.wrap));
  $("app").dataset.sidebar = state.prefs.sidebar === "collapsed" ? "collapsed" : "open";
  $("prompt").enterKeyHint = state.prefs.enterToSend ? "send" : "enter";
}

// ---------------------------------------------------------------------------
// App shell
// ---------------------------------------------------------------------------

async function enterApp(user) {
  state.me = user;
  applyTheme(user.settings.theme);
  applyPrefs();
  renderAccount();
  renderUsage();
  renderGreeting();
  syncUsageModeControls();
  restoreLanguage();
  renderSkillCounts();
  $("auth").hidden = true;
  $("boot").hidden = true;
  $("app").hidden = false;
  startStatusPolling();
  loadSkills();
  await loadConversations();
  await routeFromLocation();
  if (matchMedia("(hover: hover)").matches) $("prompt").focus();
}

function renderAccount() {
  const user = state.me;
  $("account-name").textContent = user.displayName;
  $("account-username").textContent = `@${user.username}`;
  $("account-btn").setAttribute("aria-label", `Account menu for ${user.displayName}`);
  $("menu-who").textContent = `@${user.username}`;
  renderAvatar($("account-avatar"), user);
}

function renderGreeting() {
  const hour = new Date().getHours();
  const part = hour < 5 ? "Up late" : hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const first = (state.me?.displayName || "").trim().split(/\s+/)[0];
  $("greeting").textContent = first ? `${part}, ${first}` : "What should we build?";
}

function renderUsage() {
  const { used, limit, resetsAt } = state.me.usage;
  const left = Math.max(0, limit - used);
  $("usage").textContent = `${left} left`;
  $("open-context").dataset.low = String(left <= 3);
  $("open-context").setAttribute("aria-label", `${left} of ${limit} messages left today. Show usage`);

  const note = $("composer-note");
  if (left === 0) {
    const wait = resetsAt - Math.floor(Date.now() / 1000);
    note.textContent = `You've used today's ${limit} messages. They reset in ${formatDuration(Math.max(wait, 60))}.`;
    note.dataset.tone = "warn";
  } else {
    note.textContent = "Coda can make mistakes. Check code before you use it.";
    delete note.dataset.tone;
  }
  updateComposer();
  if ($("context").open) renderContext();
}

function renderContext() {
  if (!state.me) return;
  const usage = state.me.usage;
  const settings = state.me.settings;
  const last = [...state.messages.values()].at(-1);
  const meta = last?.meta || {};
  const conversation = state.conversations.find((item) => item.id === state.activeId);
  $("context-chat").textContent = conversation?.title || "New chat";
  $("context-status").textContent = state.modelStatus?.online ? "Online" : "Offline";
  $("context-mode").textContent = (settings.usageMode || "medium").replace(/^./, (c) => c.toUpperCase());
  const websiteTokens = { light: 2400, medium: 3200, super: 4000, intense: 4800 };
  $("context-response").textContent = `Websites: up to ${(websiteTokens[settings.usageMode] || 3200).toLocaleString()} tokens`;
  const windowTokens = state.modelStatus?.contextTokens || meta.contextTokens;
  $("context-window").textContent = windowTokens ? `${windowTokens.toLocaleString()} tokens` : "—";
  $("context-skills").textContent = state.skills.catalog.length ? String(activeSkills().length) : "—";
  $("context-messages").textContent = String($("messages").querySelectorAll(".msg-user, .msg-bot").length);
  $("context-input").textContent = Number.isFinite(meta.promptTokens) ? `${meta.promptTokens.toLocaleString()} tokens` : "—";
  $("context-output").textContent = Number.isFinite(meta.tokens) ? `${meta.tokens.toLocaleString()} tokens` : "—";
  $("context-daily").textContent = `${usage.used} of ${usage.limit} used`;
  $("context-progress").max = usage.limit;
  $("context-progress").value = usage.used;
  $("context-reset").textContent = `Resets ${new Date(usage.resetsAt * 1000).toLocaleString()}`;
}

function updateComposer() {
  const left = state.me ? state.me.usage.limit - state.me.usage.used : 0;
  const prompt = $("prompt");
  const length = composedMessage(prompt.value).length;
  const tooLong = length > state.config.maxMessageChars;
  prompt.disabled = left <= 0;
  prompt.maxLength = state.config.maxMessageChars;
  for (const example of document.querySelectorAll(".example")) example.disabled = left <= 0;
  $("send").disabled = state.sending || left <= 0 || tooLong || (!prompt.value.trim() && !state.attachment);
  $("composer-count").textContent = state.attachment || length > state.config.maxMessageChars * .8 ? `${length.toLocaleString()} / ${state.config.maxMessageChars.toLocaleString()}` : "";
  $("composer-count").dataset.over = String(tooLong);
}

function autosize() {
  const prompt = $("prompt");
  prompt.style.height = "auto";
  prompt.style.height = `${Math.min(prompt.scrollHeight, 240)}px`;
}

function selectedLanguage() {
  return document.querySelector('input[name="lang"]:checked')?.value || "auto";
}

const ATTACHED_FILE = /\n\n<attached_file name="([^"]+)">\n([\s\S]*?)\n<\/attached_file>$/;

function composedMessage(prompt) {
  const text = prompt.trim();
  if (!state.attachment) return text;
  return `${text}${text ? "\n\n" : ""}<attached_file name="${state.attachment.name}">\n${state.attachment.content}\n</attached_file>`;
}

function splitAttachedFile(text) {
  const match = text.match(ATTACHED_FILE);
  return match ? { text: text.slice(0, match.index).trim(), fileName: match[1] } : { text, fileName: null };
}

function clearAttachment() {
  state.attachment = null;
  $("attachment-chip").hidden = true;
  $("attachment-name").textContent = "";
  $("file-input").value = "";
  updateComposer();
}

async function attachFile(file) {
  if (!file) return;
  if (file.size > 100 * 1024) return toast("Choose a code or text file under 100 KB.");
  const allowed = /\.(txt|md|html|css|js|jsx|ts|tsx|py|json|xml|ya?ml)$/i;
  if (!allowed.test(file.name)) return toast("That file type isn't supported yet.");
  const content = await file.text();
  if (content.includes("\0")) return toast("That file doesn't look like text.");
  const safeName = file.name.replace(/["<>]/g, "").slice(0, 80) || "attachment.txt";
  const shortened = content.length > 5_000;
  state.attachment = { name: safeName, content: content.slice(0, 5_000) };
  $("attachment-name").textContent = safeName;
  $("attachment-chip").hidden = false;
  updateComposer();
  $("prompt").focus();
  if (composedMessage($("prompt").value).length > state.config.maxMessageChars) toast("Shorten your prompt or attach a smaller file.");
  else if (shortened) toast("Attached the first 5,000 characters of that file.");
}

function syncUsageModeControls() {
  const mode = state.me?.settings?.usageMode || "medium";
  for (const radio of document.querySelectorAll('input[name="header-usage-mode"], input[name="usage-mode"]')) radio.checked = radio.value === mode;
}

// ---- popovers (model menu, language, skills, account) ----

const POPUPS = [
  ["model-menu", "model-trigger", ".model-picker"],
  ["tool-menu", "tool-trigger", ".popover-anchor"],
  ["skills-pop", "skills-trigger", ".popover-anchor"],
  ["account-menu", "account-btn", ".account"],
];

function setPopup(id, triggerId, open) {
  $(id).hidden = !open;
  $(triggerId).setAttribute("aria-expanded", String(open));
}

function togglePopup(id) {
  for (const [other, trigger] of POPUPS) {
    if (other !== id) setPopup(other, trigger, false);
  }
  const [, trigger] = POPUPS.find(([p]) => p === id);
  const open = $(id).hidden;
  setPopup(id, trigger, open);
  if (open && id === "skills-pop") renderSkillsQuick();
  if (open && id === "account-menu") $(id).querySelector("[role=menuitem]").focus();
  return open;
}

function closePopups({ restoreFocus = false } = {}) {
  let closed = false;
  for (const [id, trigger] of POPUPS) {
    if ($(id).hidden) continue;
    setPopup(id, trigger, false);
    if (restoreFocus) $(trigger).focus();
    closed = true;
  }
  return closed;
}

function setLanguage(lang) {
  for (const radio of document.querySelectorAll('input[name="lang"]')) radio.checked = radio.value === lang;
  $("tool-label").textContent = lang === "auto" ? "Auto" : (LANG_LABEL[lang] || lang);
  $("tool-trigger").dataset.lang = lang;
  $("tool-trigger").setAttribute("aria-label", `Language: ${lang === "auto" ? "auto detect" : LANG_LABEL[lang]}`);
  setPopup("tool-menu", "tool-trigger", false);
  try {
    localStorage.setItem("opcoda-lang", lang);
  } catch {
    // ignore
  }
}

function restoreLanguage() {
  let lang = "auto";
  try {
    lang = localStorage.getItem("opcoda-lang") || "auto";
  } catch {
    // ignore
  }
  setLanguage(["auto", "html", "css", "javascript", "python"].includes(lang) ? lang : "auto");
}

// ---- model status ----

async function checkStatus() {
  try {
    const status = await api("/api/status");
    state.modelStatus = status;
    setStatus(status.online ? "online" : "offline");
  } catch {
    state.modelStatus = { online: false };
    setStatus("offline");
  }
  if ($("context").open) renderContext();
}

function setStatus(stateName) {
  const node = $("status");
  node.dataset.state = stateName;
  const text = { online: "Online", offline: "Offline", checking: "Checking…" }[stateName];
  $("status-text").textContent = text;
  $("model-status-line").textContent = {
    online: "Online · ready for your next task",
    offline: "Offline · Coda's PC is off or not serving",
    checking: "Checking…",
  }[stateName];
  $("model-trigger").title = `Coda 1.0 · ${text}`;
}

function startStatusPolling() {
  stopStatusPolling();
  checkStatus();
  state.statusTimer = setInterval(() => {
    if (document.visibilityState === "visible") checkStatus();
  }, 60_000);
}

function stopStatusPolling() {
  clearInterval(state.statusTimer);
}

// ---- sidebar ----

const isMobile = () => matchMedia("(max-width: 860px)").matches;

function setDrawer(open) {
  $("app").dataset.drawer = open ? "open" : "closed";
  $("open-sidebar").setAttribute("aria-expanded", String(open));
  if (open) $("new-chat").focus();
}

function toggleSidebar() {
  if (isMobile()) return setDrawer($("app").dataset.drawer !== "open");
  setPref("sidebar", state.prefs.sidebar === "collapsed" ? "open" : "collapsed");
  $(state.prefs.sidebar === "collapsed" ? "open-sidebar" : "collapse-sidebar").focus();
}

function openSearch() {
  if (isMobile()) setDrawer(true);
  else if (state.prefs.sidebar === "collapsed") setPref("sidebar", "open");
  $("search-box").hidden = false;
  $("search-toggle").setAttribute("aria-expanded", "true");
  $("chat-search").focus();
  $("chat-search").select();
}

function closeSearch() {
  $("chat-search").value = "";
  $("search-box").hidden = true;
  $("search-toggle").setAttribute("aria-expanded", "false");
  renderConversationList();
}

// ---------------------------------------------------------------------------
// Conversations
// ---------------------------------------------------------------------------

async function loadConversations() {
  try {
    const { conversations } = await api("/api/conversations");
    state.conversations = conversations;
  } catch {
    state.conversations = [];
  }
  renderConversationList();
}

function dateGroup(seconds) {
  const day = 86_400_000;
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  const t = seconds * 1000;
  if (t >= start.getTime()) return "Today";
  if (t >= start.getTime() - day) return "Yesterday";
  if (t >= start.getTime() - 7 * day) return "Previous 7 days";
  if (t >= start.getTime() - 30 * day) return "Previous 30 days";
  return new Date(t).toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

function renderConversationList() {
  const holder = $("conversation-groups");
  const query = $("chat-search").value.trim().toLowerCase();
  const items = query ? state.conversations.filter((c) => c.title.toLowerCase().includes(query)) : state.conversations;
  holder.replaceChildren();
  let list = null;
  let current = null;
  for (const conv of items) {
    const group = query ? "Results" : dateGroup(conv.updatedAt);
    if (group !== current) {
      current = group;
      holder.append(el("h2", "history-label", group));
      list = el("ul");
      holder.append(list);
    }
    const li = el("li", "conv");
    if (conv.id === state.activeId) li.setAttribute("aria-current", "page");
    const link = el("a", "", conv.title);
    link.href = `/c/${conv.id}`;
    link.title = conv.title;
    link.addEventListener("click", (e) => {
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
      e.preventDefault();
      openConversation(conv.id, { push: true });
    });
    const del = el("button", "icon-btn conv-delete");
    del.type = "button";
    del.setAttribute("aria-label", `Delete chat: ${conv.title}`);
    del.title = "Delete chat";
    del.innerHTML = icon("trash");
    del.addEventListener("click", () => deleteConversation(conv));
    li.append(link, del);
    list.append(li);
  }
  const empty = $("history-empty");
  empty.hidden = items.length > 0;
  empty.textContent = query ? "No chats match that search." : "Your chats will show up here.";
}

async function routeFromLocation() {
  const match = location.pathname.match(/^\/c\/([0-9a-f-]{36})$/);
  if (match) await openConversation(match[1], { push: false });
  else newChat({ push: false });
}

function setEmpty(empty) {
  $("chat").dataset.empty = String(empty);
  $("empty-state").hidden = !empty;
}

function newChat({ push = true } = {}) {
  state.activeId = null;
  state.artifactId = null;
  state.messages.clear();
  closeWorkspace();
  $("messages").replaceChildren();
  setEmpty(true);
  renderGreeting();
  clearAttachment();
  if (push && location.pathname !== "/") history.pushState(null, "", "/");
  document.title = "Opcoda — Coda";
  renderConversationList();
  if (isMobile()) setDrawer(false);
  if ($("context").open) renderContext();
}

async function openConversation(id, { push }) {
  try {
    const { conversation, messages } = await api(`/api/conversations/${id}`);
    state.activeId = conversation.id;
    state.artifactId = null;
    state.messages.clear();
    closeWorkspace();
    const nodes = [];
    let lastUser = null;
    for (const m of messages) {
      if (m.role === "user") {
        lastUser = m;
        nodes.push(userMessage(m.content, m.meta?.language));
      } else {
        nodes.push(botMessage({ ...m, prompt: lastUser?.content, language: lastUser?.meta?.language || "auto" }));
      }
    }
    $("messages").replaceChildren(...nodes);
    setEmpty(messages.length === 0);
    if (push) history.pushState(null, "", `/c/${conversation.id}`);
    document.title = `${conversation.title} — Opcoda`;
    renderConversationList();
    if (isMobile()) setDrawer(false);
    scrollToBottom(true);
    if ($("context").open) renderContext();
  } catch (err) {
    if (err.status === 404) {
      toast("That chat doesn't exist anymore.");
      newChat();
    } else if (err.status !== 401) {
      toast(err.message);
    }
  }
}

async function deleteConversation(conv) {
  await confirmAction({
    text: `Delete “${conv.title}”? This can't be undone.`,
    okLabel: "Delete chat",
    run: async () => {
      await api(`/api/conversations/${conv.id}`, { method: "DELETE" });
      state.conversations = state.conversations.filter((c) => c.id !== conv.id);
      if (state.activeId === conv.id) newChat();
      else renderConversationList();
      toast("Chat deleted.");
    },
  });
}

// ---------------------------------------------------------------------------
// Messages
// ---------------------------------------------------------------------------

function actionButton(label, iconName, handler, { text = false } = {}) {
  const button = el("button", text ? "msg-action has-text" : "msg-action");
  button.type = "button";
  button.innerHTML = icon(iconName);
  if (text) button.append(el("span", "", label));
  button.setAttribute("aria-label", label);
  button.title = label;
  button.addEventListener("click", handler);
  return button;
}

function flashCopied(button, ok) {
  button.innerHTML = icon(ok ? "check" : "alert");
  button.title = ok ? "Copied" : "Copy failed";
  setTimeout(() => {
    button.innerHTML = icon("copy");
    button.title = button.getAttribute("aria-label");
  }, 1600);
}

function userMessage(text, language) {
  const li = el("li", "msg msg-user");
  const attached = splitAttachedFile(text);
  if (attached.fileName) {
    const file = el("div", "message-attachment");
    file.innerHTML = icon("paperclip");
    file.append(el("span", "", attached.fileName));
    li.append(file);
  }
  if (attached.text) {
    const bubble = el("div", "bubble", attached.text);
    if (language && language !== "auto") {
      const tag = el("span", "lang-tag bubble-lang", LANG_LABEL[language] || language);
      tag.dataset.lang = language;
      bubble.prepend(tag);
    }
    li.append(bubble);
  }
  const actions = el("div", "msg-actions");
  const copy = actionButton("Copy message", "copy", async () => flashCopied(copy, await copyText(attached.text || text)));
  const edit = actionButton("Edit in message box", "pencil", () => {
    $("prompt").value = attached.text;
    if (language) setLanguage(language);
    autosize();
    updateComposer();
    $("prompt").focus();
  });
  actions.append(copy, edit);
  li.append(actions);
  return li;
}

function messageLang(message) {
  return message.meta?.lang || "python";
}

function verdictFor(message) {
  const meta = message.meta || {};
  const checks = meta.checks || [];
  if (meta.finished === false) return { state: "warn", text: "Cut off" };
  if (checks.length) {
    const failed = checks.filter((c) => !c.ok).length;
    return failed ? { state: "warn", text: `${failed} ${failed === 1 ? "issue" : "issues"}` } : { state: "ok", text: "Checks passed" };
  }
  if (meta.syntaxOk === false) return { state: "warn", text: "Not valid" };
  if (meta.syntaxOk === true) return { state: "ok", text: "Valid" };
  return null;
}

function verdictNode(verdict) {
  const node = el("span", "verdict");
  node.dataset.state = verdict.state;
  node.innerHTML = icon(verdict.state === "ok" ? "check" : "alert");
  node.append(verdict.text);
  return node;
}

function metaLine(message) {
  const meta = message.meta || {};
  const parts = [];
  if (meta.drafts?.total > 1 && !meta.steps) parts.push(`${meta.drafts.passed} of ${meta.drafts.total} drafts passed`);
  const repairs = (meta.steps || []).filter((s) => s === "repair").length;
  if (meta.steps?.includes("plan")) parts.push("planned");
  if (repairs) parts.push(`self-fixed ${repairs}×`);
  if (meta.steps?.includes("review")) parts.push("reviewed");
  if (meta.ms) parts.push(`${(meta.ms / 1000).toFixed(1)} s`);
  if (Number.isFinite(meta.tokens)) parts.push(`${meta.tokens.toLocaleString()} tokens`);
  return parts.join(" · ");
}

function summaryText(message) {
  const lang = messageLang(message);
  const files = message.meta?.files || [];
  const lines = lineCount(message.content.replace(/\n+$/, ""));
  const what = files.length > 1 ? `a ${files.length}-file ${LANG_LABEL[lang] || ""} project` : `${LANG_LABEL[lang] || "the"} code`;
  const verdict = verdictFor(message);
  const tail = !verdict ? "" : verdict.state === "ok" ? " It passed every check." : message.meta?.finished === false
    ? " It stopped at the length limit, so it may be incomplete." : ` The checks found ${verdict.text}; open it to see details.`;
  return `Here's ${what} (${lines} ${lines === 1 ? "line" : "lines"}).${tail}`;
}

function botMessage(message) {
  state.messages.set(message.id, message);
  const lang = messageLang(message);
  const code = message.content.replace(/\n+$/, "");
  const lines = lineCount(code);
  const files = message.meta?.files || [];

  const li = el("li", "msg msg-bot");
  li.dataset.id = message.id;
  const avatar = el("div", "bot-avatar");
  avatar.innerHTML = '<svg aria-hidden="true"><use href="#i-mark"/></svg>';
  const main = el("div", "bot-main");
  main.append(el("p", "bot-summary", summaryText(message)));

  const card = el("div", "file-card");
  card.dataset.id = message.id;
  const head = el("div", "file-head");
  const tag = el("span", "lang-tag", LANG_LABEL[lang] || lang);
  tag.dataset.lang = lang;
  const fileLabel = files.length > 1 ? `${files[0].path} +${files.length - 1}` : FILE_NAME[lang] || "code.txt";
  head.append(tag, el("span", "file-name", fileLabel), el("span", "file-meta", `${lines} ${lines === 1 ? "line" : "lines"}`));
  const verdict = verdictFor(message);
  if (verdict) head.append(verdictNode(verdict));

  const actions = el("div", "file-actions");
  const addAction = (label, iconName, handler, primary = false) => {
    const button = el("button", primary ? "btn btn-secondary" : "btn btn-ghost");
    button.type = "button";
    button.innerHTML = icon(iconName);
    button.append(el("span", "btn-label", label));
    button.setAttribute("aria-label", `${label} ${FILE_NAME[lang] || "code"}`);
    button.addEventListener("click", handler);
    actions.append(button);
    return button;
  };
  if (CAN_PREVIEW.has(lang)) addAction("Preview", "external", () => openWorkspace(message.id, "preview"), true);
  if (CAN_RUN.has(lang)) addAction("Run", "play", () => openWorkspace(message.id, "run", { autoRun: true }), true);
  addAction("Open", "panel", () => openWorkspace(message.id, "code"));
  head.append(actions);

  const body = el("div", "file-body");
  const pre = el("pre");
  pre.innerHTML = highlight(code.split("\n").slice(0, 12).join("\n"), lang);
  body.append(pre);
  if (lines > 12) {
    body.classList.add("is-clipped");
    const more = el("button", "btn btn-secondary file-more", `Show all ${lines} lines`);
    more.type = "button";
    more.addEventListener("click", (e) => {
      e.stopPropagation();
      openWorkspace(message.id, "code");
    });
    body.append(more);
  }
  body.addEventListener("click", () => openWorkspace(message.id, "code"));
  card.append(head, body);
  main.append(card);

  const bar = el("div", "msg-actions bot-actions");
  const copy = actionButton("Copy code", "copy", async () => flashCopied(copy, await copyText(message.content)));
  bar.append(copy, actionButton(files.length ? "Download project" : "Download file", "download", () => downloadFile(message)));
  if (message.prompt) {
    bar.append(actionButton("Try again", "refresh", () => regenerate(message)));
  }
  const meta = metaLine(message);
  if (meta) bar.append(el("span", "msg-meta", meta));
  main.append(bar);
  li.append(avatar, main);
  return li;
}

const WORK_STEPS = ["Reading your request", "Planning the structure", "Writing code", "Checking the result"];

function workingMessage() {
  const li = el("li", "msg msg-bot is-working");
  li.setAttribute("aria-label", "Coda is writing");
  const avatar = el("div", "bot-avatar");
  avatar.innerHTML = '<svg aria-hidden="true"><use href="#i-mark"/></svg>';
  const box = el("div", "working");
  const label = el("span", "working-label", WORK_STEPS[0]);
  const clock = el("time", "", "0s");
  box.append(label, clock);
  const skeleton = el("div", "skeleton");
  skeleton.setAttribute("aria-hidden", "true");
  skeleton.append(el("i"), el("i"), el("i"));
  const main = el("div", "bot-main");
  main.append(box, skeleton);
  li.append(avatar, main);
  const started = Date.now();
  li.timer = setInterval(() => {
    const seconds = Math.round((Date.now() - started) / 1000);
    clock.textContent = seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const step = seconds < 3 ? 0 : seconds < 8 ? 1 : seconds < 75 ? 2 : 3;
    label.textContent = seconds >= 120 ? "Still writing · bigger pages take a few minutes" : WORK_STEPS[step];
  }, 1000);
  return li;
}

function nearBottom() {
  const thread = $("thread");
  return thread.scrollHeight - thread.scrollTop - thread.clientHeight < 160;
}

function scrollToBottom(instant = false) {
  const thread = $("thread");
  thread.scrollTo({ top: thread.scrollHeight, behavior: instant || matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth" });
}

// Coda writes code; catch obvious small talk before it spends a daily message.
const SMALL_TALK = /^(hi|hello|hey|yo|sup|hiya|howdy|thanks|thank you|ok|okay|lol|who are you|what are you|what can you do|how are you|good (morning|afternoon|evening|night))\b[\s!?.]*$/i;

function looksLikeTask(text) {
  const t = text.trim();
  if (/[(){}[\]=:_#<>]|\b(def|return|class|import|function|const)\b/.test(t)) return true;
  if (SMALL_TALK.test(t)) return false;
  return t.split(/\s+/).length >= 3;
}

function showTaskTip() {
  const note = $("composer-note");
  note.textContent = "Coda is focused on code. Describe something to build, like “A landing page for a bakery”, or send again to send anyway.";
  note.dataset.tone = "warn";
}

async function sendMessage(text, language, { retry = false, fix = null } = {}) {
  text = text.trim();
  if (!text || state.sending) return;
  state.sending = true;
  updateComposer();

  setEmpty(false);
  const list = $("messages");
  // A fix request shows its file like an attachment; the server attaches the stored code.
  const shown = fix ? `${text}\n\n<attached_file name="${fix.fileName}">\n\n</attached_file>` : text;
  const userEl = retry ? null : userMessage(shown, language);
  const working = workingMessage();
  if (userEl) list.append(userEl);
  list.append(working);
  scrollToBottom();

  try {
    const body = { conversationId: state.activeId, message: text, language, retry, ...(fix ? { fix: { messageId: fix.messageId } } : {}) };
    const data = await api("/api/chat", { method: "POST", body });
    clearInterval(working.timer);
    const sent = retry ? null : data.messages[0];
    const reply = { ...data.messages.at(-1), prompt: sent?.content ?? text, language: sent?.meta?.language ?? language,
      fromAutoFix: Boolean(fix?.auto) };
    const follow = nearBottom();
    working.replaceWith(botMessage(reply));
    state.me.usage = data.usage;
    if (!state.activeId) {
      state.activeId = data.conversation.id;
      history.pushState(null, "", `/c/${data.conversation.id}`);
      document.title = `${data.conversation.title} — Opcoda`;
    }
    state.conversations = [data.conversation, ...state.conversations.filter((c) => c.id !== data.conversation.id)];
    renderConversationList();
    renderUsage();
    setStatus("online");
    const lang = messageLang(reply);
    if (state.prefs.autoRun && CAN_RUN.has(lang)) openWorkspace(reply.id, "run", { autoRun: true });
    else if (state.prefs.autoOpen && window.matchMedia(WIDE).matches) openWorkspace(reply.id, lang === "html" ? "preview" : "code");
    if (follow) scrollToBottom();
  } catch (err) {
    clearInterval(working.timer);
    working.remove();
    if (err.status === 401) return;
    const host = userEl || el("li", "msg msg-user");
    if (!userEl) list.append(host);
    host.classList.add("is-failed");
    const row = el("div", "msg-error");
    row.setAttribute("role", "alert");
    row.append(el("span", "", err.message));
    if (["model_offline", "model_busy", "model_error", "network"].includes(err.code)) {
      const again = el("button", "btn btn-secondary btn-sm", "Retry");
      again.type = "button";
      again.addEventListener("click", () => {
        host.remove();
        sendMessage(text, language, { retry });
      });
      row.append(again);
    }
    host.append(row);
    if (err.code === "model_offline") setStatus("offline");
    if (err.code === "daily_limit" && err.extra.usage) {
      state.me.usage = err.extra.usage;
      renderUsage();
    }
  } finally {
    state.sending = false;
    updateComposer();
  }
}

function regenerate(message) {
  if (state.sending) return toast("Coda is still working on the last message.");
  // The latest answer is retried in place; an older one is asked again as a new message.
  const latest = [...state.messages.keys()].at(-1) === message.id;
  sendMessage(message.prompt, message.language || "auto", { retry: latest && Boolean(state.activeId) });
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

function downloadFile(message) {
  const lang = messageLang(message);
  const files = message.meta?.files || [];
  const url = URL.createObjectURL(files.length ? projectZip(files) : new Blob([message.content], { type: "text/plain;charset=utf-8" }));
  const link = el("a");
  link.href = url;
  link.download = files.length ? "opcoda-project.zip" : FILE_NAME[lang] || "code.txt";
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ---------------------------------------------------------------------------
// Skills
// ---------------------------------------------------------------------------

async function loadSkills() {
  if (state.skills.loading) return state.skills.loading;
  state.skills.loading = (async () => {
    try {
      const data = await api("/api/skills");
      state.skills = { ...state.skills, catalog: data.skills || [], online: data.online, applies: data.applies };
    } catch {
      state.skills = { ...state.skills, online: false };
    } finally {
      state.skills.loading = null;
    }
    renderSkillCounts();
    if (!$("skills-pop").hidden) renderSkillsQuick();
    if ($("settings").open) renderSkillsPane();
  })();
  return state.skills.loading;
}

function skillOn(skill) {
  const saved = state.me?.settings?.skills || {};
  return Object.hasOwn(saved, skill.id) ? saved[skill.id] : skill.default;
}

// Counts cover the coding-style skills; design guides only apply when a request is related.
function activeSkills() {
  return state.skills.catalog.filter((s) => s.kind === "builtin" && skillOn(s));
}

function renderSkillCounts() {
  const count = state.skills.catalog.length ? String(activeSkills().length) : "";
  $("skills-count").textContent = count;
  $("skills-trigger-count").textContent = count;
  $("skills-trigger").setAttribute("aria-label", count ? `Skills, ${count} on` : "Skills");
}

async function setSkill(id, value) {
  const before = state.me.settings.skills || {};
  const skill = state.skills.catalog.find((s) => s.id === id);
  // Store only differences from the default, so new defaults reach everyone.
  const patch = { [id]: skill && value === skill.default ? null : value };
  state.me.settings = { ...state.me.settings, skills: { ...before, [id]: value } };
  renderSkillCounts();
  try {
    const { user } = await api("/api/me", { method: "PATCH", body: { settings: { skills: patch } } });
    state.me = { ...state.me, settings: user.settings };
  } catch (err) {
    state.me.settings = { ...state.me.settings, skills: before };
    toast(err.message);
  }
  renderSkillCounts();
  if ($("settings").open) renderSkillsPane();
  if (!$("skills-pop").hidden) renderSkillsQuick();
}

function skillSwitch(skill, idPrefix) {
  const input = el("input");
  input.type = "checkbox";
  input.className = "switch";
  input.id = `${idPrefix}-${skill.id}`;
  input.checked = skillOn(skill);
  input.addEventListener("change", () => setSkill(skill.id, input.checked));
  return input;
}

const LANG_SHORT = { html: "HTML", css: "CSS", javascript: "JS", python: "Python" };

function renderSkillsQuick() {
  const holder = $("skills-quick");
  holder.replaceChildren();
  if (!state.skills.catalog.length) {
    holder.append(el("p", "hint", state.skills.loading ? "Loading skills…" : "Skills load when Coda is online."));
    if (!state.skills.loading) loadSkills();
    return;
  }
  // Show the skills that apply to the chosen language (all of them on Auto).
  const lang = selectedLanguage();
  const skills = state.skills.catalog.filter((s) => s.kind === "builtin" && (lang === "auto" || s.langs.includes(lang)));
  let group = null;
  for (const skill of skills) {
    if (skill.group && skill.group !== group) {
      group = skill.group;
      holder.append(el("span", "skill-quick-group", group));
    }
    const row = el("label", "skill-row");
    row.htmlFor = `quick-${skill.id}`;
    row.title = skill.description;
    row.append(el("span", "skill-row-name", skill.name), skillSwitch(skill, "quick"));
    holder.append(row);
  }
  $("skills-pop-label").textContent = lang === "auto" ? "Skills" : `Skills for ${LANG_LABEL[lang]}`;
}

function renderSkillsPane() {
  const holder = $("skills-list");
  const notice = $("skills-notice");
  holder.replaceChildren();
  const { catalog, online, applies } = state.skills;
  notice.hidden = online !== false && applies !== false;
  notice.textContent = online === false
    ? "Coda is offline, so the skill list can't load right now. Your saved choices are kept."
    : "The model that's running right now doesn't use skills. Your choices apply when it does.";
  const GROUP_NOTES = {
    Quality: "Make the code more reliable. Applied to every request in the languages shown.",
    Style: "How the code reads.",
    "Web design": "How pages look and behave.",
    Apps: "Extra behaviour for interactive pages and scripts.",
  };
  const builtinGroups = [...new Set(catalog.filter((s) => s.kind === "builtin").map((s) => s.group || "Coding style"))];
  const groups = [
    ...builtinGroups.map((g) => [(s) => s.kind === "builtin" && (s.group || "Coding style") === g, g, GROUP_NOTES[g] || ""]),
    [(s) => s.kind === "guide", "Design guides", "From the ai-skills folder. On means Coda may use the guide when your request is related."],
  ];
  for (const [match, title, desc] of groups) {
    const skills = catalog.filter(match);
    if (!skills.length) continue;
    const section = el("section", "skill-group");
    section.append(el("h4", "", title), el("p", "hint", desc));
    for (const skill of skills) {
      const row = el("label", "setting skill-setting");
      row.htmlFor = `pane-${skill.id}`;
      const text = el("span", "setting-text");
      const name = el("span", "setting-name", skill.name);
      for (const lang of skill.langs) {
        const chip = el("span", "lang-tag", LANG_SHORT[lang] || lang);
        chip.dataset.lang = lang;
        name.append(chip);
      }
      text.append(name);
      if (skill.description) text.append(el("span", "setting-desc", skill.description));
      row.append(text, skillSwitch(skill, "pane"));
      section.append(row);
    }
    holder.append(section);
  }
  if (!catalog.length && state.skills.loading) holder.append(el("p", "hint", "Loading skills…"));
  $("skills-reset").disabled = !Object.keys(state.me.settings.skills || {}).length;
}

async function resetSkills() {
  const saved = state.me.settings.skills || {};
  const patch = Object.fromEntries(Object.keys(saved).map((id) => [id, null]));
  try {
    const { user } = await api("/api/me", { method: "PATCH", body: { settings: { skills: patch } } });
    state.me = { ...state.me, settings: user.settings };
    toast("Skills reset to defaults.");
  } catch (err) {
    toast(err.message);
  }
  renderSkillCounts();
  renderSkillsPane();
}

// ---------------------------------------------------------------------------
// Code workspace
// ---------------------------------------------------------------------------

function openWorkspace(id, tab = "code", { autoRun = false } = {}) {
  const message = state.messages.get(id);
  if (!message) return;
  const lang = messageLang(message);
  const changed = state.artifactId !== id;
  state.artifactId = id;
  document.querySelectorAll(".file-card.is-active").forEach((c) => c.classList.remove("is-active"));
  document.querySelector(`.file-card[data-id="${id}"]`)?.classList.add("is-active");

  const tag = $("ws-lang");
  tag.textContent = LANG_LABEL[lang] || lang;
  tag.dataset.lang = lang;
  $("ws-file").textContent = FILE_NAME[lang] || "code.txt";
  const verdict = verdictFor(message);
  const status = $("ws-status");
  status.textContent = verdict ? verdict.text : "";
  status.dataset.state = verdict ? verdict.state : "";

  $("ws-tab-preview").hidden = !CAN_PREVIEW.has(lang);
  $("ws-tab-run").hidden = !CAN_RUN.has(lang);
  if ((tab === "preview" && !CAN_PREVIEW.has(lang)) || (tab === "run" && !CAN_RUN.has(lang))) tab = "code";

  if (changed) {
    state.selectedFile = null;
    renderProjectFiles(message);
    renderChecks(message);
    $("preview-frame").replaceChildren();
    delete $("preview-frame").dataset.id;
    resetRunOutput();
  }
  renderCodeView(message);

  $("workspace").hidden = false;
  $("app").dataset.workspace = "open";
  $("toggle-workspace").hidden = false;
  $("toggle-workspace").setAttribute("aria-expanded", "true");
  selectTab(tab);
  if (autoRun) runActive();
}

function closeWorkspace() {
  if (!$("workspace")) return;
  stopRun("Stopped.");
  $("workspace").hidden = true;
  delete $("app").dataset.workspace;
  $("toggle-workspace").setAttribute("aria-expanded", "false");
  $("toggle-workspace").hidden = !state.artifactId || !state.messages.has(state.artifactId);
  document.querySelectorAll(".file-card.is-active").forEach((c) => c.classList.remove("is-active"));
}

function selectTab(tab) {
  for (const button of document.querySelectorAll(".ws-tabs [role=tab]")) {
    const selected = button.dataset.tab === tab;
    button.setAttribute("aria-selected", String(selected));
    button.tabIndex = selected ? 0 : -1;
  }
  $("ws-code").hidden = tab !== "code";
  $("ws-preview").hidden = tab !== "preview";
  $("ws-run").hidden = tab !== "run";
  if (tab === "preview") loadPreview();
}

function renderCodeView(message) {
  const file = (message.meta?.files || []).find(file => file.path === state.selectedFile) || message.meta?.files?.[0];
  const lang = file?.lang || messageLang(message);
  const code = (file?.content ?? message.content).replace(/\n+$/, "");
  $("ws-file").textContent = file?.path || FILE_NAME[lang] || "code.txt";
  $("ws-lang").textContent = LANG_LABEL[lang] || lang;
  $("ws-lang").dataset.lang = lang;
  const view = $("ws-code-view");
  const gutter = el("pre", "code-gutter");
  gutter.setAttribute("aria-hidden", "true");
  gutter.textContent = Array.from({ length: lineCount(code) }, (_, i) => i + 1).join("\n");
  const lines = el("pre", "code-lines");
  lines.innerHTML = highlight(code, lang);
  lines.tabIndex = 0;
  lines.setAttribute("aria-label", `${FILE_NAME[lang] || "Code"}, ${lineCount(code)} lines`);
  view.replaceChildren(gutter, lines);
}

function renderProjectFiles(message) {
  const files = message.meta?.files || [];
  const holder = $("project-files");
  holder.hidden = !files.length;
  holder.replaceChildren();
  for (const file of files) {
    const button = el("button", "project-file", file.path);
    button.type = "button";
    button.setAttribute("aria-pressed", String(file.path === (state.selectedFile || files[0].path)));
    button.addEventListener("click", () => {
      state.selectedFile = file.path;
      renderProjectFiles(message);
      renderCodeView(message);
      selectTab("code");
    });
    holder.append(button);
  }
  $("ws-download").setAttribute("aria-label", files.length ? "Download project ZIP" : "Download file");
}

function renderChecks(message) {
  const meta = message.meta || {};
  const checks = meta.checks || [];
  const details = $("ws-checks");
  details.hidden = !checks.length && meta.finished !== false;
  const list = $("ws-checks-list");
  list.replaceChildren();
  const failed = checks.filter((c) => !c.ok).length + (meta.finished === false ? 1 : 0);
  const summary = $("ws-checks-summary");
  summary.innerHTML = icon(failed ? "alert" : "check");
  summary.className = failed ? "check-bad" : "check-ok";
  summary.append(failed ? `${failed} ${failed === 1 ? "check needs" : "checks need"} attention` : `All ${checks.length} checks passed`);
  if (meta.finished === false) {
    const li = el("li");
    li.innerHTML = icon("alert");
    li.firstChild.classList.add("check-bad");
    const text = el("div", "", "Finished writing");
    text.append(el("small", "", "Stopped at the length limit. Choose a higher response effort in Settings → Coda."));
    li.append(text);
    list.append(li);
  }
  for (const check of checks) {
    const li = el("li");
    li.innerHTML = icon(check.ok ? "check" : "alert");
    li.firstChild.classList.add(check.ok ? "check-ok" : "check-bad");
    const text = el("div", "", check.name);
    if (check.detail) text.append(el("small", "", check.detail));
    li.append(text);
    list.append(li);
  }
  details.open = failed > 0;
}

// ---- "Ask Coda to fix": real errors from the browser sandboxes go back to Coda ----

function fixBar(barId, error) {
  const bar = $(barId);
  bar.replaceChildren();
  bar.hidden = !error;
  if (!error) return;
  bar.innerHTML = icon("alert");
  const text = el("span", "", error);
  text.title = error;
  const button = el("button", "btn btn-secondary btn-sm");
  button.type = "button";
  button.innerHTML = icon("refresh");
  button.append("Ask Coda to fix");
  const id = state.artifactId;
  button.addEventListener("click", () => askFix(id, error));
  bar.append(text, button);
  // Optional: one automatic attempt for the newest answer, never for an answer that was itself an automatic fix.
  const message = state.messages.get(id);
  const newest = [...state.messages.keys()].at(-1) === id;
  if (state.prefs.autoFix && newest && message && !message.fromAutoFix && !state.autoFixed.has(id) && !state.sending) {
    state.autoFixed.add(id);
    toast("Found an error. Asking Coda to fix it…");
    askFix(id, error, { auto: true });
  }
}

function askFix(id, error, { auto = false } = {}) {
  const message = state.messages.get(id);
  if (!message) return;
  if (state.sending) return toast("Coda is still working on the last message.");
  const lang = messageLang(message);
  if (!window.matchMedia(WIDE).matches) closeWorkspace();
  const what = lang === "html" ? "page" : `${LANG_LABEL[lang] || ""} code`;
  sendMessage(`Fix this ${what}. When I ran it, it failed with this error:\n${error.slice(-600)}\nKeep everything else working.`, lang,
    { fix: { messageId: id, fileName: FILE_NAME[lang] || "code.txt", auto } });
}

window.addEventListener("message", (event) => {
  const frame = $("preview-frame").querySelector("iframe");
  const msg = event.data || {};
  if (!frame || event.source !== frame.contentWindow || msg.source !== "coda-preview" || msg.type !== "error") return;
  if (!$("preview-fix").hidden) return; // keep the first error; later ones usually follow from it
  fixBar("preview-fix", `${msg.message}${msg.line ? ` (line ${msg.line})` : ""}`);
});

function loadPreview() {
  const id = state.artifactId;
  const holder = $("preview-frame");
  if (!id || holder.dataset.id === id && holder.firstChild) return;
  fixBar("preview-fix", "");
  const frame = el("iframe");
  frame.setAttribute("sandbox", "allow-scripts allow-forms allow-modals");
  frame.title = "Preview of the generated page";
  frame.src = `/api/messages/${id}/preview`;
  holder.dataset.id = id;
  holder.replaceChildren(frame);
  $("preview-open").href = `/api/messages/${id}/preview`;
}

// ---- Run (Python via Pyodide / JavaScript), isolated in /sandbox/run.html ----

const runner = { frame: null, ready: null, resolveReady: null, running: false, timer: null };

function ensureRunner() {
  if (runner.frame) return runner.ready;
  runner.ready = new Promise((resolve) => (runner.resolveReady = resolve));
  const frame = el("iframe");
  frame.setAttribute("sandbox", "allow-scripts");
  frame.title = "Code runner";
  frame.hidden = true;
  frame.src = "/sandbox/run.html";
  document.body.append(frame);
  runner.frame = frame;
  return runner.ready;
}

function resetRunOutput() {
  fixBar("run-fix", "");
  $("run-output").replaceChildren();
  $("run-status").textContent = "Runs in your browser in a sandbox, not on any server.";
  setRunButton(false);
}

function appendOutput(text, kind = "stdout") {
  const out = $("run-output");
  out.append(kind === "stdout" ? document.createTextNode(text) : el("span", kind, text));
  out.scrollTop = out.scrollHeight;
}

function setRunButton(running) {
  const button = $("run-button");
  button.innerHTML = icon(running ? "stop" : "play");
  button.append(running ? "Stop" : "Run");
  runner.running = running;
}

async function runActive() {
  const message = state.messages.get(state.artifactId);
  if (!message) return;
  const lang = messageLang(message);
  if (!CAN_RUN.has(lang)) return;
  if (runner.running) stopRun("Stopped.");
  selectTab("run");
  fixBar("run-fix", "");
  $("run-output").replaceChildren();
  appendOutput(lang === "python" ? "$ python main.py\n" : "$ node script.js\n", "sys");
  $("run-status").textContent = "Starting…";
  setRunButton(true);
  const started = await Promise.race([ensureRunner().then(() => true), new Promise((r) => setTimeout(() => r(false), 10_000))]);
  if (!started) {
    runner.frame?.remove();
    runner.frame = null;
    stopRunnerUi("The code runner couldn't start. A browser extension may be blocking it.");
    return;
  }
  if (!runner.running) return;
  runner.lang = lang;
  runner.frame.contentWindow.postMessage({ type: "run", lang, code: message.content }, "*");
  armTimeout(lang === "javascript" ? 8 : 0);
}

function armTimeout(seconds) {
  clearTimeout(runner.timer);
  if (seconds > 0) {
    runner.timer = setTimeout(() => {
      stopRun(`Stopped after ${seconds} seconds (possible infinite loop).`);
      fixBar("run-fix", `The program was still running after ${seconds} seconds, so it may loop forever or wait for input.`);
    }, seconds * 1000);
  }
}

function stopRun(reason) {
  clearTimeout(runner.timer);
  if (!runner.running) return;
  runner.frame?.contentWindow?.postMessage({ type: "stop" }, "*");
  stopRunnerUi(reason);
}

function stopRunnerUi(reason) {
  setRunButton(false);
  $("run-status").textContent = reason;
  appendOutput(`\n${reason}\n`, "sys");
}

window.addEventListener("message", (event) => {
  if (!runner.frame || event.source !== runner.frame.contentWindow) return;
  const msg = event.data || {};
  if (msg.source !== "coda-runner") return;
  if (msg.type === "ready") runner.resolveReady?.();
  else if (msg.type === "status") {
    $("run-status").textContent = `${msg.text}…`;
    if (msg.text === "Running") armTimeout(runner.lang === "python" ? 15 : 8);
  } else if (msg.type === "output" && runner.running) appendOutput(msg.text, msg.stream === "stderr" ? "stderr" : "stdout");
  else if (msg.type === "done" && runner.running) {
    clearTimeout(runner.timer);
    setRunButton(false);
    if (msg.ok) {
      $("run-status").textContent = "Finished without errors.";
      appendOutput("\nProcess finished.\n", "sys");
    } else {
      $("run-status").textContent = "Stopped with an error.";
      appendOutput(`\n${msg.error}\n`, "stderr");
      fixBar("run-fix", String(msg.error).trim().split("\n").slice(-4).join("\n"));
    }
  }
});

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function selectPane(pane) {
  for (const tab of document.querySelectorAll(".settings-nav [role=tab]")) {
    const selected = tab.dataset.pane === pane;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  }
  for (const section of document.querySelectorAll(".settings-pane")) section.hidden = section.id !== `pane-${pane}`;
  if (pane === "skills") {
    renderSkillsPane();
    if (!state.skills.catalog.length) loadSkills();
  }
}

function openSettings(pane = "general") {
  closePopups();
  if (isMobile()) setDrawer(false);
  const user = state.me;
  renderAvatar($("settings-avatar"), user);
  $("avatar-remove").hidden = !user.avatarVersion;
  $("s-display").value = user.displayName;
  const joined = new Date(user.createdAt * 1000).toLocaleDateString(undefined, { month: "long", year: "numeric" });
  $("s-username").textContent = `Signed in as @${user.username} · joined ${joined}`;
  showError($("profile-error"), "");
  showError($("password-error"), "");
  $("password-form").reset();
  for (const radio of document.querySelectorAll('input[name="theme"]')) radio.checked = radio.value === user.settings.theme;
  syncUsageModeControls();
  $("s-temperature").value = user.settings.temperature;
  $("temperature-out").textContent = Number(user.settings.temperature).toFixed(2);
  $("pref-enter").checked = state.prefs.enterToSend;
  $("pref-autopen").checked = state.prefs.autoOpen;
  $("pref-autorun").checked = state.prefs.autoRun;
  $("pref-wrap").checked = state.prefs.wrap;
  $("pref-autofix").checked = state.prefs.autoFix;
  selectPane(pane);
  if (!$("settings").open) $("settings").showModal();
  document.querySelector(`.settings-nav [data-pane="${pane}"]`).focus();
}

async function saveSettings(patch, { quiet = false } = {}) {
  try {
    const { user } = await api("/api/me", { method: "PATCH", body: { settings: patch } });
    state.me = { ...state.me, settings: user.settings };
    syncUsageModeControls();
    if ($("context").open) renderContext();
    if (!quiet) toast("Saved.");
  } catch (err) {
    toast(err.message);
  }
}

async function saveProfile(event) {
  event.preventDefault();
  const button = event.submitter;
  setBusy(button, true);
  showError($("profile-error"), "");
  try {
    const { user } = await api("/api/me", { method: "PATCH", body: { displayName: $("s-display").value } });
    state.me = { ...state.me, displayName: user.displayName };
    $("s-display").value = user.displayName;
    renderAccount();
    renderGreeting();
    renderAvatar($("settings-avatar"), state.me);
    toast("Profile saved.");
  } catch (err) {
    showError($("profile-error"), err.message);
  } finally {
    setBusy(button, false);
  }
}

async function squareImage(file) {
  if (file.size > 20 * 1024 * 1024) throw new Error("That image is too large. Choose one under 20 MB.");
  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    throw new Error("That file type isn't supported. Use PNG, JPEG or WebP.");
  }
  const side = Math.min(bitmap.width, bitmap.height);
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 256;
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingQuality = "high";
  ctx.drawImage(bitmap, (bitmap.width - side) / 2, (bitmap.height - side) / 2, side, side, 0, 0, 256, 256);
  bitmap.close?.();
  for (const [type, quality] of [["image/webp", 0.86], ["image/jpeg", 0.88], ["image/jpeg", 0.7]]) {
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, type, quality));
    if (blob && blob.type === type && blob.size < 300 * 1024) return blob;
  }
  throw new Error("Couldn't process that image.");
}

async function uploadAvatar(event) {
  const file = event.target.files?.[0];
  event.target.value = "";
  if (!file) return;
  const label = $("avatar-upload-label");
  label.textContent = "Uploading…";
  try {
    const blob = await squareImage(file);
    const { avatarVersion } = await api("/api/me/avatar", { method: "PUT", blob });
    state.me.avatarVersion = avatarVersion;
    renderAccount();
    renderAvatar($("settings-avatar"), state.me);
    $("avatar-remove").hidden = false;
    toast("Profile picture updated.");
  } catch (err) {
    toast(err.message);
  } finally {
    label.textContent = "Upload photo";
  }
}

async function removeAvatar() {
  try {
    await api("/api/me/avatar", { method: "DELETE" });
    state.me.avatarVersion = null;
    renderAccount();
    renderAvatar($("settings-avatar"), state.me);
    $("avatar-remove").hidden = true;
    toast("Profile picture removed.");
  } catch (err) {
    toast(err.message);
  }
}

async function changePassword(event) {
  event.preventDefault();
  const current = $("s-current").value;
  const next = $("s-new").value;
  if (!current) return showError($("password-error"), "Enter your current password.");
  if (next.length < 8) return showError($("password-error"), "Your new password needs at least 8 characters.");
  const button = event.submitter;
  setBusy(button, true);
  showError($("password-error"), "");
  try {
    await api("/api/me/password", { method: "POST", body: { currentPassword: current, newPassword: next } });
    $("password-form").reset();
    toast("Password changed. Other devices were signed out.");
  } catch (err) {
    showError($("password-error"), err.message);
  } finally {
    setBusy(button, false);
  }
}

async function revokeSessions() {
  try {
    const { revoked } = await api("/api/me/sessions/revoke-others", { method: "POST", body: {} });
    toast(revoked ? `Signed out of ${revoked} other ${revoked === 1 ? "device" : "devices"}.` : "No other devices were signed in.");
  } catch (err) {
    toast(err.message);
  }
}

async function deleteAccount() {
  await confirmAction({
    text: "This permanently deletes your account, every chat, and your profile picture. Enter your password to confirm.",
    okLabel: "Delete account",
    password: true,
    run: async (password) => {
      await api("/api/me", { method: "DELETE", body: { password } });
      $("settings").close();
      history.replaceState(null, "", "/");
      showAuth();
      toast("Your account was deleted.");
    },
  });
}

async function signOut() {
  closePopups();
  try {
    await api("/api/auth/logout", { method: "POST", body: {} });
  } catch {
    // the cookie is cleared server-side when possible; continue either way
  }
  history.replaceState(null, "", "/");
  $("messages").replaceChildren();
  setAuthMode("login");
  showAuth();
}

// ---- confirm dialog ----

function confirmAction({ text, okLabel, password = false, run }) {
  const dialog = $("confirm");
  $("confirm-title").textContent = okLabel;
  $("confirm-text").textContent = text;
  $("confirm-ok").textContent = okLabel;
  $("confirm-password-field").hidden = !password;
  $("confirm-password").value = "";
  showError($("confirm-error"), "");
  return new Promise((resolve) => {
    const form = $("confirm-form");
    const onSubmit = async (event) => {
      event.preventDefault();
      const value = $("confirm-password").value;
      if (password && !value) return showError($("confirm-error"), "Enter your password.");
      setBusy($("confirm-ok"), true);
      try {
        await run(value);
        dialog.close();
      } catch (err) {
        showError($("confirm-error"), err.message);
      } finally {
        setBusy($("confirm-ok"), false);
      }
    };
    const cleanup = () => {
      form.removeEventListener("submit", onSubmit);
      resolve();
    };
    form.addEventListener("submit", onSubmit);
    dialog.addEventListener("close", cleanup, { once: true });
    dialog.showModal();
    (password ? $("confirm-password") : $("confirm-cancel")).focus();
  });
}

// ---------------------------------------------------------------------------
// Wiring
// ---------------------------------------------------------------------------

function submitComposer() {
  const prompt = $("prompt");
  if ($("send").disabled) return;
  const visibleText = prompt.value;
  if (!state.attachment && !looksLikeTask(visibleText) && state.warnedText !== visibleText.trim()) {
    state.warnedText = visibleText.trim();
    showTaskTip();
    return;
  }
  if (state.warnedText !== null) {
    state.warnedText = null;
    renderUsage();
  }
  const text = composedMessage(visibleText);
  prompt.value = "";
  clearAttachment();
  autosize();
  closePopups();
  sendMessage(text, selectedLanguage());
}

function wireDialog(id) {
  const dialog = $(id);
  dialog.querySelector("[data-close]")?.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) dialog.close();
  });
}

function wire() {
  // auth
  $("tab-login").addEventListener("click", () => setAuthMode("login"));
  $("tab-signup").addEventListener("click", () => setAuthMode("signup"));
  $("auth-form").addEventListener("submit", submitAuth);
  for (const button of document.querySelectorAll("[data-reveal]")) {
    button.addEventListener("click", () => {
      const input = $(button.dataset.reveal);
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      button.textContent = show ? "Hide" : "Show";
      button.setAttribute("aria-pressed", String(show));
    });
  }

  // composer
  const prompt = $("prompt");
  prompt.addEventListener("input", () => {
    autosize();
    if (state.warnedText !== null && prompt.value.trim() !== state.warnedText) {
      state.warnedText = null;
      renderUsage();
    }
    updateComposer();
  });
  prompt.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" || e.isComposing) return;
    const mod = e.ctrlKey || e.metaKey;
    if (state.prefs.enterToSend ? !e.shiftKey : mod) {
      e.preventDefault();
      submitComposer();
    }
  });
  prompt.addEventListener("paste", (e) => {
    const file = [...(e.clipboardData?.files || [])][0];
    if (file && /^text\/|json|xml|javascript/.test(file.type)) {
      e.preventDefault();
      attachFile(file).catch(() => toast("Couldn't read that file."));
    }
  });
  $("composer").addEventListener("submit", (e) => {
    e.preventDefault();
    submitComposer();
  });
  const box = $("composer");
  box.addEventListener("dragover", (e) => {
    if ([...(e.dataTransfer?.types || [])].includes("Files")) {
      e.preventDefault();
      box.classList.add("is-dropping");
    }
  });
  box.addEventListener("dragleave", () => box.classList.remove("is-dropping"));
  box.addEventListener("drop", (e) => {
    box.classList.remove("is-dropping");
    const file = e.dataTransfer?.files?.[0];
    if (!file) return;
    e.preventDefault();
    attachFile(file).catch(() => toast("Couldn't read that file."));
  });
  for (const radio of document.querySelectorAll('input[name="lang"]')) {
    radio.addEventListener("change", () => {
      setLanguage(radio.value);
      $("tool-trigger").focus();
    });
  }
  for (const example of document.querySelectorAll(".example")) {
    example.addEventListener("click", () => {
      prompt.value = example.dataset.prompt;
      setLanguage(example.dataset.lang || "auto");
      autosize();
      updateComposer();
      prompt.focus();
      prompt.setSelectionRange(prompt.value.length, prompt.value.length);
    });
  }
  $("attach-file").addEventListener("click", () => $("file-input").click());
  $("file-input").addEventListener("change", (e) => attachFile(e.target.files?.[0]).catch(() => toast("Couldn't read that file.")));
  $("remove-attachment").addEventListener("click", clearAttachment);
  $("tool-trigger").addEventListener("click", () => {
    if (togglePopup("tool-menu")) document.querySelector('#tool-menu input:checked')?.focus();
  });
  $("skills-trigger").addEventListener("click", () => togglePopup("skills-pop"));

  // thread
  const thread = $("thread");
  thread.addEventListener("scroll", () => {
    $("jump-down").hidden = $("chat").dataset.empty === "true" || nearBottom();
  }, { passive: true });
  $("jump-down").addEventListener("click", () => scrollToBottom());

  // navigation
  const startNew = () => {
    newChat();
    prompt.focus();
  };
  $("new-chat").addEventListener("click", startNew);
  $("header-new-chat").addEventListener("click", startNew);
  $("home-link").addEventListener("click", (e) => {
    e.preventDefault();
    startNew();
  });
  $("open-sidebar").addEventListener("click", () => (isMobile() ? setDrawer(true) : toggleSidebar()));
  $("collapse-sidebar").addEventListener("click", toggleSidebar);
  $("close-sidebar").addEventListener("click", () => {
    setDrawer(false);
    $("open-sidebar").focus();
  });
  $("scrim").addEventListener("click", () => setDrawer(false));
  $("search-toggle").addEventListener("click", () => ($("search-box").hidden ? openSearch() : closeSearch()));
  $("chat-search").addEventListener("input", renderConversationList);
  $("chat-search").addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      closeSearch();
      $("search-toggle").focus();
    } else if (e.key === "Enter") {
      $("conversation-groups").querySelector("a")?.click();
    }
  });
  $("open-skills").addEventListener("click", () => openSettings("skills"));
  window.addEventListener("popstate", () => state.me && routeFromLocation());

  // workspace
  $("ws-close").addEventListener("click", closeWorkspace);
  $("toggle-workspace").addEventListener("click", () => {
    if (!$("workspace").hidden) closeWorkspace();
    else if (state.artifactId) openWorkspace(state.artifactId, "code");
  });
  for (const button of document.querySelectorAll(".ws-tabs [role=tab]")) {
    button.addEventListener("click", () => selectTab(button.dataset.tab));
    button.addEventListener("keydown", (e) => {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      const tabs = [...document.querySelectorAll(".ws-tabs [role=tab]")].filter((t) => !t.hidden);
      const next = tabs[(tabs.indexOf(button) + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
      next.focus();
      selectTab(next.dataset.tab);
    });
  }
  $("ws-copy").addEventListener("click", async () => {
    const message = state.messages.get(state.artifactId);
    const file = message?.meta?.files?.find(file => file.path === state.selectedFile) || message?.meta?.files?.[0];
    if (message) toast((await copyText(file?.content ?? message.content)) ? "Copied to clipboard." : "Copy failed.");
  });
  $("ws-download").addEventListener("click", () => {
    const message = state.messages.get(state.artifactId);
    if (message) downloadFile(message);
  });
  $("run-button").addEventListener("click", () => (runner.running ? stopRun("Stopped.") : runActive()));

  // menus
  $("account-btn").addEventListener("click", () => togglePopup("account-menu"));
  $("model-trigger").addEventListener("click", () => togglePopup("model-menu"));
  for (const button of document.querySelectorAll("[data-settings]")) {
    button.addEventListener("click", () => openSettings(button.dataset.settings));
  }
  $("open-shortcuts").addEventListener("click", () => {
    closePopups();
    $("shortcuts").showModal();
  });
  $("open-context").addEventListener("click", () => {
    renderContext();
    $("context").showModal();
  });
  $("sign-out").addEventListener("click", signOut);
  document.addEventListener("click", (e) => {
    for (const [id, trigger, scope] of POPUPS) {
      if (!$(id).hidden && !e.target.closest(scope)?.contains($(id))) setPopup(id, trigger, false);
    }
  });
  $("account-menu").addEventListener("keydown", (e) => {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    e.preventDefault();
    const items = [...$("account-menu").querySelectorAll("[role=menuitem]")];
    const next = items[(items.indexOf(document.activeElement) + (e.key === "ArrowDown" ? 1 : items.length - 1)) % items.length];
    next.focus();
  });

  // keyboard shortcuts
  document.addEventListener("keydown", (e) => {
    if (!state.me || $("app").hidden) return;
    const mod = e.ctrlKey || e.metaKey;
    const key = e.key.toLowerCase();
    const typing = e.target.closest?.("input, textarea, [contenteditable]");
    if (mod && e.shiftKey && key === "o") {
      e.preventDefault();
      newChat();
      prompt.focus();
    } else if (mod && !e.shiftKey && key === "k") {
      e.preventDefault();
      openSearch();
    } else if (mod && e.shiftKey && key === "s") {
      e.preventDefault();
      toggleSidebar();
    } else if (e.key === "/" && !typing && !document.querySelector("dialog[open]")) {
      e.preventDefault();
      prompt.focus();
    } else if (e.key === "Escape") {
      if (closePopups({ restoreFocus: true })) return;
      if ($("app").dataset.drawer === "open") {
        setDrawer(false);
        $("open-sidebar").focus();
      } else if (!$("workspace").hidden && !document.querySelector("dialog[open]")) {
        closeWorkspace();
      }
    }
  });

  // settings
  for (const id of ["context", "settings", "shortcuts"]) wireDialog(id);
  for (const tab of document.querySelectorAll(".settings-nav [role=tab]")) {
    tab.addEventListener("click", () => selectPane(tab.dataset.pane));
    tab.addEventListener("keydown", (e) => {
      const keys = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 };
      if (!(e.key in keys)) return;
      e.preventDefault();
      const tabs = [...document.querySelectorAll(".settings-nav [role=tab]")];
      const next = tabs[(tabs.indexOf(tab) + keys[e.key] + tabs.length) % tabs.length];
      next.focus();
      selectPane(next.dataset.pane);
    });
  }
  $("profile-form").addEventListener("submit", saveProfile);
  $("avatar-input").addEventListener("change", uploadAvatar);
  $("avatar-remove").addEventListener("click", removeAvatar);
  for (const radio of document.querySelectorAll('input[name="theme"]')) {
    radio.addEventListener("change", () => {
      applyTheme(radio.value);
      saveSettings({ theme: radio.value }, { quiet: true });
    });
  }
  for (const radio of document.querySelectorAll('input[name="usage-mode"]')) {
    radio.addEventListener("change", () => saveSettings({ usageMode: radio.value }, { quiet: true }));
  }
  for (const radio of document.querySelectorAll('input[name="header-usage-mode"]')) {
    radio.addEventListener("change", () => {
      saveSettings({ usageMode: radio.value }, { quiet: true });
      setPopup("model-menu", "model-trigger", false);
      toast(`Response effort: ${radio.value.replace(/^./, (c) => c.toUpperCase())}`);
    });
  }
  $("s-temperature").addEventListener("input", (e) => ($("temperature-out").textContent = Number(e.target.value).toFixed(2)));
  $("s-temperature").addEventListener("change", (e) => saveSettings({ temperature: Number(e.target.value) }, { quiet: true }));
  const prefs = { "pref-enter": "enterToSend", "pref-autopen": "autoOpen", "pref-autorun": "autoRun", "pref-wrap": "wrap", "pref-autofix": "autoFix" };
  for (const [id, key] of Object.entries(prefs)) $(id).addEventListener("change", (e) => setPref(key, e.target.checked));
  $("skills-reset").addEventListener("click", resetSkills);
  $("password-form").addEventListener("submit", changePassword);
  $("revoke-sessions").addEventListener("click", revokeSessions);
  $("delete-account").addEventListener("click", deleteAccount);
  $("confirm-cancel").addEventListener("click", () => $("confirm").close());
}

async function boot() {
  state.prefs = loadPrefs();
  wire();
  try {
    state.config = { ...state.config, ...(await api("/api/config")) };
  } catch {
    // keep defaults
  }
  try {
    const { user } = await api("/api/me");
    await enterApp(user);
  } catch (err) {
    showAuth(err.status === 401 ? "" : err.message);
  }
}

boot();
