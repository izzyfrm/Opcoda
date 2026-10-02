"""Opcoda's own byte-level BPE tokenizer (trained from scratch, no external libraries).

Text is first split into chunks with a code-aware regex (identifiers with an optional
leading space, numbers, punctuation runs, and newline+indentation runs), then byte pair
merges learned on Coda's corpus are applied inside each chunk. Every byte is a token, so
any text round-trips exactly.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# newline + indentation | word | number | punctuation run | spaces/tabs | any other whitespace
PATTERN = r"\n[ \t]*| ?[A-Za-z_][A-Za-z0-9_]*| ?[0-9]+| ?[^\sA-Za-z0-9_]+|[ \t]+|\s"


class BPETokenizer:
    def __init__(self, merges: list[tuple[int, int]], pattern: str = PATTERN):
        self.pattern = pattern
        self._split = re.compile(pattern)
        self.merges = [tuple(m) for m in merges]
        self.ranks = {pair: i for i, pair in enumerate(self.merges)}
        self.vocab: list[bytes] = [bytes([i]) for i in range(256)]
        for a, b in self.merges:
            self.vocab.append(self.vocab[a] + self.vocab[b])
        self.vocab_size = len(self.vocab)
        self._cache: dict[str, list[int]] = {}

    # -- encoding -------------------------------------------------------------

    def _encode_chunk(self, chunk: str) -> list[int]:
        cached = self._cache.get(chunk)
        if cached is not None:
            return cached
        ids = list(chunk.encode("utf-8"))
        while len(ids) > 1:
            best = min(range(len(ids) - 1), key=lambda i: self.ranks.get((ids[i], ids[i + 1]), 1 << 30))
            pair = (ids[best], ids[best + 1])
            rank = self.ranks.get(pair)
            if rank is None:
                break
            new_id = 256 + rank
            out, i = [], 0
            while i < len(ids):
                if i < len(ids) - 1 and ids[i] == pair[0] and ids[i + 1] == pair[1]:
                    out.append(new_id)
                    i += 2
                else:
                    out.append(ids[i])
                    i += 1
            ids = out
        if len(self._cache) < 500_000:
            self._cache[chunk] = ids
        return ids

    def encode(self, text: str) -> list[int]:
        out: list[int] = []
        for chunk in self._split.findall(text):
            out.extend(self._encode_chunk(chunk))
        return out

    def decode(self, ids: list[int]) -> str:
        return b"".join(self.vocab[i] for i in ids if 0 <= i < self.vocab_size).decode("utf-8", errors="replace")

    def token_bytes(self, token_id: int) -> bytes:
        return self.vocab[token_id]

    # -- persistence ----------------------------------------------------------

    def to_dict(self) -> dict:
        return {"type": "bpe", "version": 1, "pattern": self.pattern, "merges": [list(m) for m in self.merges]}

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict()), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict) -> "BPETokenizer":
        if data.get("type") != "bpe":
            raise ValueError("not a BPE tokenizer")
        return cls([tuple(m) for m in data["merges"]], data.get("pattern", PATTERN))

    @classmethod
    def load(cls, path: str | Path) -> "BPETokenizer":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def train_bpe(texts, vocab_size: int, pattern: str = PATTERN, min_frequency: int = 2, verbose: bool = False) -> BPETokenizer:
    """Learn vocab_size - 256 merges from an iterable of strings."""
    split = re.compile(pattern)
    chunk_counts: Counter = Counter()
    for text in texts:
        chunk_counts.update(split.findall(text))

    words = [list(chunk.encode("utf-8")) for chunk in chunk_counts]
    freqs = list(chunk_counts.values())
    pair_counts: dict[tuple[int, int], int] = defaultdict(int)
    where: dict[tuple[int, int], set[int]] = defaultdict(set)
    for idx, word in enumerate(words):
        f = freqs[idx]
        for pair in zip(word, word[1:]):
            pair_counts[pair] += f
            where[pair].add(idx)

    merges: list[tuple[int, int]] = []
    while 256 + len(merges) < vocab_size and pair_counts:
        pair = max(pair_counts, key=pair_counts.__getitem__)
        if pair_counts[pair] < min_frequency:
            break
        new_id = 256 + len(merges)
        merges.append(pair)
        for idx in where.pop(pair, set()):
            word, f = words[idx], freqs[idx]
            for old in zip(word, word[1:]):
                count = pair_counts.get(old, 0) - f
                if count > 0:
                    pair_counts[old] = count
                else:
                    pair_counts.pop(old, None)
                if old != pair:
                    where[old].discard(idx)
            out, i = [], 0
            while i < len(word):
                if i < len(word) - 1 and word[i] == pair[0] and word[i + 1] == pair[1]:
                    out.append(new_id)
                    i += 2
                else:
                    out.append(word[i])
                    i += 1
            words[idx] = out
            for new_pair in zip(out, out[1:]):
                pair_counts[new_pair] += f
                where[new_pair].add(idx)
        pair_counts.pop(pair, None)
        if verbose and len(merges) % 500 == 0:
            print(f"  {len(merges)} merges")
    return BPETokenizer(merges, pattern)
