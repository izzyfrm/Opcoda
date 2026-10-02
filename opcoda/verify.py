"""Static checks for code in Coda's four languages.

Nothing in this module runs the code it checks:
- Python: ast.parse plus a scope analysis that finds names used but never defined
  (Coda's most common mistake, e.g. `return number % 2` inside `def evens(nums)`).
- HTML: tag balance via html.parser, document structure, embedded <style>/<script>.
- CSS: braces, selectors, `property: value` declarations, known property names.
- JavaScript: compiled (never called) with `new AsyncFunction(source)` in Node when
  Node is installed; otherwise a bracket/string balance check.

Used by the curriculum generator (to keep training data valid), server.py (to pick the
best of several drafts), and CodaBench.
"""
from __future__ import annotations

import ast
import builtins
import html.parser
import json
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass, field

LANGS = ("python", "html", "css", "javascript")


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class Report:
    lang: str
    checks: list[Check] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return bool(self.checks) and all(c.ok for c in self.checks)

    @property
    def passed(self) -> int:
        return sum(c.ok for c in self.checks)

    def add(self, name: str, ok: bool, detail: str = "") -> bool:
        self.checks.append(Check(name, bool(ok), detail if not ok else ""))
        return ok

    def to_dict(self) -> dict:
        return {"lang": self.lang, "ok": self.ok,
                "checks": [c.__dict__ for c in self.checks], "stats": self.stats}


def check(code: str, lang: str) -> Report:
    lang = normalize_lang(lang)
    if lang == "python":
        return check_python(code)
    if lang == "html":
        return check_html(code)
    if lang == "css":
        return check_css(code)
    if lang == "javascript":
        return check_js(code)
    report = Report(lang or "unknown")
    report.add("Known language", False, f"unsupported language {lang!r}")
    return report


def normalize_lang(lang: str | None) -> str:
    lang = (lang or "").strip().lower()
    return {"py": "python", "js": "javascript", "htm": "html"}.get(lang, lang)


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

BUILTIN_NAMES = set(dir(builtins)) | {"__name__", "__file__", "__doc__", "__builtins__"}
_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _bindings(nodes) -> set[str]:
    """Names bound directly in a scope (not inside nested functions/classes/comprehensions)."""
    names: set[str] = set()
    stack = list(nodes)
    while stack:
        n = stack.pop()
        if isinstance(n, (*_FUNCS, ast.ClassDef)):
            names.add(n.name)
            continue
        if isinstance(n, (ast.Lambda, *_COMPREHENSIONS)):
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            names.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for alias in n.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            names.update(n.names)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            names.add(n.name)
        elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and n.name:
            names.add(n.name)
        elif isinstance(n, ast.MatchMapping) and n.rest:
            names.add(n.rest)
        stack.extend(ast.iter_child_nodes(n))
    return names


def _params(args: ast.arguments) -> set[str]:
    names = {a.arg for a in args.posonlyargs + args.args + args.kwonlyargs}
    if args.vararg:
        names.add(args.vararg.arg)
    if args.kwarg:
        names.add(args.kwarg.arg)
    return names


def _find_undefined(nodes, visible: set[str], undefined: set[str]) -> None:
    stack = list(nodes)
    while stack:
        n = stack.pop()
        if isinstance(n, _FUNCS):
            stack.extend(n.decorator_list)
            stack.extend(n.args.defaults)
            stack.extend(d for d in n.args.kw_defaults if d is not None)
            _find_undefined(n.body, visible | _params(n.args) | _bindings(n.body), undefined)
            continue
        if isinstance(n, ast.Lambda):
            stack.extend(n.args.defaults)
            _find_undefined([n.body], visible | _params(n.args), undefined)
            continue
        if isinstance(n, ast.ClassDef):
            stack.extend(n.bases)
            stack.extend(k.value for k in n.keywords)
            stack.extend(n.decorator_list)
            class_names = _bindings(n.body)
            for stmt in n.body:  # methods don't see class-level names; class body does
                _find_undefined([stmt], visible if isinstance(stmt, _FUNCS) else visible | class_names, undefined)
            continue
        if isinstance(n, _COMPREHENSIONS):
            targets = {t.id for g in n.generators for t in ast.walk(g.target) if isinstance(t, ast.Name)}
            inner = [g.iter for g in n.generators] + [i for g in n.generators for i in g.ifs]
            inner += [n.key, n.value] if isinstance(n, ast.DictComp) else [n.elt]
            _find_undefined(inner, visible | targets, undefined)
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            if n.id not in visible:
                undefined.add(n.id)
            continue
        stack.extend(ast.iter_child_nodes(n))


