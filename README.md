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

## 2. Generate the Python curriculum

Coda currently trains on Python only. The main data source is an original, locally generated curriculum
(200+ task families, instruction-to-code and plain completions):

```powershell
python tools/make_python_curriculum.py
```

Extra `.py` files you own or that are permissively licensed can go in `data/raw/`, or can be imported with
provenance via `tools/ingest_repo.py`.

## 3. Prepare the byte-token dataset

```powershell
python prepare_data.py
```

This writes `train.bin`, `val.bin` (held-out task families), and `val_iid.bin`, plus
`data/dataset_manifest.json`. CodaBench tasks are checked for and kept out of the training data.

## 4. Train (CPU, ~15 minutes)

```powershell
python train.py --name phase3
```

Defaults: `smoke` profile (~3.3M params), 700 steps × 32 × 256 tokens, warmup + cosine LR, and early stopping
on validation loss. The best checkpoint is `checkpoints/coda-phase3-best.pt`.

Do **not** move to the larger profiles until training, checkpointing, and generation are stable.

## 5. Generate code and evaluate

```powershell
python generate.py checkpoints/coda-phase3-best.pt --task "Return the number of vowels in text." --prompt "def count_vowels(text):" --temperature 0.2
python evals/coda_bench.py checkpoints/coda-phase3-best.pt --functional
```

See `HANDOFF.md` for the current state, results, and next steps.

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
