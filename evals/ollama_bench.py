"""Run CodaBench's held-out Python tasks through the local Ollama backend."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["CODA_BACKEND"] = "ollama"

from evals.coda_bench import load_tasks, score  # noqa: E402
from server import GenerateRequest, generate_ollama, OLLAMA_MODEL  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="evals/ollama_results.json")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    tasks = load_tasks()[:args.limit or None]
    rows = []
    for task in tasks:
        request = GenerateRequest(prompt=f"{task['description']} Use this exact signature: {task['signature']}",
                                  language="python", temperature=0, max_tokens=300)
        reply = generate_ollama(request)
        result = score(task, reply["text"], functional=True)
        rows.append({"task": task["name"], "syntax": result["syntax"],
                     "functional": result["functional"], "source": reply["text"]})
        print(f"{task['name']}: syntax={result['syntax']} tests={result['functional']['status'] if result['functional'] else 'not run'}", flush=True)
    summary = {"model": OLLAMA_MODEL, "tasks": len(rows),
               "syntax": sum(row["syntax"] for row in rows),
               "functional": sum(bool(row["functional"] and row["functional"]["status"] == "passed") for row in rows)}
    Path(args.out).write_text(json.dumps({"summary": summary, "details": rows}, indent=2), encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