def undefined_names(tree: ast.Module) -> set[str]:
    undefined: set[str] = set()
    _find_undefined(tree.body, BUILTIN_NAMES | _bindings(tree.body), undefined)
    return undefined


def check_python(code: str) -> Report:
    report = Report("python")
    if not code.strip():
        report.add("Has code", False, "empty")
        return report
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError) as exc:
        report.add("Valid syntax", False, f"{getattr(exc, 'msg', exc)} (line {getattr(exc, 'lineno', '?')})")
        return report
    report.add("Valid syntax", True)
    missing = sorted(undefined_names(tree))
    report.add("All names defined", not missing, "undefined: " + ", ".join(missing[:6]))
    funcs = [n for n in ast.walk(tree) if isinstance(n, _FUNCS)]
    empty = [f.name for f in funcs if all(isinstance(s, ast.Pass) or (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)) for s in f.body)]
    report.add("No empty functions", not empty, ", ".join(empty[:4]))
    report.stats = {
        "lines": code.rstrip("\n").count("\n") + 1,
        "functions": len(funcs),
        "classes": sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree)),
    }
    return report


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
KNOWN_TAGS = VOID_TAGS | set("""a abbr address article aside audio b blockquote body button canvas caption cite code
data datalist dd del details dfn dialog div dl dt em fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 head
header hgroup html i iframe ins kbd label legend li main map mark menu meter nav noscript object ol optgroup option
output p picture pre progress q s samp script search section select slot small span strong style sub summary sup svg
table tbody td template textarea tfoot th thead time title tr u ul var video path circle rect line polyline polygon g
defs symbol use ellipse text tspan desc lineargradient radialgradient stop clippath mask pattern image foreignobject""".split())
SECTION_TAGS = {"header", "nav", "main", "section", "article", "aside", "footer", "form"}


