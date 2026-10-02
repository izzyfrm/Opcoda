"""Generate Coda's Phase 3 Python curriculum (original, deterministic, local).

No external model and no downloads. Output is a JSONL file of examples in two
families of formats:

- instruction-to-code:

    <task>
    Return the number of vowels in text, ignoring case.
    </task>
    <code>
    def count_vowels(text):
        ...
    </code>

- plain code completion (bare function, "# description" comment, or the legacy
  "# Task: description" comment).

Anti-memorisation measures:
- 200+ task families, each with several implementations and phrasings;
- fresh function/parameter/local names for every example (no add_1/add_2);
- docstrings in only a small fraction of examples;
- AST-level dedup (ignores docstrings and type hints);
- whole task families are held out for validation, so val loss measures
  generalisation to *unseen tasks*, not recall of seen ones;
- CodaBench tasks (evals/heldout_tasks.json) are banned from the curriculum.

Usage:
    python tools/make_python_curriculum.py
    python tools/make_python_curriculum.py --per-family 250 --seed 7
"""
from __future__ import annotations

import argparse
import ast
import builtins
import copy
import json
import keyword
import math
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from string import Template
from textwrap import dedent, indent

sys.path.insert(0, str(Path(__file__).resolve().parent))
from curriculum_families import FAMILIES, LOCAL_POOLS, PAIR_POOLS, PARAM_POOLS, TYPE_HINTS, Family  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
HELDOUT = REPO / "evals" / "heldout_tasks.json"
RESERVED = set(keyword.kwlist) | set(dir(builtins))
PLACEHOLDER = re.compile(r"\$(?:([_a-z][_a-z0-9]*)|\{([_a-z][_a-z0-9]*)\})", re.IGNORECASE)

# "Return x" -> "Write a function that returns x" for extra phrasing variety.
THIRD_PERSON = {
    "Return": "returns", "Count": "counts", "Check": "checks", "Convert": "converts",
    "Add": "adds", "Subtract": "subtracts", "Multiply": "multiplies", "Divide": "divides",
    "Clamp": "clamps", "Reverse": "reverses", "Collapse": "collapses", "Pad": "pads",
    "Shift": "shifts", "Join": "joins", "Parse": "parses", "Format": "formats",
    "Turn": "turns", "Remove": "removes", "Split": "splits", "Group": "groups",
    "Increase": "increases", "Round": "rounds",
}
LEADS = ["Write a function that", "Write a Python function that", "Implement a function that", "Create a function that"]


@dataclass
class Rendered:
    fn: str
    task: str
    code: str
    impl: int


def placeholders(template: str) -> set[str]:
    return {m.group(1) or m.group(2) for m in PLACEHOLDER.finditer(template)}


def _choose(options, rng, canonical):
    if not options:
        return None
    return options[0] if canonical else rng.choice(options)


def render(fam: Family, rng: random.Random, *, impl: int | None = None, canonical: bool = False,
           hint_prob: float = 0.0, doc_prob: float = 0.0) -> Rendered | None:
    used = set(RESERVED)
    fn = _choose(list(fam.names), rng, canonical)
    used.add(fn)
    mapping = {"fn": fn}
    params: list[tuple[str, str | None]] = []

    for phs, pool in fam.sig:
        if pool in PAIR_POOLS:
            options = [t for t in PAIR_POOLS[pool] if len(t) == len(phs) and not set(t) & used]
            names = _choose(options, rng, canonical)
            hints = TYPE_HINTS.get(pool, (None,) * len(phs))
        else:
            names = _choose([n for n in PARAM_POOLS[pool] if n not in used], rng, canonical)
            names = (names,) if names else None
            hints = TYPE_HINTS.get(pool, (None,))
        if not names:
            return None
        for ph, name, hint in zip(phs, names, hints):
            mapping[ph] = name
            used.add(name)
            params.append((name, hint))

    impl_index = rng.randrange(len(fam.impls)) if impl is None else impl
    template = dedent(fam.impls[impl_index]).strip("\n")
    for ph in sorted(placeholders(template) - mapping.keys()):
        name = _choose([n for n in LOCAL_POOLS[ph] if n not in used], rng, canonical)
        if name is None:
            return None
        mapping[ph] = name
        used.add(name)

    body = Template(template).substitute(mapping)
    task = Template(fam.tasks[0] if canonical else rng.choice(fam.tasks)).substitute(mapping)

    if fam.kind == "class":
        return Rendered(fn, task, body + "\n", impl_index)

    lines = body.split("\n")
    if not canonical and len(lines) >= 4 and rng.random() < 0.10:
        last_return = max((i for i, line in enumerate(lines) if line.startswith("return ")), default=0)
        if last_return > 0 and lines[last_return - 1].strip():
            lines.insert(last_return, "")
    if not canonical and rng.random() < doc_prob and '"' not in task and "\\" not in task:
        lines.insert(0, f'"""{task}"""')
    body = "\n".join(lines)

    annotate = (not canonical and rng.random() < hint_prob and all(h for _, h in params))
    args = ", ".join(f"{n}: {h}" if annotate else n for n, h in params)
    code = f"def {fn}({args}):\n" + indent(body, "    ", lambda line: bool(line.strip())) + "\n"
    return Rendered(fn, task, code, impl_index)


