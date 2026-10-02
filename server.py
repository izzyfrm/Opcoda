"""Coda model API (runs on your PC; opcoda.cc reaches it privately through a Cloudflare Tunnel).

    uvicorn server:app --host 127.0.0.1 --port 8000

Environment:
    CODA_BACKEND      ollama (default) or coda (from-scratch checkpoint)
    CODA_OLLAMA_MODEL local Ollama model (default: llama3.2:3b)
    CODA_CHECKPOINT   Coda checkpoint when CODA_BACKEND=coda
    CODA_MODEL_TOKEN  shared secret; when set, /api/generate requires
                      "Authorization: Bearer <token>". Always set it when tunnelled.
                      If unset, the token is read from .coda-model-token (gitignored).

Endpoints:
    GET  /health        model status (no secrets)
    POST /api/generate  {"prompt", "language"?, "temperature"?, "max_tokens"?, "drafts"?}
                        -> {"text", "lang", "finished", "syntax_ok", "checks", "drafts", ...}

How a reply is produced (Phase 4 checkpoints):
    1. The request becomes Coda's training format: <task>…</task><code lang="…">.
    2. Coda writes several drafts at once (one batched pass with a KV cache).
    3. Every draft is checked by opcoda.verify for its language. Nothing is executed:
       Python is parsed and scanned for undefined names, HTML/CSS are parsed, and
       JavaScript is only compiled by Node.
    4. The best draft wins: finished > passes every check > passes more checks > longer.
"""
import hmac
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from opcoda.verify import _HTMLChecker, check_css, check_html, check_js_many, check_python, normalize_lang
from opcoda.ui_skill import ui_guidance
from opcoda.markdown_skills import markdown_guidance
from opcoda.project import website_project, missing_assets

CANDIDATES = ["checkpoints/coda-v4-best.pt", "checkpoints/coda-coda-v4-best.pt", "checkpoints/coda-phase3-best.pt",
              "checkpoints/coda-smoke-step-500.pt"]
BACKEND = os.environ.get("CODA_BACKEND", "ollama").lower()
OLLAMA_MODEL = os.environ.get("CODA_OLLAMA_MODEL", "llama3.2:3b")
CHECKPOINT = os.environ.get("CODA_CHECKPOINT") or next((c for c in CANDIDATES if Path(c).exists()), CANDIDATES[-1])
TOKEN_FILE = Path(".coda-model-token")
MODEL_TOKEN = os.environ.get("CODA_MODEL_TOKEN") or (TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else "")
if not MODEL_TOKEN:
    print("warning: no model token set; /api/generate is open to anyone who can reach this server")
MAX_PROMPT_CHARS = 6000
CONTEXT_TOKENS = 8192
LANGUAGES = ("html", "css", "javascript", "python")
CODE_START = re.compile(r"^\s*(def |class |import |from |@)")
LANG_TAG = re.compile(r'^<code lang="([a-z]+)">\n')

app = FastAPI(title="Coda model API", docs_url=None, redoc_url=None)
if BACKEND not in ("coda", "ollama"):
    raise RuntimeError(f"unknown CODA_BACKEND: {BACKEND}")
if BACKEND == "coda":
    import torch
    from opcoda.config import CodaConfig
    from opcoda.model import Coda
    from opcoda.tokenizer import tokenizer_from_checkpoint

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading Coda from {CHECKPOINT} on {device}...")
    payload = torch.load(CHECKPOINT, map_location=device, weights_only=False)
    config = CodaConfig(**payload["config"])
    model = Coda(config).to(device)
    model.load_state_dict(payload["model"])
    model.eval()
    tokenizer = tokenizer_from_checkpoint(payload)
    PHASE4 = payload.get("format") == "coda-phase4"
    print(f"Coda loaded: step {payload.get('step', '?')}, {model.parameter_count():,} parameters, "
          f"{'BPE, multi-language' if PHASE4 else 'byte-level, Python only'}.")
