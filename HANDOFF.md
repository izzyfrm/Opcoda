# Opcoda / Coda 1.0 — Handoff (end of Phase 3)

Read this first if you are continuing the project (human or AI).

## Ground rules (from the project owner, do not break)

- Coda is trained **from random weights** with PyTorch. Do not add API providers, pretrained models,
  Hugging Face downloads, or wrappers.
- Hardware: AMD Ryzen 7 5700G (8C/16T), 16 GB RAM, integrated graphics only, Windows. **CPU training.**
  Do not recommend CUDA/NVIDIA or large-VRAM setups.
- Keep the model around 3–5M parameters until generalization improves. Prefer short experiments
  (500–700 steps, about 15 minutes) with early stopping.
- Do not redesign the frontend (`index.html`, `server.py`). Do not delete working code unless necessary.
- Never put CodaBench tasks into training data.

## Current state

| | Phase 2 (before) | Phase 3 (now) |
|---|---|---|
| model | 3,290,624 params, 4 layers, 256 dim, 256-byte context | unchanged |
| training data | 16 docstring templates, 746k train tokens | 224 task families, 6.65M train tokens |
| tokens seen in training | ~1.2M (600 × 8 × 256) | ~5.3M (650 × 32 × 256) |
| val split | per file; val held a different file (numbered clones) | per task family (17 unseen families) + IID val |
| CodaBench syntax, `instruct` format (mean of 5 samples) | 0.4 / 12 | **7.0 / 12** |
| CodaBench syntax, `comment` (v0.1) format (mean of 5 samples) | 0.6 / 12 | **7.4 / 12** |
| CodaBench functional (mean of 5 samples) | not measured | **0 / 12** |

The Phase 2 numbers come from the same CodaBench 0.2 harness, so the comparison is fair.

Best checkpoint: `checkpoints/coda-phase3-best.pt` (step 650, val 0.640). It took 803 s on the 5700G.
The training log is in `checkpoints/coda-phase3-log.json`.

Loss curve (per byte, fixed eval windows):

```
step   train   val(unseen families)   val_iid(seen families)
 100   1.788   1.795                  1.767
 300   0.742   0.859                  0.743
 500   0.323   0.678                  0.340
 650   0.223   0.640  <- best         0.234
 700   0.208   0.652                  0.220
```

How to read it:
- **train ≈ val_iid**: the model is *not* memorizing individual examples any more. This was the Phase 2
  problem.
- **val is about 0.4 above val_iid**: this is the gap to unseen tasks. Closing it is the real work ahead.

### What the model can and cannot do

It now writes structurally valid Python: 4-space indents, closed strings and brackets, comprehensions,
loops, and it stops cleanly at `</code>`. It **cannot yet solve tasks**. Bodies often reference
variables that don't exist (`return line == 0`), or copy a pattern from a similar family (to_snake_case →
the "remove vowels" loop). Even training families are unreliable: `count_vowels` produced
`sum(1 for v in text.lower() if v > 0)`. So the model is still under-trained on *semantics*, not just
weak at transfer. See `evals/codabench_results.md` for every generated function.

## Pipeline

```
tools/curriculum_families.py   task families: names, phrasings, multiple implementations, checks
tools/make_python_curriculum.py  -> data/curriculum/curriculum.jsonl (+ stats.json)
prepare_data.py                  -> data/{train,val,val_iid}.bin + *_offsets.npy + dataset_manifest.json
train.py                         -> checkpoints/coda-<name>-{best,last}.pt + coda-<name>-log.json
evals/coda_bench.py              -> evals/codabench_results.{md,json}
evals/heldout_tasks.json         single source of truth for CodaBench tasks + banned patterns
evals/sandbox.py                 isolated execution for functional tests
tools/ingest_repo.py             import a reviewed local repo with license/revision provenance
```

### Exact commands (PowerShell, repo root, venv active)

```powershell
python tools/make_python_curriculum.py                                   # ~30 s, 35k examples, verifies all templates
python prepare_data.py                                                   # ~10 s
python train.py --name phase3                                            # ~14 min on the 5700G
python evals/coda_bench.py --self-test                                   # harness + sandbox check, no model
python evals/coda_bench.py checkpoints/coda-phase3-best.pt --functional --samples 5   # ~5 min
```

Generation:

