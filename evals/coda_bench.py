"""CodaBench 0.2: held-out function-writing checks for Coda checkpoints.

The 12 tasks live in evals/heldout_tasks.json, which the curriculum generator
and prepare_data.py also read so the tasks never leak into training data.

Prompt formats (both are scored):
- instruct: "<task>\\n{description}\\n</task>\\n<code>\\n{signature}\\n"   (Phase 3 format)
- comment:  "# Task: {description}\\n{signature}\\n"                      (CodaBench 0.1 format)

Metrics:
- syntax:     the generated function (signature + body, cut at </code> or at
              the first top-level line after the body) parses with ast.
- functional: opt-in with --functional. The function runs against unit tests
              in evals/sandbox.py (static gate + separate locked-down process).
              Nothing generated is ever executed in this process.

Usage:
    python evals/coda_bench.py checkpoints/coda-phase3-best.pt
    python evals/coda_bench.py checkpoints/coda-phase3-best.pt --functional --samples 3
    python evals/coda_bench.py --self-test
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import sandbox  # noqa: E402

TASKS_PATH = HERE / "heldout_tasks.json"
STOP = {
    "instruct": ["</code>"],
    "comment": ["\n<task>", "\n# Task:", "\ndef ", "\nclass ", "</code>"],
}
CUT_MARKERS = ("</code>", "<task>", "<code>")


def load_tasks() -> list[dict]:
    return json.loads(TASKS_PATH.read_text(encoding="utf-8"))["tasks"]


def build_prompt(task: dict, fmt: str) -> str:
    desc = task["description"]
    if fmt == "instruct":
        return f"<task>\n{desc}\n</task>\n<code>\n{task['signature']}\n"
    return f"# Task: {desc[:1].lower() + desc[1:]}\n{task['signature']}\n"


def extract_function(signature: str, completion: str) -> str:
    """Signature + indented body; stops at a format marker or the first top-level line."""
    for marker in CUT_MARKERS:
        if marker in completion:
            completion = completion[: completion.index(marker)]
    kept = [signature]
    for line in completion.split("\n"):
        if line.strip() and not line[0].isspace():
            break
        kept.append(line)
    return "\n".join(kept).rstrip() + "\n"


def syntax_check(source: str, name: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return False, f"{exc.msg} (line {exc.lineno})"
    if not any(isinstance(n, ast.FunctionDef) and n.name == name for n in tree.body):
        return False, "no function definition"
    return True, "ok"


def load_model(checkpoint: str, device: str):
    import torch
    from opcoda.config import CodaConfig
    from opcoda.model import Coda

    payload = torch.load(checkpoint, map_location=device)
    model = Coda(CodaConfig(**payload["config"])).to(device)
    model.load_state_dict(payload["model"])
    model.eval()
    return model, payload


def generate(model, tok, prompt: str, fmt: str, args, seed: int, device: str) -> str:
    import torch

    torch.manual_seed(seed)
    ids = tok.encode(prompt)
    x = torch.tensor([ids], dtype=torch.long, device=device)
    y = model.generate(x, max_new_tokens=args.tokens, temperature=args.temperature, top_k=args.top_k,
                       stop=[tok.encode(s) for s in STOP[fmt]])[0].tolist()
    return tok.decode(y[len(ids):])


def score(task: dict, source: str, functional: bool) -> dict:
    ok, detail = syntax_check(source, task["name"])
    result = {"syntax": ok, "syntax_detail": detail, "functional": None}
    if functional and ok:
        result["functional"] = sandbox.run_tests(source, task["name"], task["tests"], task.get("compare"))
    return result


def self_test() -> int:
    """Validate the harness: references must pass; hostile code must be contained."""
    tasks = load_tasks()
    failures = 0
    print("reference solutions:")
    for task in tasks:
        source = extract_function(task["signature"], task["reference"].split("\n", 1)[1])
        r = score(task, source, functional=True)
        status = r["functional"]["status"]
        good = r["syntax"] and status == "passed"
        failures += not good
        print(f"  {'ok ' if good else 'BAD'} {task['name']:16} syntax={r['syntax']} functional={status}")

    probes = {
        "import": ("def f(x):\n    import os\n    return os.getcwd()\n", "rejected"),
        "dunder escape": ("def f(x):\n    return ().__class__.__mro__\n", "rejected"),
        "open file": ("def f(x):\n    return open('x.txt', 'w')\n", "rejected"),
        "eval": ("def f(x):\n    return eval('1')\n", "rejected"),
        "infinite loop": ("def f(x):\n    while True:\n        x += 1\n", ("timeout", "error")),
        "memory bomb": ("def f(x):\n    s = 'a'\n    while True:\n        s = s + s\n", ("failed", "error")),
        "wrong answer": ("def f(x):\n    return x + 1\n", "failed"),
        "correct": ("def f(x):\n    return x * 2\n", "passed"),
    }
    tests = [{"args": "(3,)", "expected": "6"}]
    print("sandbox probes:")
    for label, (source, expected) in probes.items():
        r = sandbox.run_tests(source, "f", tests)
        allowed = expected if isinstance(expected, tuple) else (expected,)
        good = r["status"] in allowed
        failures += not good
        print(f"  {'ok ' if good else 'BAD'} {label:14} -> {r['status']:8} {r.get('detail', '')}")
    print("self-test passed" if not failures else f"self-test FAILED ({failures})")
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("checkpoint", nargs="?", default="checkpoints/coda-phase3-best.pt")
    parser.add_argument("--formats", nargs="+", choices=list(STOP), default=["instruct", "comment"])
    parser.add_argument("--tokens", type=int, default=256, help="max new byte-tokens per function")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--samples", type=int, default=1, help="samples per task; headline uses sample 1")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--functional", action="store_true", help="run unit tests in the sandbox")
    parser.add_argument("--out", default="evals/codabench_results.md")
    parser.add_argument("--self-test", action="store_true", help="check the harness and sandbox, no model needed")
    args = parser.parse_args()

    if args.self_test:
        raise SystemExit(self_test())

    import torch
    from opcoda.tokenizer import ByteTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, payload = load_model(args.checkpoint, device)
    tok = ByteTokenizer()
    tasks = load_tasks()

    print(f"checkpoint: {args.checkpoint} | step {payload.get('step', '?')} | {model.parameter_count():,} params")
    print(f"tasks: {len(tasks)} | formats: {args.formats} | samples: {args.samples} | functional: {args.functional}")

    summary: dict[str, dict] = {}
    details: dict[str, list] = {}
    for fmt in args.formats:
        print(f"\n[{fmt}]")
        rows = []
        syntax_by_sample = [0] * args.samples
        func_by_sample = [0] * args.samples
        for ti, task in enumerate(tasks):
            prompt = build_prompt(task, fmt)
            samples = []
            for s in range(args.samples):
                completion = generate(model, tok, prompt, fmt, args, args.seed + 1000 * s + ti, device)
                source = extract_function(task["signature"], completion)
                r = score(task, source, args.functional)
                r["source"] = source
                samples.append(r)
                syntax_by_sample[s] += r["syntax"]
                func_by_sample[s] += bool(r["functional"] and r["functional"]["status"] == "passed")
            first = samples[0]
            func = first["functional"]
            func_txt = f" | tests {func['passed']}/{func['total']} {func['status']}" if func else ""
            extra = f" | syntax {sum(x['syntax'] for x in samples)}/{args.samples} samples" if args.samples > 1 else ""
            print(f"  {'PASS' if first['syntax'] else 'FAIL'}  {task['name']:16} {first['syntax_detail']}{func_txt}{extra}")
            rows.append({"task": task["name"], "prompt": prompt, "samples": samples})
        n = len(tasks)
        summary[fmt] = {
            "syntax": syntax_by_sample[0],
            "syntax_mean": sum(syntax_by_sample) / args.samples,
            "functional": func_by_sample[0] if args.functional else None,
            "functional_mean": sum(func_by_sample) / args.samples if args.functional else None,
            "tasks": n,
        }
        details[fmt] = rows
        line = f"  syntax: {syntax_by_sample[0]}/{n}"
        if args.samples > 1:
            line += f" (mean over {args.samples} samples: {summary[fmt]['syntax_mean']:.2f})"
        if args.functional:
            line += f" | functional: {func_by_sample[0]}/{n}"
            if args.samples > 1:
                line += f" (mean {summary[fmt]['functional_mean']:.2f})"
        print(line)

    write_report(Path(args.out), args, payload, summary, details)
    print(f"\nresults: {args.out} (+ {Path(args.out).with_suffix('.json').name})")
    print("Note: syntax validity is not correctness; read the saved functions.")


def write_report(out: Path, args, payload, summary, details) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "checkpoint": args.checkpoint,
        "step": payload.get("step"),
        "best_val": payload.get("best_val"),
        "settings": {"tokens": args.tokens, "temperature": args.temperature, "top_k": args.top_k,
                     "samples": args.samples, "seed": args.seed, "functional": args.functional},
        "summary": summary,
    }
    out.with_suffix(".json").write_text(json.dumps({**meta, "details": details}, indent=2), encoding="utf-8")

    with out.open("w", encoding="utf-8") as f:
        f.write("# CodaBench 0.2 results\n\n")
        f.write(f"- checkpoint: `{args.checkpoint}` (step {payload.get('step', '?')})\n")
        f.write(f"- sampling: temperature {args.temperature}, top-k {args.top_k}, "
                f"max {args.tokens} tokens, seed {args.seed}, samples {args.samples}\n")
        f.write("- syntax validity is not functional correctness\n\n")
        f.write(f"| format | syntax (sample 1) | syntax (mean of {args.samples}) "
                f"| functional (sample 1) | functional (mean of {args.samples}) |\n|---|---|---|---|---|\n")
        for fmt, s in summary.items():
            n = s["tasks"]
            if s["functional"] is None:
                func, func_mean = "not run", "not run"
            else:
                func, func_mean = f"{s['functional']}/{n}", f"{s['functional_mean']:.2f}/{n}"
            f.write(f"| {fmt} | {s['syntax']}/{n} | {s['syntax_mean']:.2f}/{n} | {func} | {func_mean} |\n")
        for fmt, rows in details.items():
            f.write(f"\n## Format: {fmt}\n")
            for row in rows:
                r = row["samples"][0]
                verdict = "PASS" if r["syntax"] else "FAIL"
                func = r["functional"]
                func_txt = f" — tests {func['passed']}/{func['total']} ({func['status']})" if func else ""
                f.write(f"\n### {row['task']} — syntax {verdict}{func_txt}\n\n`{r['syntax_detail']}`\n\n")
                f.write("```python\n" + r["source"] + "```\n")


if __name__ == "__main__":
    main()