else:
    print(f"Using local Ollama model {OLLAMA_MODEL}.")
# One generation at a time: drafts are already batched, and parallel requests would
# just fight over the same CPU cores.
generation_lock = threading.Lock()


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=MAX_PROMPT_CHARS)
    language: str = "auto"
    mode: str = "auto"  # kept for older clients
    temperature: float = 0.6
    max_tokens: int = 900
    drafts: int = 4


def check_token(authorization: str | None) -> None:
    if not MODEL_TOKEN:
        return
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    if not hmac.compare_digest(supplied.encode(), MODEL_TOKEN.encode()):
        raise HTTPException(status_code=401, detail="invalid model token")


def build_prompt(text: str, language: str) -> tuple[str, str | None, str]:
    """Returns (prompt, forced language or None, code prefix the model is continuing)."""
    text = text.replace("\r\n", "\n").strip()
    lang = normalize_lang(language)
    lang = lang if lang in LANGUAGES else None
    prefix = ""
    if CODE_START.match(text) and lang in (None, "python"):
        # A pasted def/class line: ask Coda to finish it.
        first = text.splitlines()[0].strip()
        prefix = text + "\n"
        return f"<task>\nComplete this Python code: {first}\n</task>\n<code lang=\"python\">\n{prefix}", "python", prefix
    prompt = f"<task>\n{text}\n</task>\n"
    if lang:
        prompt += f'<code lang="{lang}">\n'
    return prompt, lang, prefix


def split_draft(raw: str, forced_lang: str | None, prefix: str) -> tuple[str | None, str, bool]:
    """Turn a decoded draft into (language, code, finished)."""
    lang = forced_lang
    if lang is None:
        m = LANG_TAG.match(raw)
        if not m or m.group(1) not in LANGUAGES:
            return None, raw, False
        lang, raw = m.group(1), raw[m.end():]
    finished = False
    for marker in ("</code>", "<task>"):
        if marker in raw:
            raw, finished = raw[: raw.index(marker)], True
    return lang, (prefix + raw).rstrip() + "\n", finished


def verify_drafts(drafts: list[dict]) -> None:
    """Attach a verification report to every draft (JavaScript checked in one Node call)."""
    scripts = []
    for d in drafts:
        if d["lang"] == "javascript":
            scripts.append(d["code"])
        elif d["lang"] == "html":
            page = _HTMLChecker()
            try:
                page.feed(d["code"])
            except Exception:  # noqa: BLE001 - malformed drafts are scored as failures below
                pass
            scripts.extend(page.scripts)
    errors = dict(zip(scripts, check_js_many(scripts))) if scripts else {}
    cached = lambda sources: [errors.get(s) for s in sources]  # noqa: E731
    for d in drafts:
        lang, code = d["lang"], d["code"]
        if lang == "python":
            report = check_python(code)
        elif lang == "html":
            report = check_html(code, js_checker=cached)
        elif lang == "css":
            report = check_css(code)
        elif lang == "javascript":
            from opcoda.verify import Report
            report = Report("javascript")
            report.add("Valid syntax", errors.get(code) is None, errors.get(code) or "")
            report.stats = {"lines": code.rstrip("\n").count("\n") + 1}
        else:
            from opcoda.verify import Report
            report = Report("unknown")
            report.add("Wrote code", False, "Coda did not start a code block")
        d["report"] = report


def ollama_language(text: str, requested: str) -> str:
    lang = normalize_lang(requested)
    if lang in LANGUAGES:
        return lang
    if re.search(r"\b(html|web ?page|website|landing page|portfolio|dashboard)\b", text, re.I):
        return "html"
    if re.search(r"\b(css|stylesheet)\b", text, re.I):
        return "css"
    if re.search(r"\b(javascript|typescript|\bjs\b)\b", text, re.I):
        return "javascript"
    return "python"


