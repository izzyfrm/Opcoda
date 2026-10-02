from pathlib import Path
import argparse
import numpy as np

ALLOWED = {".py", ".js", ".mjs", ".cjs", ".html", ".css", ".json", ".md", ".txt"}


def collect(root: Path) -> bytes:
    chunks: list[bytes] = []
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in ALLOWED)
    for path in files:
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        if not raw:
            continue
        marker = f"\n\n# <file:{path.as_posix()}>\n".encode("utf-8")
        chunks.extend((marker, raw, b"\n# </file>\n"))
    return b"".join(chunks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="data/raw")
    parser.add_argument("--out", default="data")
    parser.add_argument("--val-fraction", type=float, default=0.05)
    args = parser.parse_args()

    raw_dir = Path(args.raw)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    blob = collect(raw_dir)
    if len(blob) < 10_000:
        raise SystemExit(
            "Not enough training text. Add your own or permissively licensed code to data/raw first."
        )

    data = np.frombuffer(blob, dtype=np.uint8)
    split = max(1, int(len(data) * (1.0 - args.val_fraction)))
    train, val = data[:split], data[split:]
    train.tofile(out_dir / "train.bin")
    val.tofile(out_dir / "val.bin")

    print(f"Prepared {len(data):,} byte-tokens")
    print(f"train: {len(train):,} | val: {len(val):,}")


if __name__ == "__main__":
    main()
