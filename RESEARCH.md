# Opcoda / Coda — phase 2 research notes

## Immediate training direction

Coda's first 3.3M checkpoint proved the pipeline works, but the train/validation gap showed memorization. Phase 2 therefore keeps the model small and changes the data before scaling parameters.

### Data priorities

1. Python-only first.
2. Split train/validation by whole files, never by slicing one byte stream.
3. Exact-deduplicate files before training.
4. Track source, revision, and license for imported repositories.
5. Keep a held-out eval set that is never copied into training data.
6. Use deterministic original curriculum data only as bootstrap material, not the final corpus.

## Public dataset research

- The Stack v2 is huge (600+ programming languages), gated, and requires users to follow original repository licenses and provenance/removal requirements. It is not a good first dataset for a CPU-only 3M model.
- CodeSearchNet contains millions of code/comment pairs and includes per-repository license metadata. It is useful to study later, but the full dataset is far larger than Coda needs for the next experiment.
- CodeXGLUE is more useful as an evaluation/task source than as Coda's raw pretraining corpus. Its dataset terms should be reviewed before reuse.
- CPython's source and docs use the Python Software Foundation license; current Python documentation code examples are also dual-licensed under BSD-0. It is a promising Python source after preserving license/provenance information.

## Phase 2 target

Do not move to coda-10m yet. Train the 3.3M smoke model on roughly 0.5–5 million clean Python byte-tokens and compare validation loss plus unseen completions. Only scale the model once generalization improves.