def generate_ollama(req: GenerateRequest) -> dict:
    lang = ollama_language(req.prompt, req.language)
    guidance = ui_guidance(req.prompt, lang)
    local_guidance = markdown_guidance(req.prompt, lang)
    system_prompt = f"You are a careful {lang} coding assistant. Return only complete {lang} code, without Markdown fences or explanation. Use the user's exact requested names and behavior. Keep the solution concise."
    website = lang == "html"
    output_budget = min(max(req.max_tokens * 2, 128), 2400)
    if website:
        output_budget = 2400 if req.max_tokens <= 256 else 3200 if req.max_tokens <= 450 else 4000 if req.max_tokens <= 650 else 4800
        system_prompt = (
            "You are a website designer and frontend engineer. Return one COMPLETE standalone HTML document, "
            "with all CSS inside <style> and any necessary JS inside <script>. No Markdown or explanation. "
            "The application extracts these into index.html, css/styles.css and js/script.js automatically. "
            "When JavaScript is requested, include useful working JavaScript, such as mobile navigation or reveal animations with reduced-motion support. "
            "Design the finished website, not a bare text outline. Preserve the user's names, URLs and requirements exactly. "
            "Use a coherent visual composition: navigation, spacious hero with clear headline and useful CTA, "
            "well-structured content sections and a compact footer. For portfolios use the provided name, role and projects; "
            "make each supplied project URL a real clickable link. Do not invent achievements, testimonials or contact details. "
            "Include substantial CSS: color and spacing variables, system font stack, distinct heading sizes, "
            "a centered max-width container, grid/flex layouts, responsive mobile breakpoint, hover and visible focus states. "
            "Default to restrained neutral colors, strong contrast and one accent; respect requested themes. "
            "Avoid neon, gratuitous gradients, giant rounded cards and generic marketing filler. "
            "No external fonts, images, stylesheets or libraries: the preview has no network. "
            "Use typography, spacing and CSS shapes for visual interest. Navigation must target real sections; "
            "avoid nonfunctional buttons. Keep CSS compact to leave room for the complete body and closing tags. "
            "Use this reliable layout foundation and extend it: "
            "*{box-sizing:border-box}body{margin:0;font:400 16px/1.6 system-ui;background:#101113;color:#eee}" 
            "a{color:inherit}.container{width:min(1100px,calc(100% - 40px));margin:auto}" 
            ".hero{padding:80px 0}.hero h1{font-size:clamp(32px,6vw,64px);line-height:1.1}" 
            ".projects{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}" 
            "@media(max-width:640px){.projects{grid-template-columns:1fr}.hero{padding:48px 0}}. "
            "Never put color or bold font-weight on the universal * selector: children must inherit section colors. "
            "Keep normal body text weight 400 and headings 600-700. Adapt foundation colors to the user's theme."
        )
    if guidance:
        system_prompt += "\nUse these local design recommendations where relevant; explicit user requirements take priority:\n" + guidance
    if local_guidance:
        system_prompt += "\nApply these project coding guides where relevant. User requirements take priority; examples are patterns, not facts to copy:\n" + local_guidance
    prompt = ("Complete this code and return the whole completed file:\n" if CODE_START.match(req.prompt)
              else "Write code for this request:\n") + req.prompt
    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "keep_alive": "5m",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": min(max(req.temperature, 0.0), 1.0),
                    "num_predict": output_budget, "num_ctx": CONTEXT_TOKENS},
    }
    request = urllib.request.Request("http://127.0.0.1:11434/api/chat",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=480) as response:
            data = json.load(response)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"local Ollama unavailable: {exc}") from exc
    raw = data.get("message", {}).get("content", "").strip()
    fenced = re.search(r"```(?:[a-zA-Z0-9_+-]+)?\s*\n(.*?)\n```", raw, re.S)
    code = (fenced.group(1) if fenced else raw).strip() + "\n"
    if website:
        # Some small models still return separate fenced assets. Keep them.
        for kind, asset in re.findall(r"```(css|javascript|js)\s*\n(.*?)\n```", raw, re.S | re.I):
            if kind.lower() == "css":
                code = re.sub(r'<link\b[^>]*rel=[\"\']stylesheet[\"\'][^>]*>', '', code, flags=re.I)
                code = code.replace('</head>', '<style>\n' + asset + '\n</style>\n</head>')
            elif not re.search(r'<script\b(?![^>]*src=)', code, re.I):
                code = re.sub(r'<script\b[^>]*src=[\"\'][^\"\']+[\"\'][^>]*>\s*</script>', '', code, flags=re.I)
                code = code.replace('</body>', '<script>\n' + asset + '\n</script>\n</body>')
        styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", code, re.I | re.S))
        if len(styles.strip()) < 250:
            # Repair the exact failure in the screenshot: HTML with no usable CSS.
            repair = {**body, "messages": [
                {"role": "system", "content": "Return only complete CSS, no Markdown. Style the given HTML using its exact selectors. Respect the requested theme. Include typography, spacing, grid/flex layout, visible focus, and a mobile media query. No external assets. Keep it under 650 tokens."},
                {"role": "user", "content": req.prompt[:1500] + "\nHTML:\n" + code[:8000]},
            ], "options": {**body["options"], "num_predict": 700}}
            try:
                repair_request = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(repair).encode(), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(repair_request, timeout=85) as response:
                    repaired = json.load(response)
                css = repaired.get("message", {}).get("content", "").strip()
                css = re.sub(r'^```css\s*|\s*```$', '', css, flags=re.I)
                if check_css(css).ok and repaired.get("done_reason") != "length":
                    code = re.sub(r'<link\b[^>]*rel=[\"\']stylesheet[\"\'][^>]*>', '', code, flags=re.I)
                    code = re.sub(r'</head\s*>', lambda m: '<style>\n' + css + '\n</style>\n' + m.group(0), code, count=1, flags=re.I)
                    data["eval_count"] = (data.get("eval_count") or 0) + (repaired.get("eval_count") or 0)
            except (OSError, ValueError):
                pass  # The checks below explicitly flag missing styling/assets.
    draft = {"lang": lang, "code": code}
    verify_drafts([draft])
    report = draft["report"]
    if website:
        styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", code, re.I | re.S))
        report.add("Embedded website styling", len(styles.strip()) >= 250,
                   "This page has little embedded styling; it may render as a plain text layout.")
        report.add("Responsive layout", bool(re.search(r"@media|auto-fit|auto-fill", styles, re.I)),
                   "No responsive CSS layout rule found. Check the page on a phone.")
        report.add("Complete document", "</html>" in code.lower() and "</body>" in code.lower(),
                   "The document is incomplete. Try a higher response effort or a smaller page.")
        missing = missing_assets(code)
        report.add("Referenced files exist", not missing,
                   "Missing project assets: " + ", ".join(missing[:6]))
    return {"text": code, "lang": lang, "finished": data.get("done_reason") != "length",
            "syntax_ok": report.ok, "checks": report.to_dict(),
            "drafts": {"total": 1, "passed": int(report.ok)},
            "tokens": data.get("eval_count"), "prompt_tokens": data.get("prompt_eval_count"),
            "context_tokens": CONTEXT_TOKENS, "model": OLLAMA_MODEL,
            "files": website_project(code) if website else []}


