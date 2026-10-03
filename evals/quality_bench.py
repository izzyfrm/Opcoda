"""Measure the serving backend (server.py, Ollama) on harder tasks.

    python evals/quality_bench.py --model qwen2.5-coder:3b --mode medium --out evals/quality_qwen.json
    python evals/quality_bench.py --web            # also score the website prompts

Python: 24 tasks from evals/quality_tasks.json. The reply goes through the same code path
as the website (generate_ollama), then the target function plus its imports and helper
functions are run against hidden tests in evals/sandbox.py (module mode: separate
interpreter, OS limits, allowlisted pure-stdlib imports only).

Web: a few page/app prompts scored by the server's own static checks. Nothing is executed.
"""
import argparse
import ast
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WEB_PROMPTS = [
    ("html", "Build a to-do app with add, complete, delete, a filter for all/active/done, and tasks saved in localStorage."),
    ("html", "Make a landing page for a bike repair shop with a hero, services, prices table, opening hours and a contact form."),
    ("html", "Create a tip calculator page: bill amount, tip percentage buttons, number of people, and per-person totals that update live."),
    ("css", "Style a responsive pricing section with three plan cards, the middle one highlighted."),
    ("javascript", "Write a debounce function and a throttle function with JSDoc, plus a short demo that logs when they fire."),
    ("html", "Build a quiz page with five multiple-choice questions, a score at the end and a restart button."),
]


def program_part(code: str, name: str) -> str:
    """Keep imports, functions and classes; drop demos and top-level calls."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    keep = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
    return "\n\n".join(ast.get_source_segment(code, n) for n in keep) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="Ollama model (default: the server default)")
    parser.add_argument("--mode", default="medium", choices=["light", "medium", "super", "intense"])
    parser.add_argument("--out", default="evals/quality_results.json")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--web", action="store_true", help="also run the website prompts")
    parser.add_argument("--web-only", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.0, help="0 = repeatable comparisons")
    parser.add_argument("--server", default="server.py", help="server module file to test (e.g. an older snapshot)")
    args = parser.parse_args()
    os.environ["CODA_BACKEND"] = "ollama"
    if args.model:
        os.environ["CODA_OLLAMA_MODEL"] = args.model

    import importlib.util
    spec = importlib.util.spec_from_file_location("server", ROOT / args.server)
    server = importlib.util.module_from_spec(spec)
    sys.modules["server"] = server
    spec.loader.exec_module(server)  # reads the environment at import
    from evals import sandbox  # noqa: E402

    tokens = {"light": 256, "medium": 450, "super": 650, "intense": 900}[args.mode]
    tasks = json.loads((ROOT / "evals" / "quality_tasks.json").read_text(encoding="utf-8"))["tasks"]
    tasks = tasks[: args.limit or None]
    rows, web_rows = [], []
    started_all = time.perf_counter()
    if not args.web_only:
        for task in tasks:
            req = server.GenerateRequest(prompt=f"{task['description']} Use this exact signature: {task['signature']}",
                                         language="python", temperature=args.temperature, max_tokens=tokens)
            t0 = time.perf_counter()
            try:
                reply = server.generate_ollama(req)
            except Exception as exc:  # noqa: BLE001 - a timeout or crash counts as a failed task
                reply = {"text": "", "syntax_ok": False, "error": str(getattr(exc, "detail", exc))[:200]}
            seconds = time.perf_counter() - t0
            source = program_part(reply["text"], task["name"])
            result = sandbox.run_tests(source, task["name"], task["tests"], task.get("compare"), module=True)
            ok = result["status"] == "passed"
            rows.append({"task": task["name"], "passed": ok, "status": result["status"], "tests": f"{result['passed']}/{result['total']}",
                         "detail": result.get("detail", ""), "seconds": round(seconds, 1), "checks_ok": reply["syntax_ok"],
                         "rounds": reply.get("rounds"), "source": reply["text"]})
            print(f"{task['name']:24s} {'PASS' if ok else 'fail'} {result['passed']}/{result['total']} {result['status']:8s} {seconds:5.1f}s",
                  flush=True)
    if args.web or args.web_only:
        for lang, prompt in WEB_PROMPTS:
            req = server.GenerateRequest(prompt=prompt, language=lang, temperature=args.temperature, max_tokens=tokens)
            t0 = time.perf_counter()
            try:
                reply = server.generate_ollama(req)
            except Exception as exc:  # noqa: BLE001
                reply = {"text": "", "syntax_ok": False, "finished": False,
                         "checks": {"checks": [{"name": "Generation", "ok": False, "detail": str(getattr(exc, "detail", exc))[:200]}]}}
            seconds = time.perf_counter() - t0
            failed = [c["name"] + (": " + c["detail"] if c.get("detail") else "") for c in reply["checks"]["checks"] if not c["ok"]]
            web_rows.append({"prompt": prompt, "lang": lang, "ok": reply["syntax_ok"] and reply["finished"], "finished": reply["finished"],
                             "failed_checks": failed, "lines": reply["text"].count("\n"), "seconds": round(seconds, 1),
                             "rounds": reply.get("rounds"), "source": reply["text"]})
            print(f"web {lang:10s} {'OK  ' if web_rows[-1]['ok'] else 'FAIL'} {web_rows[-1]['lines']:4d} lines {seconds:5.1f}s {failed[:2]}", flush=True)
    summary = {"model": server.OLLAMA_MODEL, "mode": args.mode,
               "python_passed": sum(r["passed"] for r in rows), "python_total": len(rows),
               "web_ok": sum(r["ok"] for r in web_rows), "web_total": len(web_rows),
               "minutes": round((time.perf_counter() - started_all) / 60, 1)}
    Path(args.out).write_text(json.dumps({"summary": summary, "python": rows, "web": web_rows}, indent=1), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
