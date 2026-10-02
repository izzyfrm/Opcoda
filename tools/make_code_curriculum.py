"""Generate Coda's Phase 4 multi-language curriculum (HTML, CSS, JavaScript, Python).

Every example is an instruction followed by a complete file:

    <task>
    Build a landing page for Bean & Brew, a coffee shop in Portland. Include ...
    </task>
    <code lang="html">
    <!DOCTYPE html>
    ...
    </code>

Quality gates (an example is dropped if any fails):
- opcoda.verify static checks for its language (tags, CSS declarations, JS syntax,
  Python syntax and undefined names);
- Python programs are executed (they are our own templates, never model output) and
  must finish without errors; their real printed output may be appended as comments;
- JavaScript functions run in Node; all implementations of a family must agree, and the
  example calls in the code carry the real result Node computed;
- CodaBench held-out tasks and banned phrasings never appear.

Usage:
    python tools/make_code_curriculum.py              # ~60 MB, a few minutes
    python tools/make_code_curriculum.py --scale 0.2  # quick smoke run
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import random
import re
import shutil
import subprocess
import sys
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from curriculum_families import FAMILIES as PY_FUNCTION_FAMILIES  # noqa: E402
from js_families import JS_FUNCTIONS, JS_PROGRAMS  # noqa: E402
from make_python_curriculum import load_heldout, render  # noqa: E402
from opcoda.verify import _HTMLChecker, check  # noqa: E402
from program_families import PROGRAMS, make_composed_module  # noqa: E402
from web_families import FAMILIES as WEB_FAMILIES  # noqa: E402

# examples per family, by group (multiplied by --scale)
TARGETS = {"html-page": 520, "html-app": 260, "css": 220, "js-function": 140, "js-program": 50,
           "py-program": 260, "py-module": 2600, "py-function": 9000}

NODE_RUNNER = r"""
const tasks = JSON.parse(require("fs").readFileSync(0, "utf8"));
const out = [];
for (const task of tasks) {
  const logs = [];
  const fakeConsole = { log: (...a) => logs.push(a.map((x) => typeof x === "string" ? x : JSON.stringify(x)).join(" ")),
                        error: () => {}, warn: () => {} };
  try {
    if (task.kind === "call") {
      const fn = new Function("console", task.code + "\nreturn " + task.fname + ";")(fakeConsole);
      const results = task.examples.map((args) => {
        const values = new Function("return [" + args + "];")();
        const value = fn(...values);
        return value === undefined ? "undefined" : JSON.stringify(value);
      });
      out.push({ ok: true, results });
    } else {
      new Function("console", task.code)(fakeConsole);
      out.push({ ok: true, logs });
    }
  } catch (error) {
    out.push({ ok: false, error: String(error && error.message || error).slice(0, 200) });
  }
}
process.stdout.write(JSON.stringify(out));
"""


def run_node(tasks: list[dict]) -> list[dict]:
    node = shutil.which("node")
    if not node:
        raise SystemExit("Node.js is required to validate the JavaScript curriculum (https://nodejs.org).")
    results: list[dict] = []
    for i in range(0, len(tasks), 2000):
        batch = tasks[i:i + 2000]
        proc = subprocess.run([node, "-e", NODE_RUNNER], input=json.dumps(batch), capture_output=True,
                              text=True, encoding="utf-8", timeout=600)
        if proc.returncode != 0:
            raise SystemExit(f"node runner failed: {proc.stderr[:500]}")
        results.extend(json.loads(proc.stdout))
    return results


def run_python(code: str) -> tuple[bool, str]:
    """Execute one of our own program templates and capture what it prints."""
    buffer = io.StringIO()
    namespace = {"__name__": "__main__"}
    try:
        with contextlib.redirect_stdout(buffer):
            exec(compile(code, "<program>", "exec"), namespace)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    return True, buffer.getvalue()


def normalize(code: str) -> str:
    return re.sub(r"\s+", " ", code).strip()


def fmt(task: str, lang: str, code: str) -> str:
    return f"<task>\n{task}\n</task>\n<code lang=\"{lang}\">\n{code.rstrip(chr(10))}\n</code>\n"


def js_literal_comment(result: str) -> str:
    return result if len(result) <= 80 else result[:77] + "..."


# ---------------------------------------------------------------------------
# Generators per group. Each yields (family_key, group, lang, task, code, extra)
# ---------------------------------------------------------------------------

def gen_web(rng, fam, count, out):
    group = "css" if fam.lang == "css" else ("html-app" if fam.topic == "apps" else "html-page")
    for _ in range(count):
        task, code = fam.make(rng)
        out.append({"family": fam.key, "group": group, "lang": fam.lang, "task": task, "code": code})


def gen_js_functions(rng, count_per, out):
    for fam in JS_FUNCTIONS:
        for _ in range(count_per):
            name = rng.choice(fam.names)
            params = rng.choice(fam.params)
            variant = rng.choice(fam.variants)
            code = variant.replace("@fn@", name)
            task = rng.choice(fam.tasks)
            for i, p in enumerate(params):
                code = code.replace(f"@p{i}@", p)
                task = task.replace(f"@p{i}@", p)
            examples = list(fam.examples)
            if fam.deterministic and examples:
                shown = rng.sample(examples, rng.choice([1, 2, min(3, len(examples))]))
            else:
                shown = []
            out.append({"family": fam.key, "group": "js-function", "lang": "javascript", "task": task,
                        "code": code + "\n", "fname": name, "examples": shown, "deterministic": fam.deterministic})


def gen_js_programs(rng, count_per, out):
    for fam in JS_PROGRAMS:
        for _ in range(count_per):
            task, code, runnable = fam.make(rng)
            out.append({"family": fam.key, "group": "js-program", "lang": "javascript", "task": task, "code": code,
                        "runnable": runnable})


def gen_py_programs(rng, count_per, out):
    for fam in PROGRAMS:
        for _ in range(count_per):
            task, code = fam.make(rng)
            out.append({"family": fam.key, "group": "py-program", "lang": "python", "task": task, "code": code})


def gen_py_modules(rng, count, families, out):
    made = 0
    while made < count:
        result = make_composed_module(families, lambda f, r: render(f, r, hint_prob=0.15, doc_prob=0.1), rng)
        if result:
            out.append({"family": "py_module", "group": "py-module", "lang": "python", "task": result[0], "code": result[1]})
            made += 1


def gen_py_functions(rng, count, families, out):
    fams = [f for f in families if f.kind == "function"] + [f for f in families if f.kind == "class"]
    for i in range(count):
        fam = fams[i % len(fams)]
        rendered = render(fam, rng, hint_prob=0.15, doc_prob=0.05)
        if rendered:
            out.append({"family": fam.key, "group": "py-function", "lang": "python", "task": rendered.task,
                        "code": rendered.code})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scale", type=float, default=1.0, help="multiply every per-family target")
    parser.add_argument("--val-frac", type=float, default=0.1, help="share of families (per group) held out for validation")
    parser.add_argument("--output-comment-prob", type=float, default=0.4, help="share of Python programs ending with their real output")
    parser.add_argument("--derive-css", type=float, default=0.15, help="share of pages also used as a CSS-only example")
    parser.add_argument("--derive-js", type=float, default=0.3, help="share of apps also used as a JavaScript-only example")
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--out", default="data/curriculum_v4")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    targets = {k: max(1, math.ceil(v * args.scale)) for k, v in TARGETS.items()}
    heldout_names, banned = load_heldout()
    def_re = re.compile(r"\bdef\s+(" + "|".join(map(re.escape, heldout_names)) + r")\s*\(")

    # ---- validation families (whole tasks never seen in training)
    groups: dict[str, list[str]] = defaultdict(list)
    for f in WEB_FAMILIES:
        groups["css" if f.lang == "css" else ("html-app" if f.topic == "apps" else "html-page")].append(f.key)
    groups["js-function"] = [f.key for f in JS_FUNCTIONS if f.deterministic]
    groups["js-program"] = [f.key for f in JS_PROGRAMS]
    groups["py-program"] = [f.key for f in PROGRAMS]
    groups["py-function"] = [f.key for f in PY_FUNCTION_FAMILIES if f.kind == "function"]
    val_keys = set()
    for group, keys in groups.items():
        val_keys.update(rng.sample(sorted(keys), max(1, round(len(keys) * args.val_frac))))
    train_py_families = [f for f in PY_FUNCTION_FAMILIES if f.key not in val_keys]

    # ---- generate raw candidates
    raw: list[dict] = []
    for fam in WEB_FAMILIES:
        group = "css" if fam.lang == "css" else ("html-app" if fam.topic == "apps" else "html-page")
        gen_web(rng, fam, targets[group], raw)
    gen_js_functions(rng, targets["js-function"], raw)
    gen_js_programs(rng, targets["js-program"], raw)
    gen_py_programs(rng, targets["py-program"], raw)
    gen_py_modules(rng, targets["py-module"], train_py_families, raw)
    gen_py_functions(rng, targets["py-function"], PY_FUNCTION_FAMILIES, raw)
    print(f"generated {len(raw):,} raw candidates")

    # ---- dedup + held-out guard
    seen: set[str] = set()
    candidates, dropped = [], Counter()
    for ex in raw:
        key = normalize(ex["code"])
        if key in seen:
            dropped["duplicate"] += 1
            continue
        seen.add(key)
        if def_re.search(ex["code"]) or any(p.search(ex["task"]) for p in banned):
            dropped["held_out"] += 1
            continue
        candidates.append(ex)

    # ---- JavaScript: run functions/programs in Node, syntax-check everything at once
    js_tasks, js_index = [], []
    for i, ex in enumerate(candidates):
        if ex["group"] == "js-function" and ex["deterministic"] and ex["examples"]:
            js_tasks.append({"kind": "call", "code": ex["code"], "fname": ex["fname"], "examples": ex["examples"]})
            js_index.append(i)
        elif ex["group"] == "js-program" and ex.get("runnable"):
            js_tasks.append({"kind": "run", "code": ex["code"]})
            js_index.append(i)
    # family-level agreement: every variant must give the same results on every example
    agree_tasks, agree_meta = [], []
    for fam in JS_FUNCTIONS:
        if not fam.deterministic:
            continue
        for v in fam.variants:
            code = v.replace("@fn@", fam.names[0])
            for j, p in enumerate(fam.params[0]):
                code = code.replace(f"@p{j}@", p)
            agree_tasks.append({"kind": "call", "code": code, "fname": fam.names[0], "examples": list(fam.examples)})
            agree_meta.append(fam.key)
    results = run_node(js_tasks + agree_tasks)
    by_family = defaultdict(list)
    for key, res in zip(agree_meta, results[len(js_tasks):]):
        by_family[key].append(json.dumps(res.get("results")) if res.get("ok") else "error:" + res.get("error", ""))
    bad_js_families = {k for k, outs in by_family.items() if len(set(outs)) != 1 or outs[0].startswith("error:")}
    if bad_js_families:
        print(f"warning: JS families with disagreeing variants (dropped): {sorted(bad_js_families)}")
    for i, res in zip(js_index, results[:len(js_tasks)]):
        ex = candidates[i]
        if not res.get("ok"):
            ex["reject"] = "js run: " + res.get("error", "")
        elif ex["group"] == "js-function":
            calls = [f"console.log({ex['fname']}({args})); // {js_literal_comment(r)}"
                     for args, r in zip(ex["examples"], res["results"])]
            ex["code"] = ex["code"].rstrip("\n") + "\n\n" + "\n".join(calls) + "\n"
    for ex in candidates:
        if ex["family"] in bad_js_families:
            ex["reject"] = "family variants disagree"

    # ---- static checks (one batched Node call for every script)
    scripts: list[str] = []
    for ex in candidates:
        if ex.get("reject"):
            continue
        if ex["lang"] == "javascript":
            scripts.append(ex["code"])
        elif ex["lang"] == "html":
            parser_ = _HTMLChecker()
            parser_.feed(ex["code"])
            scripts.extend(parser_.scripts)
    from opcoda.verify import check_js_many
    js_errors = dict(zip(scripts, check_js_many(scripts, timeout=600)))
    cached_js = lambda sources: [js_errors.get(s) for s in sources]  # noqa: E731

    kept: list[dict] = []
    for ex in candidates:
        if ex.get("reject"):
            dropped[ex["reject"].split(":")[0]] += 1
            continue
        if ex["lang"] == "javascript":
            error = js_errors.get(ex["code"])
            ok = error is None
            detail = error or ""
        elif ex["lang"] == "html":
            from opcoda.verify import check_html
            report = check_html(ex["code"], js_checker=cached_js)
            ok, detail = report.ok, "; ".join(f"{c.name}: {c.detail}" for c in report.checks if not c.ok)
        else:
            report = check(ex["code"], ex["lang"])
            ok, detail = report.ok, "; ".join(f"{c.name}: {c.detail}" for c in report.checks if not c.ok)
        if not ok:
            dropped[f"static:{ex['lang']}"] += 1
            if dropped[f"static:{ex['lang']}"] <= 3:
                print(f"  rejected {ex['family']}: {detail[:160]}")
            continue
        if ex["group"] in ("py-program", "py-module"):
            ran, output = run_python(ex["code"])
            if not ran:
                dropped["py run"] += 1
                if dropped["py run"] <= 3:
                    print(f"  program failed {ex['family']}: {output[:160]}")
                continue
            lines = [line for line in output.splitlines() if line.strip()]
            if lines and rng.random() < args.output_comment_prob:
                shown = lines[:10]
                ex["code"] = ex["code"].rstrip("\n") + "\n\n# Output:\n" + "\n".join(f"# {line}" for line in shown) + "\n"
        kept.append(ex)

    # ---- standalone CSS / JS derived from verified pages (valid by construction)
    derived = []
    for ex in kept:
        if ex["lang"] != "html":
            continue
        page = _HTMLChecker()
        page.feed(ex["code"])
        if page.styles and rng.random() < args.derive_css:
            css = textwrap.dedent(page.styles[0]).strip("\n") + "\n"
            task = rng.choice(["Write just the CSS for this: ", "Only the stylesheet, no HTML: ", "CSS for: "]) + ex["task"]
            derived.append({**ex, "group": "css-derived", "lang": "css", "task": task, "code": css})
        if page.scripts and ex["group"] == "html-app" and rng.random() < args.derive_js:
            js = textwrap.dedent(page.scripts[0]).strip("\n") + "\n"
            task = rng.choice(["Write the JavaScript for this: ", "Just the JS for: "]) + ex["task"]
            derived.append({**ex, "group": "js-derived", "lang": "javascript", "task": task, "code": js})
    kept.extend(derived)

    # ---- format + split
    rng.shuffle(kept)
    out_dir = REPO / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    counts, sizes, splits = Counter(), Counter(), Counter()
    with (out_dir / "curriculum.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for n, ex in enumerate(kept):
            split = "val" if ex["family"] in val_keys else "train"
            text = fmt(ex["task"], ex["lang"], ex["code"])
            record = {"id": f"{ex['family']}-{n:06d}", "family": ex["family"], "group": ex["group"], "lang": ex["lang"],
                      "split": split, "task": ex["task"], "code": ex["code"], "text": text}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            counts[ex["group"]] += 1
            sizes[ex["group"]] += len(text.encode("utf-8"))
            splits[split] += 1
    stats = {"seed": args.seed, "scale": args.scale, "examples": len(kept), "splits": dict(splits),
             "by_group": {g: {"examples": counts[g], "bytes": sizes[g]} for g in counts},
             "val_families": sorted(val_keys), "dropped": dict(dropped), "bytes": sum(sizes.values())}
    (out_dir / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"kept {len(kept):,} examples ({splits['train']:,} train / {splits['val']:,} val), {sum(sizes.values()) / 1e6:.1f} MB")
    for g in sorted(counts):
        print(f"  {g:<12} {counts[g]:>6,} examples  {sizes[g] / 1e6:6.1f} MB")
    print(f"dropped: {dict(dropped)}")
    print(f"output: {out_dir / 'curriculum.jsonl'}")


if __name__ == "__main__":
    main()
