"""Code generation pipeline for the Ollama backend: plan -> write -> check -> repair -> review.

Effort (the website's Response effort setting, sent as max_tokens) picks the steps:

    light    write once
    medium   write, then up to 1 repair round if a check fails
    super    plan the requirements first, write, up to 2 repair rounds
    intense  plan, write, up to 2 repair rounds, then a review pass against the plan

Every round is checked with opcoda.verify + opcoda.quality (static only; nothing generated
is executed on this machine). A repair is kept only when it scores better than what we had,
so a round can never make the answer worse.
"""
from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass, field

from opcoda.project import missing_assets
from opcoda.quality import add_quality_checks
from opcoda.verify import Report, _HTMLChecker, check_css, check_html, check_js_many, check_python

OLLAMA = "http://127.0.0.1:11434/api/chat"
CONTEXT_TOKENS = 8192
LONG_CONTEXT_TOKENS = 16384
LANGS = ("html", "css", "javascript", "python")
FENCE = re.compile(r"```[ \t]*([A-Za-z0-9_+-]*)[ \t]*\n(.*?)(?:\n```|$)", re.S)

EFFORT = {  # max_tokens from the website -> pipeline settings
    "light": {"repairs": 0, "plan": False, "review": False},
    "medium": {"repairs": 1, "plan": False, "review": False},
    "super": {"repairs": 2, "plan": True, "review": False},
    "intense": {"repairs": 2, "plan": True, "review": True},
}


def effort_for(max_tokens: int) -> str:
    return "light" if max_tokens <= 300 else "medium" if max_tokens <= 500 else "super" if max_tokens <= 700 else "intense"


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

COMMON = (
    "Return ONLY the code for one complete file, with no Markdown fences and no explanation before or after it. "
    "Never leave placeholders, TODOs, '...' or 'rest of the code' comments: write every part. "
    "Use exactly the names, signatures, text and values the user gives. "
    "Before you finish, re-read the request and make sure every requirement is implemented and every edge case "
    "(empty input, zero, one item, duplicates, invalid input) behaves sensibly."
)

SYSTEM = {
    "python": (
        "You are a senior Python engineer. Write correct, idiomatic Python 3.11+ that runs as-is. "
        "Use only the standard library. Prefer clear names and small functions; avoid global state. "
        "Never call input() or read files: the code runs in a browser sandbox with no keyboard or disk. "
        "Do not use a mutable default argument. When the user gives a function signature, implement exactly that signature "
        "and return the result rather than printing it. "
        + COMMON
    ),
    "javascript": (
        "You are a senior JavaScript engineer. Write modern, correct ES2022 JavaScript that runs in a browser or Node without a build step. "
        "Use const/let, strict equality, and no external libraries. Never use prompt() or readline: the code runs in a sandbox with no keyboard. "
        "Functions return values instead of only logging them. "
        + COMMON
    ),
    "css": (
        "You are a senior CSS engineer. Write one complete, valid stylesheet. Start with custom properties on :root for colours, "
        "spacing and radius, then base styles, then components. Use flexbox/grid, relative units, a visible :focus-visible style, "
        "hover states, and at least one media query so it works from 360px phones to desktops. "
        "Style the class names the user mentions; otherwise use clear, conventional class names. No external fonts or images. "
        + COMMON
    ),
    "html": (
        "You are a website designer and frontend engineer. Return one COMPLETE standalone HTML document "
        "(<!DOCTYPE html>, <html lang>, <head> with charset, viewport and <title>, and <body>), with all CSS in one <style> "
        "and all JavaScript in one <script> at the end of <body>. The app splits these into index.html, css/styles.css and js/script.js. "
        "Design the finished site, not an outline: navigation that targets real sections, a clear hero, well-structured sections, "
        "and a compact footer. Use CSS custom properties, a system font stack, a centred max-width container, grid/flex layouts, "
        "a mobile breakpoint, hover and visible focus states. Default to restrained neutral colours with one accent; respect requested themes. "
        "Never put colour or bold weight on the * selector. Body text weight 400, headings 600-700. "
        "Every interactive control must work: each element your script looks up must exist with that exact id, and every function "
        "named in an event handler must be defined. Prefer addEventListener over inline onclick. Label every form field. "
        "Give images alt text. No external fonts, images, stylesheets or libraries: the preview has no network, so use CSS shapes, "
        "gradients and inline SVG for visuals. Do not invent testimonials, statistics or contact details the user didn't give. "
        "Keep CSS compact so the whole document, including closing tags, fits."
        + " " + COMMON
    ),
}