def generate_phase4(req: GenerateRequest) -> dict:
    prompt, forced_lang, prefix = build_prompt(req.prompt, req.language)
    ids = tokenizer.encode(prompt)
    if len(ids) > config.block_size - 64:
        raise HTTPException(status_code=413, detail="prompt is too long")
    n = min(max(req.drafts, 1), 6)
    samples = model.sample(ids, max_new_tokens=min(max(req.max_tokens, 32), 1000), token_bytes=tokenizer.token_bytes,
                           n=n, temperature=min(max(req.temperature, 0.05), 1.2), top_k=40, stop=["</code>", "<task>"])
    drafts = []
    for s in samples:
        lang, code, finished = split_draft(tokenizer.decode(s["ids"]), forced_lang, prefix)
        drafts.append({"lang": lang, "code": code, "finished": finished or s["finished"], "tokens": len(s["ids"])})
    verify_drafts(drafts)
    best = max(drafts, key=lambda d: (d["report"].ok, d["report"].passed, d["finished"], min(len(d["code"]), 4000)))
    return {
        "text": best["code"],
        "lang": best["lang"] or "text",
        "finished": best["finished"],
        "syntax_ok": best["report"].ok,
        "checks": best["report"].to_dict(),
        "drafts": {"total": len(drafts), "passed": sum(d["report"].ok and d["finished"] for d in drafts)},
        "tokens": best["tokens"],
    }


