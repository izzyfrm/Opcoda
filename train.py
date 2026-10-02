from pathlib import Path
import argparse
import time
import numpy as np
import torch

from opcoda.config import PROFILES
from opcoda.model import Coda


def load_tokens(path: str) -> np.memmap:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Missing {p}. Run: python prepare_data.py")
    return np.memmap(p, dtype=np.uint8, mode="r")


def batch(data: np.memmap, batch_size: int, block_size: int, device: str):
    max_start = len(data) - block_size - 1
    if max_start <= 0:
        raise SystemExit("Dataset is smaller than the model context window.")
    starts = torch.randint(0, max_start, (batch_size,)).tolist()
    x = torch.stack([
        torch.from_numpy(np.array(data[i : i + block_size], dtype=np.int64)) for i in starts
    ])
    y = torch.stack([
        torch.from_numpy(np.array(data[i + 1 : i + block_size + 1], dtype=np.int64)) for i in starts
    ])
    return x.to(device), y.to(device)


@torch.no_grad()
def estimate_loss(model, train_data, val_data, batch_size, device, iters=20):
    model.eval()
    out = {}
    for name, data in (("train", train_data), ("val", val_data)):
        losses = []
        for _ in range(iters):
            x, y = batch(data, batch_size, model.cfg.block_size, device)
            _, loss = model(x, y)
            losses.append(loss.item())
        out[name] = sum(losses) / len(losses)
    model.train()
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=PROFILES, default="smoke")
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--eval-every", type=int, default=100)
    parser.add_argument("--save-every", type=int, default=250)
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cfg = PROFILES[args.profile]
    model = Coda(cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.1)

    train_data = load_tokens("data/train.bin")
    val_data = load_tokens("data/val.bin")
    Path("checkpoints").mkdir(exist_ok=True)

    print(f"device: {device}")
    print(f"profile: {args.profile}")
    print(f"parameters: {model.parameter_count():,}")
    print(f"context: {cfg.block_size} byte-tokens")

    started = time.time()
    model.train()
    for step in range(1, args.steps + 1):
        x, y = batch(train_data, args.batch_size, cfg.block_size, device)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step == 1 or step % 10 == 0:
            elapsed = time.time() - started
            print(f"step {step:>6} | loss {loss.item():.4f} | {elapsed:.1f}s")

        if step % args.eval_every == 0:
            losses = estimate_loss(model, train_data, val_data, args.batch_size, device)
            print(f"eval       | train {losses['train']:.4f} | val {losses['val']:.4f}")

        if step % args.save_every == 0 or step == args.steps:
            path = Path("checkpoints") / f"coda-{args.profile}-step-{step}.pt"
            torch.save(
                {
                    "model": model.state_dict(),
                    "config": cfg.__dict__,
                    "profile": args.profile,
                    "step": step,
                },
                path,
            )
            print(f"saved: {path}")


if __name__ == "__main__":
    main()
