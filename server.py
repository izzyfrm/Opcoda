"""Coda model API (runs on your PC; opcoda.cc reaches it privately through a Cloudflare Tunnel).

    uvicorn server:app --host 127.0.0.1 --port 8000

Environment:
    CODA_CHECKPOINT   checkpoint to serve (default: newest of coda-v4-best.pt, coda-phase3-best.pt)
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
import os
import re
import threading
import time
from pathlib import Path

import torch
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from opcoda.config import CodaConfig
from opcoda.model import Coda
from opcoda.tokenizer import tokenizer_from_checkpoint
from opcoda.verify import _HTMLChecker, check_css, check_html, check_js_many, check_python, normalize_lang

CANDIDATES = ["checkpoints/coda-v4-best.pt", "checkpoints/coda-coda-v4-best.pt", "checkpoints/coda-phase3-best.pt",
              "checkpoints/coda-smoke-step-500.pt"]
CHECKPOINT = os.environ.get("CODA_CHECKPOINT") or next((c for c in CANDIDATES if Path(c).exists()), CANDIDATES[-1])
TOKEN_FILE = Path(".coda-model-token")
MODEL_TOKEN = os.environ.get("CODA_MODEL_TOKEN") or (TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else "")
if not MODEL_TOKEN:
    print("warning: no model token set; /api/generate is open to anyone who can reach this server")
MAX_PROMPT_CHARS = 1000
LANGUAGES = ("html", "css", "javascript", "python")
CODE_START = re.compile(r"^\s*(def |class |import |from |@)")
LANG_TAG = re.compile(r'^<code lang="([a-z]+)">\n')

app = FastAPI(title="Coda model API", docs_url=None, redoc_url=None)
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading Coda from {CHECKPOINT} on {device}...")
payload = torch.load(CHECKPOINT, map_location=device)
config = CodaConfig(**payload["config"])
model = Coda(config).to(device)
model.load_state_dict(payload["model"])
model.eval()
tokenizer = tokenizer_from_checkpoint(payload)
PHASE4 = payload.get("format") == "coda-phase4"
# One generation at a time: drafts are already batched, and parallel requests would
# just fight over the same CPU cores.
generation_lock = threading.Lock()
print(f"Coda loaded: step {payload.get('step', '?')}, {model.parameter_count():,} parameters, "
      f"{'BPE, multi-language' if PHASE4 else 'byte-level, Python only'}.")


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
    best = max(drafts, key=lambda d: (d["finished"], d["report"].ok, d["report"].passed, min(len(d["code"]), 4000)))
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
        result = generate_phase4(req) if PHASE4 else generate_phase3(req)
        result["ms"] = round((time.perf_counter() - started) * 1000)
    finally:
        generation_lock.release()
    result.update({"model": "Coda", "step": payload.get("step")})
    return result


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_PROMPT_CHARS)


@app.post("/api/chat")
def chat(req: ChatRequest, authorization: str | None = Header(default=None)):
    """Legacy endpoint: {"message"} clients get {"response"}."""
    result = generate(GenerateRequest(prompt=req.message), authorization)
    return {"response": result["text"], "model": result["model"]}
