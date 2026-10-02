"""Train Coda from random weights on CPU (or CUDA if present).

Phase 3 defaults are sized for a Ryzen 7 5700G-class CPU: ~3.3M parameters,
700 steps x 32 sequences x 256 bytes (~5.7M tokens, roughly 15 minutes).

Key behaviour:
- warmup + cosine learning-rate decay;
- a share of each batch starts exactly at an example boundary so the model
  sees whole "<task> ... </task> <code> ..." units, not only random slices;
- validation uses a fixed set of windows (low-noise, comparable across evals);
- early stopping and the best checkpoint use `val` = unseen task families;
- `val_iid` (unseen examples of seen families) is reported to expose memorisation.
"""
from pathlib import Path
import argparse
import dataclasses
import json
import math
import time

import numpy as np
import torch

from opcoda.config import PROFILES
from opcoda.model import Coda


class Split:
    """A byte-token stream plus optional example start offsets."""

    def __init__(self, data_dir: Path, name: str, block_size: int, required: bool = True, dtype: str = "uint8"):
        path = data_dir / f"{name}.bin"
        self.name = name
        self.data = None
        self.starts = None
        if not path.exists():
            if required:
                raise SystemExit(f"Missing {path}. Run: python prepare_data.py")
            return
        self.data = np.memmap(path, dtype=np.dtype(dtype), mode="r")
        self.max_start = len(self.data) - block_size - 1
        if self.max_start <= 0:
            raise SystemExit(f"{path} is smaller than the model context window.")
        offsets_path = data_dir / f"{name}_offsets.npy"
        if offsets_path.exists():
            offsets = np.load(offsets_path)
            self.starts = offsets[offsets <= self.max_start]

    def __bool__(self) -> bool:
        return self.data is not None

    def __len__(self) -> int:
        return 0 if self.data is None else len(self.data)


def windows(split: Split, starts: np.ndarray, block_size: int, device: str):
    idx = starts[:, None] + np.arange(block_size + 1)[None, :]
    chunk = torch.from_numpy(split.data[idx].astype(np.int64))
    return chunk[:, :-1].contiguous().to(device), chunk[:, 1:].contiguous().to(device)


def sample_starts(split: Split, n: int, align_frac: float, rng: np.random.Generator) -> np.ndarray:
    starts = rng.integers(0, split.max_start, size=n)
    if split.starts is not None and len(split.starts) and align_frac > 0:
        aligned = rng.random(n) < align_frac
        starts[aligned] = rng.choice(split.starts, size=int(aligned.sum()))
    return starts


def fixed_eval_starts(split: Split, count: int) -> np.ndarray:
    """Deterministic windows: evenly spaced example starts (or byte positions)."""
    pool = split.starts if split.starts is not None and len(split.starts) else np.arange(0, split.max_start)
    picks = np.linspace(0, len(pool) - 1, num=min(count, len(pool))).round().astype(np.int64)
    return pool[picks]


@torch.no_grad()
def evaluate(model, split: Split, starts: np.ndarray, batch_size: int, device: str) -> float:
    model.eval()
    total = 0.0
    for i in range(0, len(starts), batch_size):
        x, y = windows(split, starts[i : i + batch_size], model.cfg.block_size, device)
        _, loss = model(x, y)
        total += loss.item() * len(x)
    model.train()
    return total / len(starts)


def lr_at(step: int, args) -> float:
    if step <= args.warmup:
        return args.lr * step / max(1, args.warmup)
    progress = min(1.0, (step - args.warmup) / max(1, args.steps - args.warmup))
    return args.min_lr + 0.5 * (args.lr - args.min_lr) * (1 + math.cos(math.pi * progress))


def make_optimizer(model, args):
    decay = [p for p in model.parameters() if p.dim() >= 2]
    no_decay = [p for p in model.parameters() if p.dim() < 2]
    return torch.optim.AdamW(
        [{"params": decay, "weight_decay": args.weight_decay}, {"params": no_decay, "weight_decay": 0.0}],
        lr=args.lr,
        betas=(0.9, 0.95),
    )


