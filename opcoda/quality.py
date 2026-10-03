"""Extra static checks for generated code. Nothing here runs the code.

opcoda.verify answers "does it parse?". These catch the mistakes small models make in
code that parses: placeholders, programs that wait for keyboard input, infinite loops,
scripts that look up elements the page doesn't have, buttons wired to functions that
don't exist, and form fields nobody can identify. Each failure carries a plain message
that is fed back to the model in the repair round.
"""
import ast
import re

from opcoda.verify import Report, _HTMLChecker

# Only comment-style TODO/FIXME: a to-do app legitimately says "todo" everywhere.
PLACEHOLDER = re.compile(r"(?:#|//|/\*|<!--)\s*(?:TODO|FIXME)\b|(?i:your code here|implement (?:this|me)\b|lorem ipsum)")
JS_DECL = re.compile(r"(?:function\s+([A-Za-z_$][\w$]*)|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=|"
                     r"window\.([A-Za-z_$][\w$]*)\s*=|([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{)")
JS_ID_LOOKUP = re.compile(r"""getElementById\(\s*['"]([^'"]+)['"]\s*\)|querySelector(?:All)?\(\s*['"]#([A-Za-z][\w-]*)['"]\s*\)""")
INLINE_CALL = re.compile(r"^\s*(?:return\s+)?([A-Za-z_$][\w$]*)\s*\(")


def _loop_can_exit(loop: ast.While) -> bool:
    for node in ast.walk(loop):
        if isinstance(node, (ast.Break, ast.Return, ast.Raise)):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("exit", "quit"):
            return True
        if isinstance(node, ast.Attribute) and node.attr == "exit":
            return True
    return False


def python_checks(code: str, report: Report) -> None:
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return
    calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    report.add("No keyboard input", "input" not in calls,
               "The program calls input(), which waits forever in the Run sandbox. Use example values in the demo instead.")
    forever = [n.lineno for n in ast.walk(tree)
               if isinstance(n, ast.While) and isinstance(n.test, ast.Constant) and n.test.value and not _loop_can_exit(n)]
    report.add("Loops can finish", not forever, f"while True on line {forever[0]} has no break, return or raise." if forever else "")
    mutable = [f"{f.name}()" for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
               for d in f.args.defaults + [d for d in f.args.kw_defaults if d is not None]
               if isinstance(d, (ast.List, ast.Dict, ast.Set))]
    report.add("No shared mutable defaults", not mutable,
               f"{mutable[0]} uses a list/dict/set as a default argument; use None and create it inside." if mutable else "")
    # A function that computes a result shouldn't also chatter: leftover debug prints.
    noisy = []
    for f in ast.walk(tree):
        if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and f.name not in ("main", "demo"):
            returns_value = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(f))
            prints = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print" for n in ast.walk(f))
            if returns_value and prints:
                noisy.append(f.name)
    report.add("No debug prints", not noisy,
               f"{noisy[0]}() returns a result but also prints; remove the debug print() calls and print in the demo instead." if noisy else "")
    ellipsis = [f.name for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
                and any(isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is Ellipsis for s in f.body)]
    marker = PLACEHOLDER.search(code)
    report.add("No placeholders", not ellipsis and not marker,
               f"{ellipsis[0]}() is left as '...'" if ellipsis else f"Unfinished marker in the code: '{marker.group(0)}'" if marker else "")


def _js_names(source: str) -> set[str]:
    return {name for match in JS_DECL.finditer(source) for name in match.groups() if name}


def javascript_checks(code: str, report: Report) -> None:
    marker = PLACEHOLDER.search(code)
    report.add("No placeholders", not marker, f"Unfinished marker in the code: '{marker.group(0)}'" if marker else "")
    report.add("No keyboard prompts", not re.search(r"\b(prompt|readline)\s*\(", code),
               "The script waits for typed input (prompt/readline), which stalls in the Run sandbox. Use example values.")


class _Inventory(_HTMLChecker):
    """Also records inline handlers, form fields and their labels."""

    def __init__(self):
        super().__init__()
        self.handlers: list[str] = []
        self.fields: list[dict] = []
        self.label_for: set[str] = set()
        self.label_depth = 0
        self.images_without_alt = 0

    def _attrs(self, tag, attrs):
        super()._attrs(tag, attrs)
        a = {k: (v or "") for k, v in attrs}
        self.handlers += [v for k, v in a.items() if k.startswith("on") and v]
        if tag == "label":
            if a.get("for"):
                self.label_for.add(a["for"])
        if tag == "img" and "alt" not in a:
            self.images_without_alt += 1
        if tag in ("input", "select", "textarea") and a.get("type", "").lower() not in ("hidden", "submit", "button", "reset", "image"):
            self.fields.append({"id": a.get("id", ""), "named": bool(a.get("aria-label") or a.get("aria-labelledby") or a.get("title")),
                                "wrapped": self.label_depth > 0, "type": a.get("type", tag)})

    def handle_starttag(self, tag, attrs):
        if tag == "label":
            self.label_depth += 1
        super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "label" and self.label_depth:
            self.label_depth -= 1
        super().handle_endtag(tag)


def html_checks(code: str, report: Report) -> None:
    page = _Inventory()
    try:
        page.feed(code)
        page.close()
    except Exception:  # noqa: BLE001 - verify.check_html already reports parse problems
        return
    script = "\n".join(page.scripts)
    ids = set(page.ids)
    wanted = {a or b for a, b in JS_ID_LOOKUP.findall(script)}
    created = set(re.findall(r"""\.id\s*=\s*['"]([^'"]+)['"]""", script))
    missing = sorted(wanted - ids - created)
    report.add("Script finds its elements", not missing,
               "The script looks up ids the page doesn't have: " + ", ".join(f"#{m}" for m in missing[:5]))
    names = _js_names(script)
    calls = {m.group(1) for h in page.handlers if (m := INLINE_CALL.match(h))}
    builtin = {"alert", "confirm", "event", "this", "history", "location", "window", "document", "console", "print"}
    undefined = sorted(calls - names - builtin)
    report.add("Buttons call real functions", not undefined,
               "Inline handlers call functions the page never defines: " + ", ".join(f"{u}()" for u in undefined[:5]))
    unlabeled = [f for f in page.fields if not (f["named"] or f["wrapped"] or (f["id"] and f["id"] in page.label_for))]
    report.add("Form fields are labelled", not unlabeled,
               f"{len(unlabeled)} form field(s) have no <label> or aria-label." if unlabeled else "")
    report.add("Images have alt text", page.images_without_alt == 0,
               f"{page.images_without_alt} <img> without an alt attribute." if page.images_without_alt else "")
    marker = PLACEHOLDER.search(code)
    report.add("No placeholders", not marker, f"Unfinished marker in the page: '{marker.group(0)}'" if marker else "")


def add_quality_checks(code: str, lang: str, report: Report) -> Report:
    if lang == "python":
        python_checks(code, report)
    elif lang == "javascript":
        javascript_checks(code, report)
    elif lang == "html":
        html_checks(code, report)
    return report
