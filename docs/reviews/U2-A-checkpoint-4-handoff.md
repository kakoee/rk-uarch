# A3-C1/C2 correction — coordinator recheck

Status: bounded A correction, uncommitted. A remains a partial runtime checkpoint;
this does not claim all A-owned U-P3 exits, final U-REVIEW or a B report complete.

The received A3 package had 489 payload entries, manifest
`aca028908a0de74f437a3e8328959280c88d5cdb301049a7d7e01189e75ed6bb`.
Every payload verified before edits. `U2-A-checkpoint-4/received-baseline.json`
records all 792 received tracked/untracked file hashes, branch `u2/analytic` and
HEAD `1e9e794a84c5173812c23a1cf2fc04b85e6f6831`. Only two pre-existing files
advance: `src/rkuarch/cli.py` and `src/rkuarch/workload/characterize.py`.
`tests/unit/test_u2_a_completion.py` is new. The other additions are this handoff
and its evidence directory. Exact old/new hashes are in `changes-from-A3.json`;
`source-delta.patch` isolates the three source/test paths. The full dirty-payload
manifest is `U2-A-checkpoint-4/SHA256SUMS`, with repo-relative paths. It includes
received work and historical logs; those logs are not new execution evidence.
The manifest has 530 payload entries; the authored list has 44 paths (42 hashed
delta entries plus changes-from-A3.json and SHA256SUMS, the two recursive envelopes).

## A3-C1 disposition: implemented, tested, awaiting coordinator recheck

Before: `uarch validate <spec>` exited 2 as an invalid command. Now it accepts
HardwareSpec YAML/YML or strict JSON, delegates to the existing HardwareSpec and
SourcedValue validators, and exits 0 with sorted sourced-value paths, original
values/units, source/provenance/date or stipulation rationale, and category counts.
Claims include stubs; the displayed non-stub claims/stipulations/stubs sections are
disjoint. No draft reference hardware or new schema is used. Invalid input exits 2
on stderr with its offending dotted/indexed path. A reference specification with a
stipulation refuses at `cores.grid.rows`; malformed input and source/unit/rationale/
capacity/missing-value errors also refuse.

`app` is now a callable Typer application, as required by U-P3. The installed
`uarch = rkuarch.cli:app` entry point and `app()` invocation remain. Existing
prepare/capture/table/characterize/rk-component commands forward their existing
argument grammar through the unchanged parser; this is not a full parser rewrite.
Typer was already declared and installed; no dependency or lockfile changed.
`validate_command(spec: Annotated[Path, typer.Argument(...)]) -> None` is added.

Executed H1 and H2 validation both exits 0: H1 has 59 sourced values, all 59
stipulations; H2 has 67, all 67 stipulations. Both have zero claims/stubs. Independent
synthetic valid JSON/YAML controls exercise 49 values: 48 claims including 47 stubs,
and one stipulation. A separate synthetic claims-only reference control passes.
This validates input structure and provenance declarations, not silicon accuracy.

## A3-C2 disposition: implemented, tested, awaiting coordinator recheck

Before: characterize emitted only the raw JSON. Now, for
`--output path/selection.json`, it writes that same JSON plus
`path/selection.md` (exact rule: `Path(output).with_suffix(".md")`). The JSON
remains canonical JSON plus LF; Markdown is UTF-8 plus LF. A JSON destination whose
suffix is already `.md` refuses because the destinations alias. Both paths are
preflighted before either write. Existing differing bytes, non-files and output
symlinks refuse with exit 2/OutputConflict; existing identical files are retained.
Missing files use exclusive creation. This is no-overwrite conflict handling, not
a claim of an atomic two-file transaction under concurrent mutation or I/O failure.

Added API: `characterize_markdown(captured: dict[str, object]) -> str`. It consumes
the one captured computation used for JSON and checks its existing job/result
bindings. It does not rerun preparation or the engine. The Markdown binds the exact
JSON byte hash and recorded hardware/bundle/request/point/job/result, producer,
engine/model and assumptions identities. It retains per-grid query/frequency/state/
mode and rank/hit scope, row and per-op counts, instances, durations in picoseconds,
intensity, precision roles, physical dimensions and shape regimes. Known weight/KV
allocations, omissions, null diagnostics/load fields and unknown total HBM/SRAM peak
remain explicit. Per-op estimates are not presented as additive aggregate timings.

The heading labels this workload-selection output as unvalidated physical
predictions. It makes no evidence eligibility, independent review, measurement or
silicon validation claim. It is separate from B's full evidence-aware table report.
The captured JSON's five keys and existing `characterize(bundle)` API are unchanged.
All 64 recorded prior callable signatures and all four NamedTuple field maps
(including the 20-field loader) verify unchanged. The existing characterize and
capacity-summary function bodies are unchanged; no production schema changed.
`api-inventory.json` records exact signatures and the explicit CLI app-type change.

