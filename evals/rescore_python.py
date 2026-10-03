"""Re-run the hidden tests on saved Python answers (no generation), e.g. after a sandbox fix.

    python evals/rescore_python.py evals/quality/t0_*.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evals import sandbox  # noqa: E402
from evals.quality_bench import program_part  # noqa: E402

tasks = {t["name"]: t for t in json.loads((ROOT / "evals" / "quality_tasks.json").read_text(encoding="utf-8"))["tasks"]}
for path in sys.argv[1:]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data.get("python", [])
    if not rows:
        continue
    passed, failed = 0, []
    for row in rows:
        task = tasks[row["task"]]
        res = sandbox.run_tests(program_part(row["source"], task["name"]), task["name"], task["tests"], task.get("compare"), module=True)
        ok = res["status"] == "passed"
        passed += ok
        if not ok:
            failed.append(f"{row['task']}({res['status']})")
    secs = sum(r["seconds"] for r in rows) / len(rows)
    print(f"{Path(path).stem:14s} {passed:2d}/{len(rows)}  avg {secs:5.1f}s  failed: {', '.join(failed)}")