```powershell
python generate.py checkpoints/coda-phase3-best.pt --task "Return the number of vowels in text." --prompt "def count_vowels(text):" --temperature 0.2
```

## What changed in Phase 3 and why

1. **Curriculum generator rewritten** (`tools/make_python_curriculum.py`, `tools/curriculum_families.py`).
   - 224 task families across math, logic, strings, parsing, lists, dicts, algorithms, and classes.
     There are 491 implementations, often a loop version, a builtin version, and a comprehension.
   - Every example gets fresh function, parameter, and local names from type-appropriate pools. There
     are no numbered clones, and docstrings appear in only 5% of examples.
   - Before writing anything, the generator executes every implementation on sample inputs and checks
     that all implementations of a family agree, so buggy templates can't teach wrong code.
   - Dedup is AST-level and ignores docstrings and type hints, so cosmetic variants don't count as new.
   - Formats: 60% `<task>…</task><code>…</code>`. The other 40% is plain code, `# description` comments,
     or the legacy `# Task:` comments.
2. **Splits that measure generalization** (`prepare_data.py`).
   - `val` is 17 whole task families that never appear in training. Early stopping uses it.
   - `val_iid` is 3% of examples from training families. It exposes memorization.
   - Cross-split dedup, plus a contamination guard against `evals/heldout_tasks.json`. The guard drops
     held-out function names, banned phrasings, and reference solution bodies.
   - The 900 `add_0 … max_299` clones in `data/raw/generated_examples.py` are detected and skipped. The
     file was left in place.
3. **Training** (`train.py`). The model architecture is unchanged.
   - Batch size 32 instead of 8, so each step sees 4× more tokens at the same step count.
   - Peak LR 2e-3 with 50 warmup steps, cosine decay to 2e-4, AdamW betas (0.9, 0.95), and no weight
     decay on biases or LayerNorm. Phase 2 used a constant 3e-4.
   - 50% of training windows start exactly at an example boundary, so the model sees
     `<task> → <code>` units in full inside the 256-byte context.
   - Evaluation uses 256 fixed windows per split instead of 30 random batches, which makes it low-noise.
     The best checkpoint and patience are judged on `val`.
   - A run never overwrites a previous best silently: the old one is moved to `*-best.prev.pt`.
     `--name` keeps runs apart.
