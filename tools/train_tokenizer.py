"""Train Opcoda's BPE tokenizer on the curriculum (train split only).

    python tools/train_tokenizer.py --vocab 4096

Writes tokenizer/coda-bpe-4k.json and prints how many bytes one token covers on the
validation split (higher = more code fits in Coda's context window).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from opcoda.bpe import train_bpe  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--curriculum", default="data/curriculum_v4/curriculum.jsonl")
    parser.add_argument("--vocab", type=int, default=4096)
    parser.add_argument("--sample-mb", type=float, default=24.0, help="train on at most this much text")
    parser.add_argument("--out", default="tokenizer/coda-bpe-4k.json")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    train, val = [], []
    with open(REPO / args.curriculum, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            (val if rec["split"] == "val" else train).append(rec["text"])
    rng = random.Random(args.seed)
    rng.shuffle(train)
    budget, sample = int(args.sample_mb * 1e6), []
    for text in train:
        if budget <= 0:
            break
        sample.append(text)
        budget -= len(text)

    started = time.time()
    tok = train_bpe(sample, args.vocab, verbose=True)
    print(f"trained {tok.vocab_size} tokens on {sum(map(len, sample)) / 1e6:.1f} MB in {time.time() - started:.0f}s")

    probe = rng.sample(val, min(500, len(val)))
    n_bytes = sum(len(t.encode("utf-8")) for t in probe)
    n_tokens = sum(len(tok.encode(t)) for t in probe)
    assert all(tok.decode(tok.encode(t)) == t for t in probe[:50]), "round trip failed"
    print(f"validation: {n_bytes / n_tokens:.2f} bytes per token (byte-level = 1.00)")
    tok.save(REPO / args.out)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