PLAN_PROMPT = (
    "Before writing any code, plan the {lang} solution for this request. No code.\n"
    "1. Requirements: every feature, input format, output format, edge case and on-screen element, as short bullets (at most 8). "
    "Quote any example formats from the request exactly.\n"
    "2. Examples: for functions, give 3 example calls with the exact expected result, worked out carefully by hand "
    "from the request (include one edge case). For pages, list the interactions a user will try and what each must do.\n\n"
    "Request:\n{request}"
)

REPAIR_PROMPT = (
    "Automatic checks found these problems in your code:\n{problems}\n\n"
    "Fix every problem while keeping everything that already works. Return the complete corrected file, only code."
)

CUTOFF_PROMPT = (
    "Your code was cut off before the end. Rewrite the complete file more compactly (shorter CSS, no comments, "
    "no repetition) so that all of it, including closing tags, fits. Only code."
)

REVIEW_PROMPT = (
    "Review your code against the request and this plan:\n{plan}\n\n"
    "Trace each example through your code line by line and compare with the expected result. "
    "If anything is missing, gives a different result, or breaks on an edge case, return the complete corrected file. "
    "If it is already correct and complete, return it unchanged. Only code."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_language(text: str, requested: str) -> str:
    if requested in LANGS:
        return requested
    if re.search(r"<attached_file name=\"[^\"]+\.py\"", text) or re.search(r"\b(python|pandas|django|flask|\.py)\b", text, re.I):
        return "python"
    if re.search(r"\b(html|web ?page|website|site|landing page|portfolio|dashboard|app|game|form|calculator|page)\b", text, re.I) \
            and not re.search(r"\b(function|class|script|algorithm|cli|command line)\b", text, re.I):
        return "html"
    if re.search(r"\b(css|stylesheet|style sheet)\b", text, re.I):
        return "css"
    if re.search(r"\b(javascript|typescript|node|\bjs\b)\b", text, re.I):
        return "javascript"
    return "python"


@dataclass
class Draft:
    code: str
    finished: bool
    report: Report = field(default=None)

    @property
    def score(self) -> tuple:
        r = self.report
        hard = [c for c in r.checks if not c.ok and c.name in HARD_CHECKS]
        return (not hard, self.finished, r.ok, r.passed, -len([c for c in r.checks if not c.ok]))


# Failures that mean the code is broken (vs. merely weaker). These drive repair first.
HARD_CHECKS = {"Valid syntax", "All names defined", "Tags balanced", "Complete document", "Embedded JavaScript valid",
               "Embedded CSS valid", "Script finds its elements", "Buttons call real functions", "No keyboard input",
               "Loops can finish", "No placeholders", "Parses", "Has code", "No empty functions"}


class Chat:
    def __init__(self, model: str, temperature: float, budget: int, timeout: int = 480, num_ctx: int = CONTEXT_TOKENS):
        self.model, self.temperature, self.budget, self.timeout, self.num_ctx = model, temperature, budget, timeout, num_ctx
        self.eval_tokens = 0
        self.prompt_tokens = 0
        self.calls = 0

    def ask(self, messages: list[dict], budget: int | None = None, temperature: float | None = None) -> tuple[str, bool]:
        body = {"model": self.model, "stream": False, "keep_alive": "10m", "messages": messages,
                "options": {"temperature": self.temperature if temperature is None else temperature,
                            "top_p": 0.9, "repeat_penalty": 1.05, "num_predict": budget or self.budget,
                            "num_ctx": self.num_ctx}}
        request = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.load(response)
        self.calls += 1
        self.eval_tokens += data.get("eval_count") or 0
        self.prompt_tokens = max(self.prompt_tokens, data.get("prompt_eval_count") or 0)
        return data.get("message", {}).get("content", ""), data.get("done_reason") != "length"


def extract_code(raw: str, lang: str) -> str:
    """Pull the file out of a reply, tolerating fences, chatter and separate CSS/JS blocks."""
    blocks = FENCE.findall(raw)
    if not blocks:
        code = raw.strip()
        # Drop a lead-in sentence such as "Here is the code:" when the code starts later.
        starts = {"python": r"^(?:import |from |def |class |@|#|\"\"\"|[A-Za-z_]\w* = )", "javascript": r"^(?:/[/*]|const |let |function |class |import |export |'use strict')",
                  "css": r"^(?:/\*|:root|@|[.#*a-z][^{\n]*\{)", "html": r"^(?:<!DOCTYPE|<html|<!--)"}[lang]
        lines = code.splitlines()
        first = next((i for i, line in enumerate(lines) if re.match(starts, line.strip(), re.I)), 0)
        return "\n".join(lines[first:]).strip() + "\n"
    aliases = {"py": "python", "python3": "python", "js": "javascript", "javascript": "javascript", "html": "html",
               "css": "css", "python": "python"}
    main = [b for tag, b in blocks if aliases.get(tag.lower(), lang if not tag else None) == lang]
    code = (max(main, key=len) if main else max((b for _, b in blocks), key=len)).strip() + "\n"
    if lang == "html":
        for tag, asset in blocks:
            kind = aliases.get(tag.lower())
            if kind == "css" and "<style" not in code.lower():
                code = re.sub(r"<link\b[^>]*rel=[\"']stylesheet[\"'][^>]*>", "", code, flags=re.I)
                code = re.sub(r"</head\s*>", lambda m: "<style>\n" + asset + "\n</style>\n" + m.group(0), code, count=1, flags=re.I)
            elif kind == "javascript" and not re.search(r"<script\b(?![^>]*src=)", code, re.I):
                code = re.sub(r"<script\b[^>]*src=[\"'][^\"']+[\"'][^>]*>\s*</script>", "", code, flags=re.I)
                code = re.sub(r"</body\s*>", lambda m: "<script>\n" + asset + "\n</script>\n" + m.group(0), code, count=1, flags=re.I)
    return code


def check(code: str, lang: str) -> Report:
    if lang == "python":
        report = check_python(code)
    elif lang == "css":
        report = check_css(code)
    elif lang == "javascript":
        report = Report("javascript")
        error = check_js_many([code])[0] if code.strip() else "empty"
        report.add("Valid syntax", error is None, error or "")
        report.stats = {"lines": code.rstrip("\n").count("\n") + 1}
    else:
        report = check_html(code)
        styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", code, re.I | re.S))
        report.add("Embedded website styling", len(styles.strip()) >= 250,
                   "The page has almost no CSS, so it will look like plain text. Add real styling in the <style> block.")
        report.add("Responsive layout", bool(re.search(r"@media|auto-fit|auto-fill|clamp\(", styles, re.I)),
                   "No responsive rule: add a media query or fluid grid so it works on phones.")
        missing = missing_assets(code)
        report.add("Referenced files exist", not missing,
                   "The page links files that don't exist: " + ", ".join(missing[:6]) + ". Inline them or remove them.")
    return add_quality_checks(code, lang, report)


def problems_text(draft: Draft) -> str:
    failed = sorted((c for c in draft.report.checks if not c.ok), key=lambda c: c.name not in HARD_CHECKS)
    lines = [f"- {c.name}: {c.detail or 'failed'}" for c in failed[:8]]
    if not draft.finished:
        lines.insert(0, "- The file was cut off before the end.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def generate(prompt: str, lang: str, *, model: str, temperature: float, max_tokens: int,
             guidance: str = "", skills: str = "", log=None) -> dict:
    """Returns {"code", "lang", "finished", "report", "rounds", "steps", "tokens", "prompt_tokens"}."""
    effort = EFFORT[effort_for(max_tokens)]
    budget = (min(max(max_tokens * 2, 512), 2400) if lang != "html"
              else 2400 if max_tokens <= 256 else 3200 if max_tokens <= 450 else 4000 if max_tokens <= 650 else 4800)
    # Fix requests carry a whole file; give them room for the file plus a full rewrite.
    num_ctx = CONTEXT_TOKENS if len(prompt) < 5000 else LONG_CONTEXT_TOKENS
    chat = Chat(model, min(max(temperature, 0.0), 1.0), budget, num_ctx=num_ctx)
    system = SYSTEM[lang]
    if skills:
        system += "\n\nAlso follow these skills the user turned on (an explicit request still wins):\n" + skills
    if guidance:
        system += "\n\nProject guidance (use where relevant; the request wins):\n" + guidance
    steps = []

    plan = ""
    if effort["plan"]:
        plan, _ = chat.ask([{"role": "system", "content": f"You are a careful {lang} engineer planning a task."},
                            {"role": "user", "content": PLAN_PROMPT.format(lang=lang, request=prompt)}],
                           budget=420, temperature=0.2)
        plan = "\n".join(line for line in plan.strip().splitlines() if line.strip())[:2000]
        steps.append("plan")

    request = ("Complete this code and return the whole finished file:\n" if re.match(r"^\s*(def |class |import |from |@|function |const )", prompt)
               else "Write the code for this request:\n") + prompt
    if plan:
        request += "\n\nRequirements checklist (implement all of it):\n" + plan
    messages = [{"role": "system", "content": system}, {"role": "user", "content": request}]

    raw, finished = chat.ask(messages)
    best = Draft(extract_code(raw, lang), finished)
    best.report = check(best.code, lang)
    steps.append("write")
    last_raw = raw

    for _ in range(effort["repairs"]):
        if best.report.ok and best.finished:
            break
        follow = CUTOFF_PROMPT if not best.finished and best.report.ok else REPAIR_PROMPT.format(problems=problems_text(best))
        convo = messages + [{"role": "assistant", "content": last_raw[-12000:]}, {"role": "user", "content": follow}]
        raw, finished = chat.ask(convo, temperature=max(0.1, chat.temperature - 0.1))
        candidate = Draft(extract_code(raw, lang), finished)
        candidate.report = check(candidate.code, lang)
        steps.append("repair")
        if log:
            log(f"repair: {best.score} -> {candidate.score}")
        if candidate.score > best.score:
            best, last_raw = candidate, raw

    if effort["review"] and plan and best.finished and best.report.ok:
        convo = messages + [{"role": "assistant", "content": best.code}, {"role": "user", "content": REVIEW_PROMPT.format(plan=plan)}]
        raw, finished = chat.ask(convo, temperature=0.1)
        candidate = Draft(extract_code(raw, lang), finished)
        candidate.report = check(candidate.code, lang)
        steps.append("review")
        # A review may add what was missing, but must not break or gut a passing answer.
        if candidate.finished and candidate.report.ok and len(candidate.code) >= 0.8 * len(best.code):
            best = candidate

    return {"code": best.code, "lang": lang, "finished": best.finished, "report": best.report,
            "rounds": chat.calls, "steps": steps, "tokens": chat.eval_tokens, "prompt_tokens": chat.prompt_tokens,
            "context_tokens": num_ctx}
