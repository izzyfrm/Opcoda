import argparse
import torch

from opcoda.config import CodaConfig
from opcoda.model import Coda
from opcoda.tokenizer import ByteTokenizer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint")
    parser.add_argument("--prompt", default="def add(a, b):\n")
    parser.add_argument("--tokens", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=40)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    payload = torch.load(args.checkpoint, map_location=device)
    cfg = CodaConfig(**payload["config"])
    model = Coda(cfg).to(device)
    model.load_state_dict(payload["model"])

    tok = ByteTokenizer()
    ids = tok.encode(args.prompt)
    x = torch.tensor([ids], dtype=torch.long, device=device)
    y = model.generate(
        x,
        max_new_tokens=args.tokens,
        temperature=args.temperature,
        top_k=args.top_k,
    )[0].tolist()

    print(tok.decode(y))


if __name__ == "__main__":
    main()