4. **CodaBench 0.2** (`evals/`).
   - Tasks moved to JSON, each with unit tests and a reference solution.
   - Both prompt formats are scored. The token budget is 256 (v0.1's 120 truncated valid functions).
   - Stop sequences, standard function extraction, `--samples N`, and per-task seeds.
   - `--functional` runs tests in `sandbox.py`: a static AST gate, then `python -I -S` in a temporary
     directory, a Windows Job Object (256 MB, no child processes, 5 s CPU), restricted builtins, and a
     10 s timeout. `--self-test` proves it contains imports, dunder escapes, `open`/`eval`, infinite
     loops, and memory bombs.
5. **Smaller fixes.**
   - `Coda.generate(stop=...)` was added and is backward compatible.
   - `generate.py --task` was added, and a literal `\n` from PowerShell is now treated as a newline.
   - `tools/ingest_repo.py` was a copy of the old generator. It is now the documented ingest tool.

## Website (opcoda.cc)

The frontend moved from the root `index.html` (removed; still in git history) to `web/`, a Cloudflare
Worker named `opcoda`. Full details are in `web/README.md`. Summary:

- `web/public/` is a static, no-build site: auth screen, chat with highlighted code, history, settings
  (profile picture, display name, theme, creativity/length, password, sign out elsewhere, delete account).
- `web/src/` handles `/api/*`: accounts (PBKDF2), cookie sessions, D1 storage, rate limits, and the daily
  message limit.
- Chat flows: Worker → Workers VPC service `coda-model` → private Cloudflare Tunnel `opcoda-model` →
  `server.py` at `127.0.0.1:8000` on the owner's PC. There is no public model URL, and requests carry a
  shared `MODEL_TOKEN` as well. When the PC is off, the site shows Coda as Offline.
- Deployed 2026-10-02. Resource IDs are in `web/README.md`.
- `server.py` is now just the model API: it serves `coda-phase3-best.pt`, wraps plain-English requests in
  the `<task>` format, stops at `</code>`, runs one generation at a time, and requires the token.
- `.\start-coda.ps1` runs `server.py` and the tunnel together.
- Tests: `cd web; npm run check; node test/api-smoke.mjs` (33 API checks against `wrangler dev`).

## Phase 4 (multi-language Coda) — IN PROGRESS, not deployed

Built:
- `opcoda/bpe.py`: BPE tokenizer trained from scratch (`tokenizer/coda-bpe-4k.json`, 3.15 bytes/token).
- `opcoda/verify.py`: static checks for Python, HTML, CSS and JS. No code is executed.
- `tools/make_code_curriculum.py` (+ `web_families.py`, `js_families.py`, `program_families.py`):
  52k verified examples (80 MB) of HTML pages and apps, CSS, JS and Python programs → `data/v4`
  (14M train tokens).
- Model: `coda-6m` profile (6.0M params, 1024-token context), KV-cache `Coda.sample()` for
  batched drafts.
- `server.py`: best-of-N drafts, each verified per language.
- Worker: `language` and `drafts` settings, `/api/messages/:id/preview` (sandboxed).
- UI: code workspace (Code / Preview / Run), `public/sandbox/run.html` (Pyodide 314.0.7 + JS in a
  classic Web Worker, opaque origin, tested working).

Remaining:
1. Training was started: `python train.py --profile coda-6m --data-dir data/v4 --name coda-v4
   --steps 1800 --batch-size 16 --lr 1.5e-3 --min-lr 1.5e-4 --warmup 100 --eval-every 150
   --eval-windows 96 --align-frac 0.75 --patience 6 --save-every 600`. Output goes to
   `checkpoints/coda-coda-v4-best.pt`. When it's done, rename it to `checkpoints/coda-v4-best.pt`.
   If the run was interrupted, rerun the same command.
2. Test locally with `.claude/launch.json` configs `coda-model-test` (port 8001, uses
   `CODA_CHECKPOINT`) and `opcoda-web-test`.
3. Deploy the Worker: `cd web; npx wrangler deploy`. Then restart `.\start-coda.ps1`, which
   auto-selects the newest checkpoint.
4. CodaBench still uses the Phase 3 prompt format. Update it to load the tokenizer from the
   checkpoint (`opcoda.tokenizer.tokenizer_from_checkpoint`) and use `<code lang="python">`.
5. The in-app browser pane blocks iframes (`ERR_BLOCKED_BY_CLIENT`). Verify Preview and Run in a
   real browser.

Do NOT restart `start-coda.ps1` before training finishes. The new `server.py` would pick up the
half-trained `coda-coda-v4-best.pt`.

## Known issues / gotchas

- `checkpoints/coda-smoke-*.pt` are the Phase 2 checkpoints, kept for comparison.
- New files written by the Write tool on Windows have CRLF line endings. Git `autocrlf` normalizes them.
- The CodaBench headline is noisy at 12 tasks. Always compare runs with `--samples 5` means.
- Some families yield few unique variants (classes, circle formulas). `data/curriculum/stats.json` lists
  per-family counts.

## Recommended next steps (in order)

1. **Train longer before changing anything else.** Val was still dropping at step 650 and train ≈
   val_iid, so the model is under-fit, not over-fit. Try `python train.py --name p3-long --steps 2000`
   (~40 min). Compare CodaBench means and val. The curriculum is large enough (6.65M tokens) that 2–3
   epochs should not memorize; watch the train − val_iid gap.
2. **Build a bigger unseen-task functional eval** from the 17 val families. The reference
   implementations and `checks` already exist in `curriculum_families.py`, so expected outputs can be
   computed by running the references. Twelve CodaBench tasks with 0 functional passes give no gradient
   of progress; 17 more tasks with partial credit would.
3. **Make the model use its parameters.** Most failures reference undefined names. Ideas: weight the
   loss more on code tokens after `<code>`; add families whose body must mention every parameter; add
   "fix the bug" / "complete the body" variants built from the same templates.
4. **Compositional families.** CodaBench tasks are compositions of curriculum skills, such as reverse +
   compare or split + len. Add explicit two-step families (e.g. "reverse then uppercase", "count items
   that satisfy X") so the model sees composition during training.
5. Only after functional passes appear, consider a BPE tokenizer (which gives more code per 256-token
   context) or the `coda-10m` profile.
