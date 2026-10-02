"""Build Coda's byte-token training/validation streams.

Inputs:
- data/curriculum/curriculum.jsonl from tools/make_python_curriculum.py
  (train/val split is already decided per *task family* by the generator);
- optional .py files under data/raw and data/imported (split per file).

Outputs (in --out, default data/):
- train.bin / val.bin / val_iid.bin       uint8 byte-token streams
- train_offsets.npy / val_offsets.npy ... start offset of every example, used
                                          by train.py for example-aligned windows
- dataset_manifest.json                   counts, hashes, contamination report

Validation sets:
- val      = held-out task families (unseen tasks). train.py early-stops on it.
- val_iid  = held-out examples of training families. The gap between train and
             val_iid shows plain memorisation; val_iid vs val shows how well
             skills transfer to new tasks.

Every record is checked against evals/heldout_tasks.json; anything that
defines a CodaBench function, matches a banned pattern, or reproduces a
reference solution is dropped and reported.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import re
from pathlib import Path

import numpy as np

DEFAULT_ROOTS = ["data/raw", "data/imported"]
DEFAULT_CURRICULUM = "data/curriculum/curriculum.jsonl"
HELDOUT = Path("evals/heldout_tasks.json")
ALLOWED = {".py"}
SKIP_PARTS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
}
NUMBERED_DEF = re.compile(r"^def \w+?_\d+\(", re.MULTILINE)
ANY_DEF = re.compile(r"^def \w+\(", re.MULTILINE)


def iter_files(roots: list[Path]):
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in ALLOWED:
                continue
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            yield path


def read_clean(path: Path, max_file_bytes: int) -> bytes | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if not raw or len(raw) > max_file_bytes:
        return None
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return raw.replace(b"\r\n", b"\n")


def is_numbered_clone_file(text: str) -> bool:
    """Files like add_0/add_1/add_2... teach memorisation, not programming."""
    defs = len(ANY_DEF.findall(text))
    return defs >= 6 and len(NUMBERED_DEF.findall(text)) / defs > 0.5


def wrap_file(path: Path, raw: bytes) -> bytes:
    # Only the file name (not the full local path) so the model doesn't waste
    # capacity memorising directory noise.
    return f"# <coda_file:{path.name}>\n".encode("utf-8") + raw.rstrip(b"\n") + b"\n# </coda_file>\n"


def normalize_code(code: str) -> str:
    try:
        return ast.dump(ast.parse(code))
    except SyntaxError:
        return " ".join(code.split())


def function_bodies(code: str) -> list[str]:
    """Normalised bodies of top-level functions (names/signatures ignored)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return [ast.dump(ast.Module(body=node.body, type_ignores=[]))
            for node in tree.body if isinstance(node, ast.FunctionDef)]


class ContaminationGuard:
    def __init__(self, spec_path: Path):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        names = [t["name"] for t in spec["tasks"]]
        self.def_re = re.compile(r"\bdef\s+(" + "|".join(map(re.escape, names)) + r")\s*\(")
        self.patterns = [re.compile(p, re.IGNORECASE) for p in spec["banned_patterns"]]
        self.reference_bodies = {b for t in spec["tasks"] for b in function_bodies(t["reference"])}
        self.spec_sha256 = hashlib.sha256(spec_path.read_bytes()).hexdigest()

    def check(self, text: str, task: str | None, code: str | None) -> str | None:
        hit = self.def_re.search(text)
        if hit:
            return f"defines held-out function {hit.group(1)}"
        if task is not None:
            for pat in self.patterns:
                if pat.search(task):
                    return f"task matches banned pattern {pat.pattern!r}"
        if code is not None and self.reference_bodies & set(function_bodies(code)):
            return "reproduces a held-out reference solution"
        return None


