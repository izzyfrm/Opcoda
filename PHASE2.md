# Coda Phase 2 — run order

From the Opcoda repo root:

```powershell
python tools/make_python_curriculum.py --examples 4000
python prepare_data.py
python train.py --profile smoke --steps 2000 --batch-size 8 --eval-every 100 --patience 6
```

Use the best validation checkpoint, not automatically the final checkpoint:

```powershell
python generate.py checkpoints/coda-smoke-best.pt --prompt "def count_vowels(text):" --temperature 0.2 --top-k 10 --tokens 100
python generate.py checkpoints/coda-smoke-best.pt --prompt "def unique_items(values):" --temperature 0.2 --top-k 10 --tokens 120
python generate.py checkpoints/coda-smoke-best.pt --prompt "def clamp(number, low, high):" --temperature 0.2 --top-k 10 --tokens 100
```

To add a reviewed local open-source repository later:

```powershell
python tools/ingest_repo.py C:\path\to\repo --name SOURCE_NAME --license LICENSE_ID --revision COMMIT_OR_TAG
python prepare_data.py
```

Keep `SOURCE.json` files in Git so provenance survives even when the large copied dataset is gitignored.
