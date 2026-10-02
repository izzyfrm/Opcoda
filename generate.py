import argparse
import torch

from opcoda.config import CodaConfig
from opcoda.model import Coda
from opcoda.tokenizer import tokenizer_from_checkpoint


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint")
    parser.add_argument("--prompt", default=None,
                        help='code prefix, e.g. "def add(a, b):" (a literal \\n is treated as a newline)')
    parser.add_argument("--task", default=None,
                        help="plain-English task; uses the <task>/<code> format and stops at </code>")
    parser.add_argument("--tokens", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    payload = torch.load(args.checkpoint, map_location=device)
    cfg = CodaConfig(**payload["config"])
    model = Coda(cfg).to(device)
    model.load_state_dict(payload["model"])

    # PowerShell passes "\n" through literally; treat it as a newline.
    code = (args.prompt if args.prompt is not None else ("" if args.task else "def add(a, b):\n")).replace("\\n", "\n")
    if code.rstrip().endswith(":") and not code.endswith("\n"):
        code += "\n"
    code_tag = '<code lang="python">' if payload.get("format") == "coda-phase4" else '<code>'
    prompt = f"<task>\n{args.task}\n</task>\n{code_tag}\n{code}" if args.task else code
    stop = ["</code>"] if args.task else None

    tok = tokenizer_from_checkpoint(payload)
    ids = tok.encode(prompt)
    x = torch.tensor([ids], dtype=torch.long, device=device)
    y = model.generate(
        x,
        max_new_tokens=args.tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        stop=[tok.encode(s) for s in stop] if stop else None,
    )[0].tolist()

    print(tok.decode(y))


if __name__ == "__main__":
    main()