def canonical_code(code: str) -> str:
    """AST form without docstrings/annotations, so cosmetic variants count as duplicates."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body = node.body[1:] or [ast.Pass()]
        if isinstance(node, ast.FunctionDef):
            node.returns = None
            for a in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
                a.annotation = None
    return ast.unparse(tree)


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def _same(a, b) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        try:
            return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
        except TypeError:
            return False
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return type(a) is type(b) and len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


def _run(code: str, name: str, args):
    # Trusted code: these are our own curriculum templates, not model output.
    ns: dict = {}
    exec(compile(code, f"<{name}>", "exec"), ns)
    try:
        return ("ok", ns[name](*copy.deepcopy(args)))
    except Exception as exc:  # noqa: BLE001 - we compare exception types across variants
        return ("raise", type(exc).__name__)


def verify(families: list[Family], trials: int = 4) -> list[str]:
    """Every implementation must parse and agree with implementation 0 on the family's checks."""
    errors = []
    rng = random.Random(0)
    for fam in families:
        try:
            if fam.kind == "class":
                for i in range(len(fam.impls)):
                    for t in range(trials):
                        r = render(fam, rng, impl=i, canonical=(t == 0))
                        exec(compile(r.code, f"<{fam.key}>", "exec"), {})
                continue
            ref = render(fam, rng, impl=0, canonical=True)
            expected = [_run(ref.code, ref.fn, args) for args in fam.checks]
            for kind, value in expected:
                if kind != "ok":
                    errors.append(f"{fam.key}: reference raised {value}")
            for i in range(len(fam.impls)):
                for t in range(trials):
                    r = render(fam, rng, impl=i, canonical=(t == 0), hint_prob=0.5, doc_prob=0.5)
                    if r is None:
                        continue
                    for args, want in zip(fam.checks, expected):
                        got = _run(r.code, r.fn, args)
                        if got[0] != want[0] or not _same(got[1], want[1]):
                            errors.append(f"{fam.key} impl {i}: {args!r} -> {got!r}, expected {want!r}\n{r.code}")
                            break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{fam.key}: {type(exc).__name__}: {exc}")
    return errors


def load_heldout() -> tuple[list[str], list[re.Pattern]]:
    spec = json.loads(HELDOUT.read_text(encoding="utf-8"))
    names = [t["name"] for t in spec["tasks"]]
    patterns = [re.compile(p, re.IGNORECASE) for p in spec["banned_patterns"]]
    return names, patterns


def ban_violations(families: list[Family], names: list[str], patterns: list[re.Pattern]) -> list[str]:
    problems = []
    for fam in families:
        texts = [fam.key, *fam.names, *(n.replace("_", " ") for n in fam.names), *fam.tasks]
        for text in texts:
            for pat in patterns:
                if pat.search(text):
                    problems.append(f"{fam.key}: {text!r} matches banned pattern {pat.pattern!r}")
        for name in fam.names:
            if name in names:
                problems.append(f"{fam.key}: uses held-out function name {name!r}")
    return problems


# --------------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------------