Fresh saved npu-m256 × Llama-3.1-70B × FP8/TP8 runs with explicit synthetic assignment
use PYTHONHASHSEED/OMP_NUM_THREADS 1 and 4. Both JSON and Markdown are byte-identical
between runs. JSON is also byte-identical to A3's preserved H2 capture:

- JSON SHA256: `0fa1d4ebc103ead39e00505860ff27236c9f860702e1d45d592ef4b2799bf43f`.
- Markdown SHA256: `084a3451a51ac091a60b709a344d170141bf20f6fc2851053c55f75f6314573b`.

Saved twins are under `U2-A-checkpoint-4/demo/seed-{1,4}/characterize.{json,md}`.
Each has two query points and unknown total peak. The independent q-projection
expectation is 1,342,177,280 matrix ops (`2*8192*1024*80`) at each point. The tiny
literal row independently checks 1184 matrix, 572 vector, 1296 read, 288 write and
1,892,000ps in the correct Markdown columns. `demo-results.json` records commands,
environments, source/input/output hashes, exits and inspected observations.

## Tests-first and final checks

`tests-first.py.txt` and `before.txt` preserve the pre-body tests and 14 failures /
2 passes. `after-initial.txt` is not a green result: two intended-valid synthetic
inputs accidentally retained reference status after adding a stipulation; the
validator correctly refused them. The tests were corrected to proposed status,
keeping the separate reference-stipulation refusal. `after-v2.txt` records 21 passes.
`identity-tests-first.py.txt` and `identity-before.txt` preserve a later failing
hardware-identity display assertion before that addition (1 failed,7 passed).
Initial lint/mypy outputs are preserved separately; final outputs supersede them.

Fresh final execution on the exact source hashes in `check-results.json`:

- `pytest -p no:cacheprovider tests/unit/test_u2_a_completion.py tests/unit/test_u2_a_cli.py -q --tb=short`: 28 passed in 14.19s.
- Focused shape/prepared/hardware/physical discrepancy/prompt/third-party regression: 300 passed in 6.98s. Exact file arguments are in the saved runner and check record.
- `mypy --no-incremental`: 49 source files pass; `ruff check --no-cache src contract tests/unit` passes.
- Contract `generate --check`, engine protocol `generate(check=True)` and `git diff --check` pass.

These are two disjoint pytest selections, 328 passes total, zero skips. They are
not a new broad-suite, long-table replay or B integration claim. `run-checks.py.txt`
records the exact interpreter/argv/cwd/environment; source hashes were checked again
after the runs and demo. Prior 638 remains the historical union of A3 author runs;
the coordinator's executed checks and limited B consumer check remain separate.

## Preserved limits, reconciliation and proposed file list

Accepted `Padding.logical` stays positive. A selected rank with no logical
vocabulary slots still explicitly refuses; that refusal is not supported execution.
A rank with a nonempty shard and zero local embedding hits still executes zero
embedding weight reads with the captured masked output. Both cases pass their
existing tests. A new geometry-only check confirms nonempty shards for the three
named sidecars at required TP1/8, plus adjacent TP2/4. This is not a new all-model/TP
execution-coverage claim. A broader carrier change remains separate.

`tests/unit/test_u2_a_cli.py` is byte-unchanged. Preserve the coordinator's exact two
integration adaptations from historical A2 export paths to
`contract/tests/fixtures/u2_b/a2-export/npu-l4.execution-model.json` and
`npu-l4.oracle-compat.yaml`. The new test file needs no such adaptation. Transfer
only this three-path source/test delta; do not overlay the historical CLI test file.
U2-AB2-C1 is resolved/integrated; accepted exports and H1/H2 hardware are unchanged.

Historical proposal, A1/A2/A3 handoffs, evidence and manifests are untouched. Snapshot
verification and all received-file comparisons are recorded in `preservation.json`.
No proof interpreter, B report, policy/schema change, producer/engine change,
oracle generation/adoption, human flag, dependency installation, agent/message, cleanup,
cross-worktree edit, staging, commit, push or tag occurred. The known generator
fingerprint gate, remaining report/review/adoption/publication/closure work and
unexecuted broader cases are not claimed complete. No substantiated estimate change:
A 140–222/B 100–154 plus independent reviewer 16–24 remains the prior planning scope.

Proposed file list: `U2-A-checkpoint-4/checkpoint-paths.txt` (all authored paths;
the exact three runtime/test paths are identified above).
Proposed message, not committed:
`fix(u2): add hardware validation CLI and deterministic workload Markdown`

Stop for coordinator recheck. All work remains uncommitted.