def write_split(out_dir: Path, name: str, texts: list[bytes]) -> dict:
    offsets = np.zeros(len(texts), dtype=np.int64)
    pos = 0
    for i, t in enumerate(texts):
        offsets[i] = pos
        pos += len(t) + 1
    blob = b"\n".join(texts) + b"\n" if texts else b""
    np.frombuffer(blob, dtype=np.uint8).tofile(out_dir / f"{name}.bin")
    np.save(out_dir / f"{name}_offsets.npy", offsets)
    return {"examples": len(texts), "bytes": len(blob), "tokens": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}


def write_token_split(out_dir: Path, name: str, sequences: list[list[int]]) -> dict:
    """BPE mode: every example is already encoded (and ends with a newline token)."""
    offsets = np.zeros(len(sequences), dtype=np.int64)
    pos = 0
    for i, ids in enumerate(sequences):
        offsets[i] = pos
        pos += len(ids)
    flat = np.fromiter((t for ids in sequences for t in ids), dtype=np.uint16, count=pos)
    flat.tofile(out_dir / f"{name}.bin")
    np.save(out_dir / f"{name}_offsets.npy", offsets)
    return {"examples": len(sequences), "tokens": int(pos), "sha256": hashlib.sha256(flat.tobytes()).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--curriculum", default=DEFAULT_CURRICULUM)
    parser.add_argument("--roots", nargs="*", default=DEFAULT_ROOTS, help="directories of .py files")
    parser.add_argument("--out", default="data")
    parser.add_argument("--val-fraction", type=float, default=0.08, help="file-level val share for .py roots")
    parser.add_argument("--iid-fraction", type=float, default=0.03, help="share of train-family examples held out as val_iid")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--max-file-kb", type=int, default=256)
    parser.add_argument("--tokenizer", default=None, help="BPE tokenizer JSON (e.g. tokenizer/coda-bpe-4k.json); omit for byte tokens")
    parser.add_argument("--max-tokens", type=int, default=0, help="drop examples longer than this many tokens (0 = keep all)")
    args = parser.parse_args()

    if not 0.0 <= args.val_fraction <= 0.30:
        raise SystemExit("--val-fraction must be between 0 and 0.30")

    guard = ContaminationGuard(HELDOUT)
    rng = random.Random(args.seed)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    dropped = {"duplicate": 0, "contaminated": 0, "numbered_clones": 0, "cross_split_leak": 0}
    contamination_log: list[str] = []
    splits: dict[str, list[dict]] = {"train": [], "val": [], "val_iid": []}

    # ---- curriculum examples (split decided per family by the generator)
    curriculum = Path(args.curriculum)
    curriculum_families = {"train": set(), "val": set()}
    if curriculum.exists():
        with curriculum.open(encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                key = normalize_code(rec["code"])
                if key in seen:
                    dropped["duplicate"] += 1
                    continue
                reason = guard.check(rec["text"], rec["task"], rec["code"])
                if reason:
                    dropped["contaminated"] += 1
                    contamination_log.append(f"{rec['id']}: {reason}")
                    continue
                seen.add(key)
                curriculum_families[rec["split"]].add(rec["family"])
                splits[rec["split"]].append({"source": rec["id"], "key": key, "text": rec["text"].encode("utf-8")})
    else:
        print(f"warning: {curriculum} not found; run tools/make_python_curriculum.py first")

    # ---- raw / imported .py files (split per file)
    file_records = []
    skipped_files = []
    for path in sorted(iter_files([Path(r) for r in args.roots]), key=lambda p: p.as_posix()):
        raw = read_clean(path, args.max_file_kb * 1024)
        if raw is None:
            continue
        text = raw.decode("utf-8")
        if is_numbered_clone_file(text):
            dropped["numbered_clones"] += 1
            skipped_files.append(path.as_posix())
            continue
        key = normalize_code(text)
        if key in seen:
            dropped["duplicate"] += 1
            continue
        reason = guard.check(text, None, text)
        if reason:
            dropped["contaminated"] += 1
            contamination_log.append(f"{path.as_posix()}: {reason}")
            continue
        seen.add(key)
        file_records.append({"source": path.as_posix(), "key": key, "text": wrap_file(path, raw)})

    rng.shuffle(file_records)
    n_val_files = round(len(file_records) * args.val_fraction) if len(file_records) >= 10 else 0
    splits["val"].extend(file_records[:n_val_files])
    splits["train"].extend(file_records[n_val_files:])

    # ---- IID validation: random examples from *training* families
    rng.shuffle(splits["train"])
    curriculum_train = [r for r in splits["train"] if not r["source"].startswith(tuple(args.roots))]
    n_iid = round(len(curriculum_train) * args.iid_fraction)
    iid_ids = {id(r) for r in curriculum_train[:n_iid]}
    splits["val_iid"] = [r for r in splits["train"] if id(r) in iid_ids]
    splits["train"] = [r for r in splits["train"] if id(r) not in iid_ids]

    # ---- no identical example may appear in train and a val split
    train_keys = {r["key"] for r in splits["train"]}
    for name in ("val", "val_iid"):
        before = len(splits[name])
        splits[name] = [r for r in splits[name] if r["key"] not in train_keys]
        dropped["cross_split_leak"] += before - len(splits[name])

    if len(splits["train"]) < 100 or sum(len(r["text"]) for r in splits["train"]) < 100_000:
        raise SystemExit("Training set is too small. Run: python tools/make_python_curriculum.py")
    if not splits["val"]:
        raise SystemExit("Validation set is empty.")

    tokenizer_info = None
    if args.tokenizer:
        from opcoda.bpe import BPETokenizer
        tok = BPETokenizer.load(args.tokenizer)
        dropped["too_long"] = 0
        encoded: dict[str, list[list[int]]] = {}
        for name, recs in splits.items():
            seqs = []
            for r in recs:
                ids = tok.encode(r["text"].decode("utf-8") + "\n")
                if args.max_tokens and len(ids) > args.max_tokens:
                    dropped["too_long"] += 1
                    continue
                seqs.append(ids)
            encoded[name] = seqs
        stats = {name: write_token_split(out_dir, name, seqs) for name, seqs in encoded.items()}
        tokenizer_info = {"type": "bpe", "path": Path(args.tokenizer).as_posix(), "vocab_size": tok.vocab_size,
                          "sha256": hashlib.sha256(Path(args.tokenizer).read_bytes()).hexdigest()}
    else:
        stats = {name: write_split(out_dir, name, [r["text"] for r in recs]) for name, recs in splits.items()}

    manifest = {
        "format": "coda-phase4" if tokenizer_info else "coda-phase3",
        "tokenizer": tokenizer_info or {"type": "bytes", "vocab_size": 256},
        "dtype": "uint16" if tokenizer_info else "uint8",
        "max_tokens": args.max_tokens,
        "seed": args.seed,
        "curriculum": str(curriculum),
        "roots": list(args.roots),
        "heldout_spec_sha256": guard.spec_sha256,
        "splits": stats,
        "val_families": sorted(curriculum_families["val"]),
        "train_family_count": len(curriculum_families["train"]),
        "files": {
            "train": sorted(r["source"] for r in splits["train"] if r["source"].endswith(".py")),
            "val": sorted(r["source"] for r in splits["val"] if r["source"].endswith(".py")),
            "skipped_numbered_clones": skipped_files,
        },
        "dropped": dropped,
        "contamination_examples": contamination_log[:50],
    }
    (out_dir / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    unit = "BPE tokens" if tokenizer_info else "byte-tokens"
    for name, s in stats.items():
        print(f"{name:8} {s['examples']:>7,} examples | {s['tokens']:>10,} {unit}")
    print(f"val families (unseen tasks): {len(curriculum_families['val'])}")
    print(f"dropped: {dropped}")
    if skipped_files:
        print(f"skipped numbered-clone files: {skipped_files}")
    if contamination_log:
        print(f"contamination examples: {contamination_log[:5]}")
    print(f"manifest: {out_dir / 'dataset_manifest.json'}")


if __name__ == "__main__":
    main()