def vary_task(task: str, rng: random.Random, kind: str) -> str:
    first, _, rest = task.partition(" ")
    if kind == "function" and first in THIRD_PERSON and rng.random() < 0.2:
        return f"{rng.choice(LEADS)} {THIRD_PERSON[first]} {rest}"
    return task


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def format_example(task: str, code: str, rng: random.Random, instruct_frac: float) -> tuple[str, str]:
    if rng.random() < instruct_frac:
        return "instruct", f"<task>\n{task}\n</task>\n<code>\n{code}</code>\n"
    r = rng.random()
    if r < 0.35:
        return "plain", code
    if r < 0.70:
        return "comment", f"# {task}\n{code}"
    return "task_comment", f"# Task: {lower_first(task)}\n{code}"


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-family", type=int, default=200, help="max unique examples per task family")
    parser.add_argument("--examples", type=int, default=None, help="approximate total; overrides --per-family")
    parser.add_argument("--instruct-frac", type=float, default=0.6, help="share of <task>/<code> examples")
    parser.add_argument("--doc-prob", type=float, default=0.05, help="share of functions with a docstring")
    parser.add_argument("--hint-prob", type=float, default=0.15, help="share of functions with type hints")
    parser.add_argument("--val-frac", type=float, default=0.08, help="share of task families held out for validation")
    parser.add_argument("--val-families", default="", help="comma-separated family keys to hold out (overrides --val-frac)")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out", default="data/curriculum")
    parser.add_argument("--skip-verify", action="store_true")
    args = parser.parse_args()

    families = list(FAMILIES)
    keys = [f.key for f in families]
    if len(keys) != len(set(keys)):
        raise SystemExit("duplicate family keys")
    all_names = [n for f in families for n in f.names]
    dupes = [n for n, c in Counter(all_names).items() if c > 1]
    if dupes:
        raise SystemExit(f"function names shared across families: {dupes}")

    heldout_names, banned = load_heldout()
    problems = ban_violations(families, heldout_names, banned)
    if problems:
        raise SystemExit("held-out contamination in curriculum families:\n  " + "\n  ".join(problems))

    if not args.skip_verify:
        errors = verify(families)
        if errors:
            raise SystemExit(f"{len(errors)} template verification errors:\n\n" + "\n\n".join(errors[:20]))
        print(f"verified {len(families)} families ({sum(len(f.impls) for f in families)} implementations)")

    per_family = args.per_family
    if args.examples:
        per_family = math.ceil(args.examples / len(families))

    rng = random.Random(args.seed)
    if args.val_families:
        val_keys = set(args.val_families.split(","))
        unknown = val_keys - set(keys)
        if unknown:
            raise SystemExit(f"unknown --val-families: {sorted(unknown)}")
    else:
        candidates = sorted(f.key for f in families if f.kind == "function")
        val_keys = set(rng.sample(candidates, max(1, round(len(candidates) * args.val_frac))))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("curriculum_*.py"):  # Phase 2 output format
        old.unlink()

    seen: set[str] = set()
    records = []
    per_family_counts: dict[str, int] = {}
    formats = Counter()
    name_re = re.compile(r"\bdef\s+(" + "|".join(map(re.escape, heldout_names)) + r")\s*\(")

    for fam in families:
        made, attempts = 0, 0
        while made < per_family and attempts < per_family * 12:
            attempts += 1
            r = render(fam, rng, hint_prob=args.hint_prob, doc_prob=args.doc_prob)
            if r is None:
                continue
            key = canonical_code(r.code)
            if key in seen:
                continue
            task = vary_task(r.task, rng, fam.kind)
            if name_re.search(r.code) or any(p.search(task) for p in banned):
                continue
            seen.add(key)
            fmt, text = format_example(task, r.code, rng, args.instruct_frac)
            formats[fmt] += 1
            records.append({
                "id": f"{fam.key}-{made:04d}",
                "family": fam.key,
                "topic": fam.topic,
                "split": "val" if fam.key in val_keys else "train",
                "format": fmt,
                "fn": r.fn,
                "impl": r.impl,
                "task": task,
                "code": r.code,
                "text": text,
            })
            made += 1
        per_family_counts[fam.key] = made

    rng.shuffle(records)
    jsonl = out / "curriculum.jsonl"
    with jsonl.open("w", encoding="utf-8", newline="\n") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    split_counts = Counter(r["split"] for r in records)
    total_bytes = sum(len(r["text"].encode("utf-8")) for r in records)
    stats = {
        "seed": args.seed,
        "per_family": per_family,
        "families": len(families),
        "examples": len(records),
        "text_bytes": total_bytes,
        "splits": dict(split_counts),
        "formats": dict(formats),
        "topics": dict(Counter(r["topic"] for r in records)),
        "val_families": sorted(val_keys),
        "per_family_counts": per_family_counts,
    }
    (out / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")

    thin = sorted((c, k) for k, c in per_family_counts.items() if c < per_family // 2)
    print(f"families: {len(families)} | val families: {len(val_keys)} -> {', '.join(sorted(val_keys))}")
    print(f"examples: {len(records):,} ({split_counts['train']:,} train / {split_counts['val']:,} val)")
    print(f"formats:  {dict(formats)}")
    print(f"size:     {total_bytes:,} bytes (~{total_bytes / max(1, len(records)):.0f} bytes/example)")
    if thin:
        print(f"note: {len(thin)} families have few unique variants (e.g. {thin[:5]})")
    print(f"output:   {jsonl}")


if __name__ == "__main__":
    main()
