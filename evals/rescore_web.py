"""Re-score saved website outputs with today's checks so different runs compare fairly.

    python evals/rescore_web.py evals/quality/t0_baseline.json evals/quality/t0_medium.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opcoda.codegen import check  # noqa: E402

for path in sys.argv[1:]:
    rows = json.loads(Path(path).read_text(encoding="utf-8")).get("web", [])
    ok = 0
    print(f"== {path}")
    for row in rows:
        report = check(row["source"], row["lang"]) if row["source"] else None
        failed = [c.name for c in report.checks if not c.ok] if report else ["no output"]
        passed = report is not None and report.ok and row["finished"]
        ok += passed
        print(f"  {'OK  ' if passed else 'FAIL'} {row['lang']:10s} {row['lines']:4d} lines {row['seconds']:6.1f}s "
              f"{'' if row['finished'] else '[cut off] '}{', '.join(failed)}")
    print(f"  {ok}/{len(rows)} pass every check")
