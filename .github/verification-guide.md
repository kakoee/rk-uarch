# Local verification measurements

Run the existing relevant selection with explicit timing (no new package):

```sh
uv run pytest -q -rs -p tests.verification_timing --timing-jsonl=/tmp/fresh-run/phases.jsonl \
  --durations=30 --junitxml=/tmp/fresh-run/results.xml tests/unit/test_ci_scope.py
```

The JSONL stream records exact selected and deselected node IDs, setup/call/teardown duration,
skips/xfails/failures and starts before test execution. Only `finish` records the exit status;
partial progress is not a pass. The output filename must be new. JUnit remains a conventional
interchange format. Keep the same selection and environment for before/after measurements;
record source commit plus patch, lock/packages, Python/OS, cache state, load, workers and RAM.
Use `/usr/bin/time -v` around the whole command for elapsed/CPU/peak RSS on Linux. Profiling
adds overhead; report its timing separately from unprofiled comparisons.

For multi-stage checks or prospective mutation sweeps, write a JSON array of trusted commands:

```json
[
  {"name": "control", "argv": [".venv/bin/python", "-m", "pytest", "-q", "tests/unit/test_ci_scope.py"]},
  {"name": "restoration", "always": true, "argv": [".venv/bin/python", "-m", "pytest", "-q", "tests/unit/test_ci_scope.py"]}
]
```

```sh
uv run python .github/verification_run.py --plan /tmp/plan.json --output /tmp/new-receipt
```

Each stage has separate stdout/stderr logs written as it runs, a start/completion event and
15-second progress heartbeat with completed/planned counts. Failed runs retain their logs.
An unexpected failure prevents later ordinary stages and records them as `not_run`; restoration
stages marked `always` still run. The runner uses one child at a time, starts no nested pool,
and never interprets an empty plan as success. A nonzero expected exit also requires literal
`contains` diagnostics, so collection errors or unrelated failures cannot substitute for the
intended fault. A complete JSON summary is written only after all dispositions are known.
This is execution reporting, not an independent review verdict or an authority token.

Plans do not isolate commands automatically. Mutation commands must operate on a fresh private
source copy, bind the exact preimage, and restore and hash-check the changed file in `finally`.
Do not modify the authoritative checkout or a sealed runtime. Use the same discriminating
assertion for positive, fault and restored runs. A focused mapping must retain a discovery
sentinel and must not replace mandated broad/final/replay runs. Preserve earlier reviewer
scripts and receipts byte for byte; apply this harness only to new work.

Worker policy is unchanged: one pytest process by default. Do not infer a safe Python pool
size from the historical 11-worker native campaign. Any future sharding should measure the
critical path and summed CPU/RAM, use isolated mutable outputs and prove identical node/outcome
coverage. Adding pytest-xdist would be a separate dependency proposal.

## Existing Python CI

Python and contract jobs emit the same opt-in phase stream plus their ordinary pytest logs,
slow-phase table and JUnit file in the runner temporary directory. An `always()` step prints
the last phase event, including totals and exit status when complete. This preserves the
machine-readable summary in job logs, including failed runs. Full JSONL/JUnit files are local
runner outputs; durable hosted artifact upload would require a separately reviewed action.
The last event of an interrupted run may be a start/phase event and is not a pass summary.

The existing [setup-uv v3 action](https://raw.githubusercontent.com/astral-sh/setup-uv/v3/action.yml)
supports its built-in dependency cache; the key inputs here include `uv.lock` and
`pyproject.toml`. Each job still runs `uv sync --locked --extra dev` and all of its required
checks on current source. No `.venv`, pytest result, host authority or runtime is reused.
Hosted cache savings are unmeasured until an actual hosted run; local warm-cache timings
cannot establish them. No action version or package dependency changes in this patch.