def save_checkpoint(path, model, cfg, args, step, best_val, extra=None, tokenizer=None):
    torch.save(
        {
            "model": model.state_dict(),
            "config": dataclasses.asdict(cfg),
            "profile": args.profile,
            "step": step,
            "best_val": best_val,
            "train_args": vars(args),
            # Phase 4+: the BPE tokenizer travels with the weights (None = byte tokens).
            "tokenizer": tokenizer,
            "format": "coda-phase4" if tokenizer else "coda-phase3",
            **(extra or {}),
        },
        path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", choices=PROFILES, default="smoke")
    parser.add_argument("--name", default=None, help="checkpoint prefix (default: profile name)")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--steps", type=int, default=700)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=2e-3, help="peak learning rate")
    parser.add_argument("--min-lr", type=float, default=2e-4, help="final learning rate of the cosine decay")
    parser.add_argument("--warmup", type=int, default=50)
    parser.add_argument("--weight-decay", type=float, default=0.1)
    parser.add_argument("--dropout", type=float, default=None, help="override the profile's dropout")
    parser.add_argument("--align-frac", type=float, default=0.5, help="share of windows that start at an example boundary")
    parser.add_argument("--eval-every", type=int, default=50)
    parser.add_argument("--eval-windows", type=int, default=256, help="fixed windows per split for each evaluation")
    parser.add_argument("--save-every", type=int, default=500, help="0 disables periodic step checkpoints")
    parser.add_argument("--patience", type=int, default=4, help="stop after this many non-improving evals; 0 disables")
    parser.add_argument("--min-delta", type=float, default=0.002)
    parser.add_argument("--threads", type=int, default=0, help="torch CPU threads (0 = PyTorch default)")
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    if args.threads:
        torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    data_dir = Path(args.data_dir)
    manifest_path = data_dir / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    dataset_info = {"format": manifest.get("format"), "splits": manifest.get("splits")}
    tok_info = manifest.get("tokenizer") or {"type": "bytes", "vocab_size": 256}
    dtype = manifest.get("dtype", "uint8")

    cfg = PROFILES[args.profile]
    if args.dropout is not None:
        cfg = dataclasses.replace(cfg, dropout=args.dropout)
    if cfg.vocab_size != tok_info["vocab_size"]:
        raise SystemExit(f"profile {args.profile} has vocab {cfg.vocab_size} but the dataset uses "
                         f"{tok_info['vocab_size']} ({tok_info['type']}). Pick a matching --profile or re-run prepare_data.py.")
    tokenizer_payload = None
    if tok_info["type"] == "bpe":
        tokenizer_payload = json.loads(Path(tok_info["path"]).read_text(encoding="utf-8"))
    name = args.name or args.profile
    model = Coda(cfg).to(device)
    optimizer = make_optimizer(model, args)

    train = Split(data_dir, "train", cfg.block_size, dtype=dtype)
    val = Split(data_dir, "val", cfg.block_size, dtype=dtype)
    val_iid = Split(data_dir, "val_iid", cfg.block_size, required=False, dtype=dtype)
    eval_sets = [(s, fixed_eval_starts(s, args.eval_windows)) for s in (train, val, val_iid) if s]
    dataset_info["tokenizer"] = {k: tok_info.get(k) for k in ("type", "vocab_size", "sha256")}

    ckpt_dir = Path("checkpoints")
    ckpt_dir.mkdir(exist_ok=True)
    best_path = ckpt_dir / f"coda-{name}-best.pt"
    if best_path.exists():
        backup = ckpt_dir / f"coda-{name}-best.prev.pt"
        best_path.replace(backup)
        print(f"previous best checkpoint moved to {backup}")

    tokens_per_step = args.batch_size * cfg.block_size
    print(f"device: {device} | threads: {torch.get_num_threads()}")
    print(f"profile: {args.profile} | parameters: {model.parameter_count():,} | dropout: {cfg.dropout}")
    print(f"context: {cfg.block_size} byte-tokens | batch: {args.batch_size} | tokens/step: {tokens_per_step:,}")
    print(f"train tokens: {len(train):,} | val tokens: {len(val):,} | val_iid tokens: {len(val_iid):,}")
    print(f"planned: {args.steps} steps = {args.steps * tokens_per_step:,} tokens "
          f"({args.steps * tokens_per_step / max(1, len(train)):.2f} epochs)")
    print(f"lr: {args.lr} -> {args.min_lr} (warmup {args.warmup}) | aligned windows: {args.align_frac:.0%}")

    history = []
    best_val, best_step, stale = float("inf"), 0, 0
    started = time.time()
    model.train()

    step = 0
    for step in range(1, args.steps + 1):
        lr = lr_at(step, args)
        for group in optimizer.param_groups:
            group["lr"] = lr

        x, y = windows(train, sample_starts(train, args.batch_size, args.align_frac, rng), cfg.block_size, device)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step == 1 or step % 10 == 0:
            elapsed = time.time() - started
            print(f"step {step:>5} | loss {loss.item():.4f} | lr {lr:.2e} | {elapsed:6.1f}s "
                  f"| {step * tokens_per_step / max(elapsed, 1e-9):,.0f} tok/s")

        if step % args.eval_every == 0 or step == args.steps:
            losses = {s.name: evaluate(model, s, starts, args.batch_size, device) for s, starts in eval_sets}
            history.append({"step": step, "lr": lr, "elapsed": round(time.time() - started, 1), **losses})
            line = " | ".join(f"{k} {v:.4f}" for k, v in losses.items())
            print(f"eval  {step:>5} | {line}")

            if losses["val"] < best_val - args.min_delta:
                best_val, best_step, stale = losses["val"], step, 0
                save_checkpoint(best_path, model, cfg, args, step, best_val, {"losses": losses, "dataset": dataset_info}, tokenizer_payload)
                print(f"best  {step:>5} | val {best_val:.4f} | saved {best_path}")
            else:
                stale += 1
                if args.patience and stale >= args.patience:
                    print(f"early stop | no val improvement for {stale} evals (best {best_val:.4f} @ step {best_step})")
                    break

        if args.save_every and step % args.save_every == 0:
            path = ckpt_dir / f"coda-{name}-step-{step}.pt"
            save_checkpoint(path, model, cfg, args, step, best_val, {"dataset": dataset_info}, tokenizer_payload)
            print(f"saved: {path}")

    last_path = ckpt_dir / f"coda-{name}-last.pt"
    save_checkpoint(last_path, model, cfg, args, step, best_val, {"dataset": dataset_info}, tokenizer_payload)
    log_path = ckpt_dir / f"coda-{name}-log.json"
    log_path.write_text(json.dumps({"args": vars(args), "best_val": best_val, "best_step": best_step,
                                    "parameters": model.parameter_count(), "history": history}, indent=2),
                        encoding="utf-8")
    print(f"done  | best val {best_val:.4f} @ step {best_step} | {time.time() - started:.0f}s")
    print(f"best: {best_path} | last: {last_path} | log: {log_path}")


if __name__ == "__main__":
    main()
