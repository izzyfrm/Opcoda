# CodaBench 0.2

A small held-out benchmark for Coda's early checkpoints: 12 function-writing tasks
(`heldout_tasks.json`) that are never part of the training data.

## Run

From the repo root:

```powershell
python evals/coda_bench.py --self-test                                        # check the harness + sandbox (no model)
python evals/coda_bench.py checkpoints/coda-phase3-best.pt                    # syntax only
python evals/coda_bench.py checkpoints/coda-phase3-best.pt --functional       # + unit tests in the sandbox
python evals/coda_bench.py checkpoints/coda-phase3-best.pt --functional --samples 3   # more stable numbers
```

Reports go to `evals/codabench_results.md` (readable) and `evals/codabench_results.json` (for tracking runs).

## What is measured

Each task is prompted in two formats:

| format | prompt |
|---|---|
| `instruct` | `<task>\n{description}\n</task>\n<code>\n{signature}\n` (the Phase 3 training format) |
| `comment` | `# Task: {description}\n{signature}\n` (the CodaBench 0.1 format) |

- **syntax**: the generated function parses with `ast`. The function is cut at `</code>` or at the first
  top-level line after the body (standard stop-sequence practice for completion benchmarks).
  Generation allows up to 256 new byte-tokens (0.1 used 120, which truncated many valid functions).
- **functional** (opt-in, `--functional`): the function is run against the task's unit tests.

The headline number is sample 1 with a fixed seed. Each task gets its own seed, so a task's result does
not depend on the order tasks run in. Use `--samples 3` or more before trusting a 1-task difference.

## Keeping the tasks held out

`heldout_tasks.json` is the single source of truth, shared by three checks:

1. `tools/make_python_curriculum.py` refuses to generate if a task family name, function name, or task
   phrasing matches `banned_patterns` or a held-out function name.
2. `prepare_data.py` drops any example or file that defines a held-out function, matches a banned pattern,
   or reproduces a reference solution body, and reports the count in `data/dataset_manifest.json`.
3. `tools/ingest_repo.py` warns when an imported repository defines held-out functions.

The curriculum still teaches the building blocks (string reversal, `split()`, loops with `%`, dict
building, slicing). "Sibling" families exist on purpose. One example is `group_by_first_letter`, which
shares the grouping pattern with `group_by_length` but uses a different key. CodaBench measures whether
Coda can combine those skills for a task it has never seen.

## Safety of functional tests

Generated code never runs in the benchmark process. `sandbox.py`:

1. **Static gate**: exactly one top-level `def`. No imports, no dunder names or attributes, no
   `open`/`exec`/`eval`/`getattr`/..., no classes, `with`, `global`, or async.
2. **Separate interpreter**: `python -I -S` in a temporary directory with an empty environment.
3. **OS limits**: a Windows Job Object (256 MB memory, no child processes, 5 s CPU) or POSIX rlimits. If
   the limits cannot be applied, the child refuses to run.
4. **Restricted builtins**: `len`, `range`, `sorted`, and similar.
5. **Wall-clock timeout**: the parent kills the process after 10 s.

`--self-test` proves the reference solutions pass and that imports, dunder escapes, file access, infinite
loops, and memory bombs are contained. This is a guard for toy functions from a 3M-parameter model. It is
not a hardened security boundary. For stronger isolation, run the benchmark in a disposable VM or container.
