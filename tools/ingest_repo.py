"""Copy Python files from a local, reviewed repository into data/imported/<name>/.

Nothing is downloaded. You must state the license and revision so provenance
survives even though the copied code is gitignored:

    python tools/ingest_repo.py C:\\path\\to\\repo --name SOURCE_NAME --license MIT --revision v1.2.3

Writes data/imported/<name>/SOURCE.json (tracked by git) next to the copied
files. prepare_data.py picks the files up, de-duplicates them, splits them by
file, and drops anything that defines a CodaBench held-out function.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKIP_PARTS = {
    ".git", ".venv", "venv", "env", "__pycache__", "node_modules", "dist", "build", "site-packages",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".eggs",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo", help="path to a local repository checkout")
    parser.add_argument("--name", required=True, help="short source name, e.g. cpython-docs")
    parser.add_argument("--license", required=True, help="SPDX license id you verified, e.g. MIT, BSD-3-Clause, PSF-2.0")
    parser.add_argument("--revision", required=True, help="commit hash or tag that was copied")
    parser.add_argument("--max-file-kb", type=int, default=256)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    src = Path(args.repo).resolve()
    if not src.is_dir():
        raise SystemExit(f"not a directory: {src}")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.name):
        raise SystemExit("--name may only contain letters, digits, '.', '_' and '-'")

    heldout = json.loads((REPO / "evals" / "heldout_tasks.json").read_text(encoding="utf-8"))
    heldout_def = re.compile(r"\bdef\s+(" + "|".join(t["name"] for t in heldout["tasks"]) + r")\s*\(")

    dest = REPO / "data" / "imported" / args.name
    files, skipped, flagged = [], 0, []
    for path in sorted(src.rglob("*.py")):
        rel = path.relative_to(src)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        raw = path.read_bytes()
        if not raw or len(raw) > args.max_file_kb * 1024:
            skipped += 1
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            skipped += 1
            continue
        if heldout_def.search(text):
            flagged.append(rel.as_posix())
        files.append({"path": rel.as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        if not args.dry_run:
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)

    source = {
        "name": args.name,
        "license": args.license,
        "revision": args.revision,
        "origin_path": str(src),
        "imported_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "file_count": len(files),
        "total_bytes": sum(f["bytes"] for f in files),
        "files": files,
    }
    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "SOURCE.json").write_text(json.dumps(source, indent=2), encoding="utf-8")

    print(f"{'would copy' if args.dry_run else 'copied'} {len(files)} files ({source['total_bytes']:,} bytes), skipped {skipped}")
    if flagged:
        print(f"warning: {len(flagged)} files define CodaBench function names; prepare_data.py will drop them: {flagged[:5]}")
    print(f"destination: {dest}")


if __name__ == "__main__":
    main()
