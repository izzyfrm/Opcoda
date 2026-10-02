# Opcoda — Coda 1.0 starter

This is the first from-scratch Coda training skeleton. It does **not** download a pretrained model and it does **not** call an AI API.

The first goal is intentionally small: prove that the entire training → checkpoint → generation loop works on your PC before scaling the model or dataset.

## 1. Create the environment (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Add training code

Put code you own or permissively licensed training material inside `data/raw/`.

Supported starter extensions:

- `.py`
- `.js`, `.mjs`, `.cjs`
- `.html`
- `.css`
- `.json`
- `.md`
- `.txt`

The included files are only tiny examples and are nowhere near enough for a useful model.

## 3. Prepare the byte-token dataset

```powershell
python prepare_data.py
```

The script intentionally refuses to train on a tiny dataset. Add enough material for at least 10,000 byte-tokens first.

## 4. First smoke training run

```powershell
python train.py --profile smoke --steps 500 --batch-size 8
```

The `smoke` profile is roughly 3M parameters and is meant to prove the pipeline works on CPU.

After that works, try longer runs. Do **not** move to the larger profiles until training/checkpointing/generation are stable.

## 5. Generate code

Use the checkpoint filename printed by training:

```powershell
python generate.py checkpoints/coda-smoke-step-500.pt --prompt "def add(a, b):\n"
```

At 500 steps on a small dataset, output may still be terrible. That's expected. The win is proving Coda learned from weights initialized from scratch.

## Model profiles

- `smoke`: ~3M params, 256-byte context. Start here.
- `coda-10m`: ~11M params. Much slower on CPU.
- `coda-25m`: ~25M-ish class. Save this for stronger hardware / a mature pipeline.

Exact parameter count is printed at startup.

## Next milestones

1. Build a real licensed coding corpus + manifest.
2. Add held-out coding evals.
3. Train an Opcoda BPE tokenizer.
4. Add instruction-style fine-tuning generated from deterministic code transformations/tests.
5. Add a local inference HTTP server.
6. Only then build the polished opcoda.cc frontend.