def generate_phase3(req: GenerateRequest) -> dict:
    """Byte-level Phase 3 checkpoints: one Python draft, as before."""
    text = req.prompt.replace("\r\n", "\n").strip()
    complete = bool(CODE_START.match(text))
    prompt = (text + "\n") if complete else f"<task>\n{text}\n</task>\n<code>\n"
    stops = ["</code>", "</task>", "<task>", "\n<code>"]
    ids = tokenizer.encode(prompt)
    out = model.generate(torch.tensor([ids], dtype=torch.long, device=device), max_new_tokens=min(max(req.max_tokens, 16), 256),
                         temperature=min(max(req.temperature, 0.05), 1.2), top_k=20, stop=[tokenizer.encode(s) for s in stops])[0].tolist()
    raw = tokenizer.decode(out[len(ids):])
    cut = min((raw.index(s) for s in stops if s in raw), default=None)
    code = ((prompt if complete else "") + (raw[:cut] if cut is not None else raw)).rstrip() + "\n"
    report = check_python(code)
    return {"text": code, "lang": "python", "finished": cut is not None, "syntax_ok": report.ok,
            "checks": report.to_dict(), "drafts": {"total": 1, "passed": int(report.ok and cut is not None)},
            "tokens": len(out) - len(ids)}


@app.get("/")
def root():
    return {"service": "coda-model-api", "website": "https://opcoda.cc", "health": "/health"}


@app.get("/health")
def health():
    if BACKEND == "ollama":
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
                available = {m["name"] for m in json.load(response).get("models", [])}
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=503, detail="local Ollama unavailable") from exc
        if OLLAMA_MODEL not in available:
            raise HTTPException(status_code=503, detail=f"model {OLLAMA_MODEL} is not installed")
        return {"ok": True, "model": OLLAMA_MODEL, "backend": "ollama", "step": None,
                "parameters": None, "languages": list(LANGUAGES), "context_tokens": CONTEXT_TOKENS,
                "project_files": True, "generator_version": 2}
    return {"ok": True, "model": "Coda", "step": payload.get("step"), "parameters": model.parameter_count(),
            "checkpoint": Path(CHECKPOINT).name, "languages": list(LANGUAGES) if PHASE4 else ["python"],
            "context_tokens": config.block_size}


@app.post("/api/generate")
def generate(req: GenerateRequest, authorization: str | None = Header(default=None)):
    check_token(authorization)
    if not generation_lock.acquire(timeout=60):
        raise HTTPException(status_code=503, detail="Coda is busy, try again in a moment")
    try:
        started = time.perf_counter()
        result = (generate_ollama(req) if BACKEND == "ollama" else
                  generate_phase4(req) if PHASE4 else generate_phase3(req))
        result["ms"] = round((time.perf_counter() - started) * 1000)
    finally:
        generation_lock.release()
    result.update({"model": OLLAMA_MODEL if BACKEND == "ollama" else "Coda",
                   "step": None if BACKEND == "ollama" else payload.get("step")})
    return result


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_PROMPT_CHARS)


@app.post("/api/chat")
def chat(req: ChatRequest, authorization: str | None = Header(default=None)):
    """Legacy endpoint: {"message"} clients get {"response"}."""
    result = generate(GenerateRequest(prompt=req.message), authorization)
    return {"response": result["text"], "model": result["model"]}