class _HTMLChecker(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.tags: Counter = Counter()
        self.unknown: set[str] = set()
        self.doctype = False
        self.styles: list[str] = []
        self.scripts: list[str] = []
        self._raw: list[str] | None = None
        self.ids: Counter = Counter()

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype html"):
            self.doctype = True

    def _attrs(self, tag, attrs):
        self.tags[tag] += 1
        if tag not in KNOWN_TAGS and "-" not in tag:
            self.unknown.add(tag)
        for key, value in attrs:
            if key == "id" and value:
                self.ids[value] += 1

    def handle_starttag(self, tag, attrs):
        self._attrs(tag, attrs)
        if tag in VOID_TAGS:
            return
        self.stack.append(tag)
        if tag in ("style", "script") and not any(k == "src" for k, _ in attrs):
            self._raw = []

    def handle_startendtag(self, tag, attrs):
        self._attrs(tag, attrs)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if tag in ("style", "script") and self._raw is not None:
            (self.styles if tag == "style" else self.scripts).append("".join(self._raw))
            self._raw = None
        if not self.stack:
            self.errors.append(f"unexpected </{tag}>")
        elif self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            self.errors.append(f"<{self.stack[-1]}> not closed before </{tag}>")
            while self.stack and self.stack[-1] != tag:
                self.stack.pop()
            self.stack.pop()
        else:
            self.errors.append(f"unexpected </{tag}>")

    def handle_data(self, data):
        if self._raw is not None:
            self._raw.append(data)


def check_html(code: str, js_checker=None) -> Report:
    report = Report("html")
    parser = _HTMLChecker()
    try:
        parser.feed(code)
        parser.close()
    except Exception as exc:  # html.parser is forgiving; this is just a guard
        report.add("Parses", False, str(exc))
        return report
    if parser.stack:
        parser.errors.append("unclosed " + ", ".join(f"<{t}>" for t in parser.stack[-3:]))
    report.add("Tags balanced", not parser.errors, "; ".join(parser.errors[:3]))
    full_document = parser.doctype or parser.tags["html"] > 0
    if full_document:
        missing = [t for t in ("html", "head", "body", "title") if parser.tags[t] == 0]
        report.add("Complete document", parser.doctype and not missing,
                   ("missing " + ", ".join(missing)) if missing else "missing <!DOCTYPE html>")
    report.add("Known tags only", not parser.unknown, ", ".join(sorted(parser.unknown)[:4]))
    dup_ids = [i for i, n in parser.ids.items() if n > 1]
    report.add("Unique ids", not dup_ids, ", ".join(dup_ids[:4]))
    for css in parser.styles:
        sub = check_css(css)
        report.add("Embedded CSS valid", sub.ok, next((c.detail for c in sub.checks if not c.ok), ""))
    if parser.scripts:
        results = (js_checker or check_js_many)(parser.scripts)
        errors = [e for e in results if e]
        report.add("Embedded JavaScript valid", not errors, errors[0] if errors else "")
    report.stats = {
        "lines": code.rstrip("\n").count("\n") + 1,
        "sections": sum(parser.tags[t] for t in SECTION_TAGS),
        "elements": sum(parser.tags.values()),
        "document": full_document,
    }
    return report


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS_PROPERTIES = set("""
accent-color align-content align-items align-self all animation animation-delay animation-direction
animation-duration animation-fill-mode animation-iteration-count animation-name animation-play-state
animation-timing-function appearance aspect-ratio backdrop-filter backface-visibility background
background-attachment background-blend-mode background-clip background-color background-image background-origin
background-position background-repeat background-size block-size border border-block border-bottom
border-bottom-color border-bottom-left-radius border-bottom-right-radius border-bottom-style border-bottom-width
border-collapse border-color border-image border-inline border-left border-left-color border-left-style
border-left-width border-radius border-right border-right-color border-right-style border-right-width
border-spacing border-style border-top border-top-color border-top-left-radius border-top-right-radius
border-top-style border-top-width border-width bottom box-shadow box-sizing break-inside caption-side caret-color
clear clip clip-path color color-scheme column-count column-gap column-rule column-width columns contain
container container-name container-type content counter-increment counter-reset cursor direction display
empty-cells fill filter flex flex-basis flex-direction flex-flow flex-grow flex-shrink flex-wrap float font
font-display font-family font-feature-settings font-size font-style font-variant font-variant-numeric font-weight
gap grid grid-area grid-auto-columns grid-auto-flow grid-auto-rows grid-column grid-column-end grid-column-start
grid-row grid-row-end grid-row-start grid-template grid-template-areas grid-template-columns grid-template-rows
height hyphens image-rendering inline-size inset isolation justify-content justify-items justify-self left
letter-spacing line-height list-style list-style-image list-style-position list-style-type margin margin-block
margin-block-end margin-block-start margin-bottom margin-inline margin-inline-end margin-inline-start margin-left
margin-right margin-top mask max-block-size max-height max-inline-size max-width min-block-size min-height
min-inline-size min-width mix-blend-mode object-fit object-position opacity order outline outline-color
outline-offset outline-style outline-width overflow overflow-wrap overflow-x overflow-y overscroll-behavior
padding padding-block padding-bottom padding-inline padding-left padding-right padding-top place-content
place-items place-self pointer-events position quotes resize right rotate row-gap scale scroll-behavior
scroll-margin scroll-margin-top scroll-padding scroll-snap-align scroll-snap-type scrollbar-color scrollbar-width
src stroke stroke-width tab-size table-layout text-align text-decoration text-decoration-color
text-decoration-line text-decoration-thickness text-indent text-overflow text-rendering text-shadow
text-transform text-underline-offset top touch-action transform transform-origin transition transition-delay
transition-duration transition-property transition-timing-function translate unicode-range user-select
vertical-align visibility white-space width will-change word-break word-spacing word-wrap writing-mode z-index
-webkit-font-smoothing -moz-osx-font-smoothing -webkit-tap-highlight-color -webkit-appearance -webkit-text-size-adjust
text-size-adjust -webkit-backdrop-filter -webkit-line-clamp line-clamp
""".split())
_DECL = re.compile(r"^\s*(--[A-Za-z0-9_-]+|-?[A-Za-z][A-Za-z-]*)\s*:\s*(\S[\s\S]*?)\s*$")


def _split_css(css: str):
    """Yield ('open', prelude) / ('close', '') / ('decl', text) events, respecting strings and parens."""
    css = re.sub(r"/\*[\s\S]*?\*/", "", css)
    buf, quote, depth = [], None, 0
    for ch in css:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            buf.append(ch)
        elif depth == 0 and ch == "{":
            yield "open", "".join(buf).strip()
            buf = []
        elif depth == 0 and ch == "}":
            if "".join(buf).strip():
                yield "decl", "".join(buf).strip()
            buf = []
            yield "close", ""
        elif depth == 0 and ch == ";":
            yield "decl", "".join(buf).strip()
            buf = []
        else:
            buf.append(ch)
    if quote or depth:
        yield "error", "unterminated string or parenthesis"
    if "".join(buf).strip():
        yield "trailing", "".join(buf).strip()


def check_css(css: str) -> Report:
    report = Report("css")
    if not css.strip():
        report.add("Has rules", False, "empty")
        return report
    errors, unknown = [], set()
    stack: list[str] = []  # 'rule' | 'group' (@media etc.) | 'keyframes'
    rules = declarations = 0
    for kind, text in _split_css(css):
        if kind == "open":
            if not text:
                errors.append("rule without a selector")
            parent = stack[-1] if stack else "group"
            if text.startswith("@"):
                at = text.split()[0].lower()
                stack.append("keyframes" if "keyframes" in at else
                             "rule" if at in ("@font-face", "@page") else "group")
            elif parent == "rule":
                stack.append("rule")  # CSS nesting
            else:
                stack.append("rule")
                rules += 1
        elif kind == "close":
            if not stack:
                errors.append("unexpected }")
            else:
                stack.pop()
        elif kind == "decl":
            if not text:
                continue
            if text.startswith("@"):  # @import / @charset statements
                continue
            if not stack or stack[-1] != "rule":
                errors.append(f"declaration outside a rule: {text[:30]!r}")
                continue
            m = _DECL.match(text)
            if not m:
                errors.append(f"malformed declaration: {text[:40]!r}")
                continue
            declarations += 1
            prop = m.group(1).lower()
            if not prop.startswith("--") and prop not in CSS_PROPERTIES:
                unknown.add(prop)
        elif kind in ("error", "trailing"):
            errors.append(text if kind == "error" else f"unexpected text at end: {text[:30]!r}")
    if stack:
        errors.append(f"{len(stack)} unclosed block(s)")
    report.add("Braces and declarations valid", not errors, "; ".join(errors[:3]))
    report.add("Known properties only", not unknown, ", ".join(sorted(unknown)[:5]))
    report.add("Has rules", rules > 0, "no rules found")
    report.stats = {"lines": css.rstrip("\n").count("\n") + 1, "rules": rules, "declarations": declarations}
    return report


# ---------------------------------------------------------------------------
# JavaScript
# ---------------------------------------------------------------------------

_NODE_CHECKER = r"""
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
let input = "";
process.stdin.on("data", (d) => (input += d)).on("end", () => {
  const out = JSON.parse(input).map((src) => {
    try { new AsyncFunction(src); return null; }   // compiles only; never called
    catch (e) { return String(e.message).slice(0, 200); }
  });
  process.stdout.write(JSON.stringify(out));
});
"""


def _balance_check(src: str) -> str | None:
    pairs, stack, i, n = {")": "(", "]": "[", "}": "{"}, [], 0, len(src)
    while i < n:
        ch = src[i]
        if src.startswith("//", i):
            i = src.find("\n", i)
            i = n if i == -1 else i
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j == -1:
                return "unterminated comment"
            i = j + 2
            continue
        if ch in "\"'`":
            j = i + 1
            while j < n and src[j] != ch:
                j += 2 if src[j] == "\\" else 1
            if j >= n:
                return "unterminated string"
            i = j + 1
            continue
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if not stack or stack.pop() != pairs[ch]:
                return f"unbalanced {ch}"
        i += 1
    return f"unclosed {stack[-1]}" if stack else None


def check_js_many(sources: list[str], timeout: float = 20.0) -> list[str | None]:
    """Syntax-check many scripts at once. Returns an error message (or None) per script."""
    if not sources:
        return []
    node = shutil.which("node")
    if node:
        try:
            proc = subprocess.run([node, "-e", _NODE_CHECKER], input=json.dumps(sources),
                                  capture_output=True, text=True, timeout=timeout, encoding="utf-8")
            if proc.returncode == 0:
                return json.loads(proc.stdout)
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
            pass
    return [_balance_check(s) for s in sources]


def check_js(code: str) -> Report:
    report = Report("javascript")
    if not code.strip():
        report.add("Has code", False, "empty")
        return report
    error = check_js_many([code])[0]
    report.add("Valid syntax", error is None, error or "")
    report.stats = {
        "lines": code.rstrip("\n").count("\n") + 1,
        "functions": len(re.findall(r"\bfunction\b|=>", code)),
    }
    return report
