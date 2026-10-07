# U1 · Lane B (U-P2) · U-REVIEW Stage 1: independent review

Date: 2026-10-06. Stage 1 only. This report gives evidence, not a verdict. It does not
adjudicate, adopt, accept an ADR, or declare U1/G1 complete.

**Reviewer independence.** I am a fresh session. I did not write any Lane A or Lane B code,
docs, artifacts or coordinator amendments, and I had no earlier part in this conversation.

**What was reviewed**

| Item | Path / identity |
|---|---|
| Primary target (combined A+B, plain directory) | `/tmp/u1-final-integration-84hif1_r` |
| Assembly evidence | `/tmp/u1-final-integration-84hif1_r-evidence/` (FINAL-VALIDATION.md, assembly.json, inventories) |
| Lane B source worktree (read-only) | `/home/jjaff/AI-infra-simulation/rk-uarch-u1-b` @ `af3b1bc` (+ uncommitted proposal) |
| Lane A source worktree (read-only) | `/home/jjaff/AI-infra-simulation/rk-uarch-u1-a` @ `af3b1bc` (+ uncommitted proposal) |
| Coordinator baseline | `/home/jjaff/AI-infra-simulation/rk-uarch` @ `89313eef20e6b252d235b40a680a1464c52c636a` |
| Pinned upstream (read-only) | `/home/jjaff/AI-infra-simulation/rk-sim-u1-pin` @ `1e5706e0ebfcc67c1a7333079a35b75f693e9963`, clean |
| Human final candidate (read-only) | `/tmp/u1-vendor-final-f96kn1fp` (manifest `6b0d69c5…8304`) |

Throughout, `C=/tmp/u1-final-integration-84hif1_r`. Every file:line below is under `C`
unless an absolute path is given.

---

## Summary

- **BLOCKING: 1 finding (F1).** It is an **unresolved human decision**, not a coding error.
  The parity harness enforces the literal rule ("no single deviation above 5%, residual
  within 0.5%"), so stacking declared deviations lets any discrepancy pass as
  `"workload parity"`. A 2× matrix_ops error passes. This must be decided and pinned by a
  test before U0002 is accepted, because accepting U0002 as written makes the loophole
  accepted policy for U-P3 and G2(c).
- **NON-BLOCKING: 15 findings (F2–F16).** Eleven are implementation defects or gaps
  (F2–F7, F10–F14). Two are human decisions (F8, F9). One is documentation (F15). One is
  later-sprint work (F16). Highest priority among the non-blocking: F2 (the harness labels
  results `"workload parity"` by default), F3 (CI never checks GENERATOR.json, so oracle
  generator drift goes unnoticed), and F4 (the U0001 pin check passes when U0001 is missing).
- **Sequencing note for the human approver.** F3 through F7 and F10–F11 all suggest changes to
  `scripts/vendor_rk.py`. Any change to that file alters `script_sha256`. Making that
  fingerprint match was the stated reason for generating candidate `6b0d69c5…`. If the
  candidate is adopted first and Stage 2 fixes the script afterwards, the adopted
  GENERATOR.json goes stale immediately. Decide the fingerprint policy (F3) and land the
  generator fixes before choosing what to adopt.
- **Synthetic success is not presented as U2 workload parity anywhere in the reviewed
  tree.** Every current caller, the CI step name and every doc label the echo/mutant run as
  a harness self-test. The risk is in the API: F2 shows the harness stamps
  `"workload parity"` on an oracle echo when the caller leaves out `self_test=True`. F8
  shows the table's `flop_parity` carrier cannot record the distinction at all.
- **The reported results reproduce independently:** 153 strict and 157 full tests pass,
  and mypy, ruff, import-linter, schema freshness and `vendor_rk.py --check` are all clean.
  A local cold-clone approximation also passes. **Pending:** hosted CI, a real cold clone on
  the Linux box, the human publication/adoption step, and ADR acceptance.

---

## Checks performed

All commands ran with `UARCH_HUMAN` unset. I never ran vendor generation. Every probe ran in
a disposable copy under my session scratchpad (`…/scratchpad/rv`, `…/scratchpad/probes/*`,
`…/scratchpad/cold*`). The candidate, evidence, worktrees, snapshots and coordinator were
not written to. A preservation check at the end confirms this.

### C1. Independent rerun in a disposable copy (`uv sync --locked --extra dev --offline`)

```text
$ uv run --no-sync python -B scripts/vendor_rk.py --check
committed snapshot manifest and matrix verified: …/scratchpad/rv/contract/vendor/rk-sim@1e5706e…
$ uv run --no-sync pytest -q -rs contract/tests --require-vendor     153 passed
$ uv run --no-sync pytest -q -rs                                      157 passed
$ uv run --no-sync python -B -m uarch_contract.generate --check        Contract schemas are fresh.
$ uv run --no-sync mypy src contract scripts                           Success: no issues found in 42 source files
$ uv run --no-sync mypy            (what CI runs)                      Success: no issues found in 30 source files
$ uv run --no-sync ruff check .                                        All checks passed!
$ uv run --no-sync lint-imports                                        Contracts: 2 kept, 0 broken.
```

### C2. Local cold-clone approximation (hosted CI and the Linux box remain PENDING)

I copied the candidate into a scratch directory, ran `git init` there, committed in that
scratch repository only, and ran `git clone`. In the clone I ran the CI `contract` job steps
and the CI `python` job's pytest selection:

```text
git ls-files contract/vendor | wc -l          → 20  (19 snapshot files + README.md)
git ls-files -s contract/vendor (modes)        → 20 × 100644  (0444 is not preserved; see F14)
vendor_rk.py --check                           → verified
pytest -q -rs contract/tests --require-vendor  → 153 passed
python -m uarch_contract.generate --check      → Contract schemas are fresh.
pytest -m "not nightly and not silicon and not native and not golden and not determinism" → 157 passed
git status after the runs                      → clean (tests write nothing into the tree)
```

This ran on WSL2 Linux. It was not on the self-hosted "Linux box" and was not hosted GitHub
Actions. It does not establish the U-REVIEW check-1 result.

### C3. Identity and change-set verification

- I exported the baseline with `git archive 89313ee` into the scratchpad and ran
  `diff -rq` against `C`. The changed and added paths are consistent with the 132
  operations in `assembly.json` (spot-checked by lane, not path-by-path). Lane B's 21 files in `C` are byte-identical to the Lane B worktree,
  except `Makefile`, which is the recorded clean three-way merge with A.
- The snapshot in `C` is byte-identical to `/tmp/u1-vendor-final-f96kn1fp`. Its MANIFEST
  SHA256 is `6b0d69c5…8304`. All 19 files are mode 0444. Decode and prefill have 432
  records each, and there are 6 component/precision groups of 144.
- Comparing the prior snapshot (Lane B, `4caea65f…3284`) with the candidate, only
  `GENERATOR.json` (`script_sha256` e13b497b… → 69a3e31f…) and `MANIFEST.json` differ.
  Every oracle and refusal byte is identical.
- `GENERATOR.json.oracle_program_sha256` equals `sha256(ORACLE_PROGRAM)` in `C`, and
  `script_sha256` equals `sha256(C/scripts/vendor_rk.py)`.
- The nine vendored `rk/` sources, `schema.json` (= upstream `web/src/schema.json`, which
  rk-sim's `make gen` writes) and both component YAMLs are byte-identical to the pinned
  checkout. The vendored modules' `rk.*` import closure is exactly the nine-file `SOURCES`
  list.
- The pinned checkout is clean, and `git ls-files -v` shows no skip-worktree or
  assume-unchanged flags. This matters for F6.

### C4. Oracle semantics (read-only reading of the pinned rk-sim)

- `IterationCounts` is documented as "Unsharded work". In the fixtures, counts are
  identical for tp=1 and tp=8 in all 432 groups, and `duration_s(tp=8)·8 == duration_s(tp=1)`
  holds exactly in all 432. This is consistent with `counts_scope: replica` and
  `duration_scope: one_tp_rank_no_collectives`, given `IterationCost._time_s` = max(roofs)/tp + collective(0).
- Every decode `memory_write_bytes` is `null`. There are no zero `matrix_ops`, and all counts
  are floats.
- The harness's replica-to-rank projection (`parity.py:71-75`, value/tp, None preserved)
  matches rk-sim's own representative-rank export: `rk/engine/f0/channels.py`
  `analytical_channels` uses `value / tp` and keeps None as `Unavailable`.
- Channel mapping: the vendored `Channel` Literal contains `matrix_ops`, `vector_ops`,
  `memory_read` and `memory_write`. rk-sim requires unit `op` for `*_ops` channels and `byte`
  for memory channels, so a name-only map is unit-consistent.
- The refusal records come from `iteration_cost()` raising `UnsupportedPrecision`. rk-sim's
  real dispatch path (`_accelerator`) wraps the same refusal in `EngineError`. The recorded
  type matches the U-P2 text.
- The oracle durations assume `dvfs=None` and `hbm_kv_bytes=None` (no system-level DVFS, no
  CXL spill). The orchestrator only adds these from system config, not from the component,
  so this is in scope. The `omissions` label does not state it (informational only).

### C5. Sourced model-shape sidecars

I fetched all three cited immutable-revision `config.json` URLs. Their SHA256s equal the
recorded `sha256` values, and every sidecar dimension equals the config (n_layers, d_model,
heads, kv_heads, d_ff, vocab, tie, experts, top-k, head_dim). A's `check_parity` passes.
Nominal versus shape-implied counts (from A's `implied_params`): llama-3.1-8b −0.0033%,
llama-3.1-70b +0.066%, mixtral-8x7b active **+0.156%** (see F9). Snapshot sidecars are
byte-identical to `contract/fixtures/model_shapes/*.json`.

### C6. Differential validator testing: vendored rk-sim classes vs. uarch classes

- `SourcedValue`: I ran 8,400 claim payloads (value × unit × provenance × source × date
  combinations, including non-finite, bool, string, blank and missing values). **54 diverge,
  and all 54 are `provenance=stub` with source `""`, `" "` or `"\t\n"`** (upstream accepts,
  uarch rejects). This is exactly the documented proposed exception, and nothing else
  diverges. No payload is accepted by uarch and rejected by rk-sim, so uarch's acceptance set
  is a subset of rk-sim's for five-field claims. The pinned library contains **0** blank
  stub sources (`grep` of `rk/components/library`), and the placeholder uses
  `source: null` throughout. The exception has no current data impact.
- `ModelSpec`: 15 boundary mutations (active>total, kv_heads not dividing, d_model%heads,
  MoE inconsistencies, zero, float/str/bool coercions, extra key, 2**70) showed **0
  divergences**.
- Both lockfiles pin pydantic 2.13.5 / pydantic-core 2.46.5. The path-loaded vendor classes
  run under uarch's pydantic. The versions match today by coincidence, not because anything
  checks it (see F7).

### C7. Failure probes beyond the existing tests

Each probe used a fresh copy of the review tree. Outcomes:

| Probe | Mutation | `--check` | strict suite | Expected | Finding |
|---|---|---|---|---|---|
| A1 | delete U0001 | exit 0 | 153 passed | fail | F4 |
| A2 | rename U0001 | exit 0 | 153 passed | fail | F4 |
| A3 | wrong pin on U0001 `**Reference:**` line (control) | exit 1, names pin | — | fail | ok |
| A4 | `RK_SCHEMA_SNAPSHOT` = `b…b` | exit 0 | 153 passed; gen-check fresh | fail | F4 |
| B | oracle program `duration_s * 2` | exit 0 | 1 failed (synthetic bridge test, incidental) | fail | F3 |
| B2 | oracle program `tp=tp` → `tp=1` | exit 0 | 153 passed; full 157 passed | fail | F3 |
| K5 | GENERATOR.json `rk_sha=c…c`, `counts_scope=per_rank`, oracle fp zeroed (+manifest) | exit 0 | 153 passed | fail | F3 |
| L1 | orphan `components/npu-l4.yaml`, no fixture rows (+manifest) | exit 0 | 153 passed | fail | F5 |
| K1 | snapshot root replaced by symlink to out-of-tree copy | exit 0 | 153 passed | fail | F10 |
| K2 | hidden extra file `.hidden` | exit 1 "file set differs: ['.hidden']" | — | fail | ok |
| K3 | one flipped byte in `rk/schema/channels.py` | exit 1 "MANIFEST mismatch: rk/schema/channels.py" | — | fail | ok |
| K4 | MANIFEST without `files` | exit 1 (uncaught `KeyError` traceback) | — | fail | ok (cosmetic) |
| N | snapshot directory removed | exit 1 "missing …MANIFEST.json" | 10 errors (non-strict: 10 skipped with reasons) | fail | ok |
| I1/I2 | stale extra schema / edited schema | gen-check exit 1 naming file | — | fail | ok |
| M | generation entry point, `UARCH_HUMAN` unset, `RK=/nonexistent` | exit 1 "human-only vendor operation" | — | refuse | ok |
| H | static `import rk` / `from rk…` / `from contract.tests…` in prod roots | lint-imports BROKEN | — | fail | ok |
| H' | `importlib.import_module('r'+'k')`, path `exec(open(contract/vendor/…))`, `from scripts.vendor_rk import PIN` in prod roots | KEPT | — | fail | F13 |
| E1–E7 | parity harness attribution and labelling probes | — | — | — | F1, F2 |
| G | scratch Git repo: modified file with `skip-worktree`, another with `assume-unchanged` | `check_clone` accepted | — | refuse | F6 |

---

## U-REVIEW checklist

| # | Check | Result |
|---|---|---|
| 1 | Joint exit criterion runs on the Linux box from a cold clone | **PENDING.** G1 = contract CI job green against the toy table, plus fixtures (≥3 ModelSpecs × ≥24 queries), plus U0001 accepted. The local cold-clone approximation passes (C2). Hosted CI and the Linux box are unavailable: there is no self-hosted runner until U3, and the snapshot and code are uncommitted. Fixtures are present in the candidate but not adopted. U0001 acceptance is a human step. |
| 2 | Numbers reaching a human without a badge | **N/A for U1.** There are no report templates, no `uarch report` and no tables (U-P4/U2). The only CLI output path is `vendor_rk.py`, which prints no numbers. Its wording is covered in F11. |
| 3 | Golden changes | **None.** `tests/golden/expected/` holds only `.keep` and shows no diff against the baseline. |
| 4 | Numerical smells | **No defect found.** New names carry units (`duration_s`, `*_bytes`, `deviation_rel`, `max_rel`, `*_sha256`). `matrix_ops` is the verbatim rk-sim name. There are no cycles, time conversions, seeds or randomness. Output ordering is deterministic (sorted file map, `sort_keys`, ordered component/model lists). Null is preserved (decode writes). tp: replica→rank projection only in the test harness (C4); table rules are unaffected. Three formulas re-derived from their docstrings and **matching**: (a) `rank_counts` = replica/tp with None kept; (b) `compare_counts` relative = (actual−ref)/ref, pass if \|rel\| ≤ 0.005 or \|rel − Σdeclared\| ≤ 0.005 (matches U0002 §6 text; see F1 on intent); (c) query inputs T = n·L, Q = Σ S_i² = n·L², decode total_context = B·t. Engine, native, DRAM-preset, HashMap and `unsafe` items: **N/A** (no engine or native code in U1). |
| 5 | Provenance | No stipulation outside `hw/designs/`: the only stipulations are in-memory test values. No hardware claim was added. Nominal model parameter counts are unsourced inputs (F9). Reference specs and derived values: **N/A** (none exist). |
| 6 | Evidence, model cards, predictions, `check_ordering` | **N/A.** There are no model cards, ledger entries or predictions. `validation/L3_silicon/check_ordering.py` does not exist yet, and CI's ordering job reports "nothing yet". |
| 7 | Fidelity / composite C2 / U-C0 floor | **N/A.** There are no engines, composites or rows. |
| 8 | Determinism (golden table at workers 1 vs N) | **N/A.** There is no golden table or engine. Generator determinism: the synthetic double collection is byte-identical (test passes). The human's two runs are Javid-reported and not evidenced by tool output (F11). |
| 9 | Native vs fork harness | **N/A** before U6. |
| 10 | Scope (§1.3 out-list) | **OK.** No mapping search, SIMD, GPU, MPI, optimistic sync, compiler, web UI, ONNX or new workload IR. Sidecars are fixtures. No new dependencies (pyproject diff only adds pytest `pythonpath` and ruff/mypy vendor exclusions). |
| 11 | READMEs still true | `contract/vendor/README.md` is incomplete or stale against the delivered layout and the adoption lifecycle (F15). The other touched READMEs are true. |

---

## Findings

Format: **severity** · class (implementation defect / human decision / later sprint) ·
location · reproducer (observed output) · proposed regression test.

Common reproducer setup (any disposable copy):

```bash
P=$(mktemp -d) && (cd /tmp/u1-final-integration-84hif1_r && \
  tar --exclude=./.venv --exclude='__pycache__' -cf - .) | tar -xpf - -C "$P" && \
  cd "$P" && env -u UARCH_HUMAN uv sync --locked --extra dev --offline
SNAP=contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963
# then: env -u UARCH_HUMAN uv run --no-sync <command>
```

### F1: BLOCKING · human decision (spec loophole; the implementation matches the literal text) · stacked declared deviations let any discrepancy pass as workload parity

- **Location:** `/tmp/u1-final-integration-84hif1_r/contract/tests/parity.py:28-32` (5% cap
  applied to each `Deviation` alone), `:63-66` (Σ of same-channel deviations used as the
  attribution), `:43-46` (dedup by id only); policy text
  `/tmp/u1-final-integration-84hif1_r/docs/decisions/U0002-the-vendored-snapshot-and-parity-discipline.md:86-93`.
- **Problem:** The cap bounds each declared deviation, not their sum. Any number of 5%
  deviations on one fixture/channel can be declared, so the effective tolerance is
  unbounded. Over-declaration and cancelling pairs are also accepted silently, and the report
  then lists the deviations as if they had explained something.
- **Reproducer** (`uv run --no-sync python -B -`):
  ```python
  import json; from pathlib import Path
  from contract.tests.parity import Deviation, compare_counts, run_parity, rank_counts
  rows = json.loads(Path('contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963/parity/fixtures.json').read_text())
  row = next(r for r in rows if r['model_id']=='llama-3.1-8b' and r['tp']==8 and r['query']['phase']=='decode')
  def doubled(*a):
      c = rank_counts(row); c['matrix_ops'] *= 2.0; return c
  devs = {row['id']: [Deviation(f'slice-{i}', 'matrix_ops', 0.05, 'stacked') for i in range(20)]}
  print(run_parity([row], doubled, deviations=devs))
  ```
  Observed: `E1 2x error with 20x5% stacked deviations -> workload parity max_rel 1.0` (passes).
  Also observed:
  - E3: an exact match carrying an unused 4.9% "phantom" deviation passes, and the report
    lists it.
  - E4: actual +0.4% with declared +4.5% passes.
  - E5: declared +5% and −5% on an exact match passes.
  - E7: a deviation on the null `memory_write_bytes` channel is accepted.
- **Why it matters now:** G2(c) and U-P3 acceptance 3 will use this harness. Concrete
  pressure exists: these fixtures' `active_params` include the untied input-embedding
  table, which is **6.54%** of llama-3.1-8b (128256·4096 / 8.03e9), 1.49% of 70b and 1.02% of
  Mixtral. If U-P3's graph does not count the embedding gather as matrix ops, its one honest
  deviation on small-context decode fixtures exceeds the 5% cap, and the harness rewards
  splitting it into two.
- **Decision needed (Javid) before U0002 acceptance:** whether "no deviation above 5%"
  bounds |Σ declared| per fixture/channel, and whether declared deviations must be needed
  (actual outside tolerance), same-signed and on a non-null channel.
- **Proposed regression tests:** `test_stacked_deviations_cannot_exceed_cap` (20×5%
  declared, 2× actual → AssertionError/ValueError); `test_unneeded_deviation_is_refused`
  (exact match plus a declared deviation → error); `test_deviation_on_null_channel_is_refused`.

### F2: NON-BLOCKING (high) · implementation defect · the harness labels results "workload parity" by default

- **Location:** `/tmp/u1-final-integration-84hif1_r/contract/tests/parity.py:83` (`self_test: bool = False`), `:109`.
- **Problem:** The label comes from what the caller asserts, not from what was compared. An
  oracle-echo callable run without `self_test=True` gets the label of real parity.
- **Reproducer:**
  ```python
  it = iter(rows)
  res = run_parity(rows, lambda m, s, p, q: rank_counts(next(it)))
  print(res['kind'], res['n_fixtures'], res['max_rel'])
  ```
  Observed: `'workload parity' 864 0.0`.
- **Current status:** no current caller or doc misuses it. `contract/tests/test_committed_snapshot.py:43`
  and `test_flop_parity.py:32` pass `self_test=True`. The CI step name says "(not workload
  parity)".
- **Proposed regression test:** `test_run_parity_requires_explicit_kind`. Calling `run_parity`
  without an explicit `kind=` raises. Optionally, `test_oracle_echo_cannot_be_labelled_workload_parity`
  checks that a candidate returning `rank_counts(fixture)` objects for every fixture is
  refused when labelled workload parity.

### F3: NON-BLOCKING (high) · implementation gap plus a fingerprint-policy decision · GENERATOR.json is never validated, so generator drift is invisible to CI

- **Location:** `/tmp/u1-final-integration-84hif1_r/scripts/vendor_rk.py:286-294` (written),
  `:436-441` (`--check` never reads it). `/tmp/u1-final-integration-84hif1_r/contract/tests/test_committed_snapshot.py:20-36`
  (not read there either). The adoption recipe at
  `/tmp/u1-final-integration-84hif1_r/docs/reviews/U1-U-P2-handoff.md:523-567` does not
  compare the target tree's generator digest with the candidate's `script_sha256`.
- **Reproducer B2:**
  ```bash
  sed -i 's/cost = iteration_cost(model, accelerator, precision, tp=tp)/cost = iteration_cost(model, accelerator, precision, tp=1)/' scripts/vendor_rk.py
  env -u UARCH_HUMAN uv run --no-sync python -B scripts/vendor_rk.py --check     # exit 0
  env -u UARCH_HUMAN uv run --no-sync pytest -q contract/tests --require-vendor   # 153 passed
  env -u UARCH_HUMAN uv run --no-sync pytest -q                                   # 157 passed
  ```
  Recorded oracle fingerprint == current program: `False`.
- **Reproducer K5:** rewrite GENERATOR.json with `rk_sha=c…c`, `counts_scope=per_rank` and a
  zero oracle fingerprint, then recompute the MANIFEST entry. `--check` exits 0, and the
  strict suite reports 153 passed.
- **Context:** the docs argue that `script_sha256` "need not match" (U0002 lines 286-290;
  handoff 277-281). The final candidate was nevertheless generated so that it would match.
  This choice needs to be explicit (see the sequencing note in the Summary).
- **Proposed regression test:** `test_generator_metadata_binds_to_committed_generator`.
  It asserts:
  - GENERATOR.json keys are exactly the expected set;
  - `rk_sha == PIN`;
  - the scopes equal every row's scopes;
  - `oracle_program_sha256 == sha256(ORACLE_PROGRAM)`;
  - if the human picks a strict policy, `script_sha256 == sha256(scripts/vendor_rk.py)`.
  Pair it with a mutation test showing the B2 edit fails CI.

### F4: NON-BLOCKING (medium) · implementation defect · the upstream-pin check fails open in strict CI, and the contract's snapshot constant is unbound

- **Location:** `/tmp/u1-final-integration-84hif1_r/scripts/vendor_rk.py:159-161` (returns
  when the ADR is absent). `/tmp/u1-final-integration-84hif1_r/contract/tests/test_committed_snapshot.py:16-17`
  does not consult `--require-vendor` (`contract/tests/conftest.py:17-22`).
  `/tmp/u1-final-integration-84hif1_r/contract/uarch_contract/common.py:8` (`RK_SCHEMA_SNAPSHOT`)
  is not tied to `scripts/vendor_rk.py:20` (`PIN`). This last part is cross-lane: A's
  constant, B's seam test.
- **Reproducer:**
  - `rm docs/decisions/U0001-the-integration-contract.md` (or `mv` it to another name):
    `--check` exits 0 and the strict suite reports 153 passed.
  - Setting `RK_SCHEMA_SNAPSHOT = "bbbb…"`: `--check` exits 0, the strict suite reports 153
    passed, and gen-check reports fresh.
- **Why:** U0002 lines 12-17 allow absence only "during Lane B preparation". After
  integration, absence should be a stop, just like a different SHA (execution-plan U1
  "Depends on").
- **Proposed regression tests:** `test_strict_mode_requires_u0001` (under `--require-vendor`, a
  missing ADR fails); `test_contract_snapshot_constant_equals_vendor_pin`
  (`uarch_contract.RK_SCHEMA_SNAPSHOT == scripts.vendor_rk.PIN`).

### F5: NON-BLOCKING (medium) · implementation gap · the snapshot's own component inventory is not checked against fixture coverage

- **Location:** `/tmp/u1-final-integration-84hif1_r/scripts/vendor_rk.py:352` (in `--check`,
  components are derived from the rows) and `:437-439`.
  `/tmp/u1-final-integration-84hif1_r/contract/tests/test_committed_snapshot.py:24`
  (`validate_matrix(rows)` without the component set).
- **Reproducer L1:** add `$SNAP/components/npu-l4.yaml` and its MANIFEST entry, with zero
  fixture rows. `--check` exits 0 and the strict suite reports 153 passed. This matters for
  U2: a PARAMS component whose 288 rows are missing goes unnoticed. The `--check` CLI also
  skips the row→component digest cross-check that pytest performs. CI runs both, so that
  part is covered.
- **Proposed regression test:** `test_every_vendored_component_has_full_coverage`, which
  calls `validate_matrix(rows, {p.name for p in (snapshot/'components').glob('*.yaml')})`.
  Also check that the model-shape sidecar set equals the row `model_id` set.

### F6: NON-BLOCKING (medium) · implementation defect · the clean-tree check trusts `git status`, which hides flagged and ignored changes

- **Location:** `/tmp/u1-final-integration-84hif1_r/scripts/vendor_rk.py:149-156`.
  `/tmp/u1-final-integration-84hif1_r/contract/tests/test_vendor_tooling.py:128-136`
  (monkeypatched `git`, so it cannot detect this). The claim at U0002 lines 24-25 ("verifies
  … a clean tree") is overstated.
- **Reproducer:** in a scratch Git repo, commit `rk/engine/f0/compute.py`, run
  `git update-index --skip-worktree` on it and edit it, then flag `keep.txt` with
  `--assume-unchanged` and edit that too. `git status --porcelain --untracked-files=all
  --ignore-submodules=none` prints nothing. With `vendor_rk.PIN` set to that repo's HEAD,
  `check_clone` **accepted** the tree even though the executed source differs from HEAD.
  Ignored files are also invisible to the check. With `python -c` and `cwd=rk`, an ignored
  top-level module in the checkout would shadow imports.
- **Current artifacts are unaffected:** the pinned checkout has no flags (C3).
- **Proposed regression test:** `test_check_clone_refuses_skip_worktree_and_assume_unchanged`,
  using a real temporary Git repo. Possible implementation: compare `git hash-object` of
  every copied or executed file against `git rev-parse HEAD:<path>`, and refuse any
  non-`H` entry in `git ls-files -v`.

### F7: NON-BLOCKING (medium) · implementation gap · the oracle environment is neither verified nor recorded

- **Location:** `/tmp/u1-final-integration-84hif1_r/scripts/vendor_rk.py:249-263`
  (`--frozen --no-sync` disables any check of the environment against rk-sim's `uv.lock`)
  and `:286-294` (GENERATOR.json has no Python or package versions and no lock digest).
  This conflicts with U0002 lifecycle step 1, lines 145-151 ("Record … the locked oracle
  environment").
- **Evidence:** the environment named in the handoff, `/tmp/rk-sim-u1-jjaffari-1e5706e`, now
  contains only `.gitignore` and `.lock` and has no `bin/python`. The interpreter and package
  set that produced the 864 values can no longer be identified. The test-side vendor classes
  run under uarch's pydantic, which equals rk-sim's lock today only by coincidence (C6).
- **Proposed regression test:** `test_generator_records_oracle_environment`. GENERATOR.json
  must include the Python version, `importlib.metadata` versions of the locked packages and
  the pinned `uv.lock` SHA256. Optionally,
  `test_round_trip_runs_under_recorded_pydantic` asserts uarch's pydantic version equals the
  recorded one. Adding these fields requires a new human-generated candidate (see the
  sequencing note).

### F8: NON-BLOCKING · human decision (contract seam, A↔B) · the table's `flop_parity` carrier cannot hold the harness's kind or attribution

- **Location:** `/tmp/u1-final-integration-84hif1_r/contract/uarch_contract/table.py:183-191`
  (`FlopParity{max_rel, declared_deviations[{id, deviation_rel, reason}]}`; matches
  build-spec line 354) versus `/tmp/u1-final-integration-84hif1_r/contract/tests/parity.py:108-115`
  (`kind`, `n_fixtures`, per-fixture `{id, channel, deviation_rel, reason}`).
- **Problem:** when U-P3 writes harness output into a table, the self-test/workload-parity
  distinction, the channel and the fixture scope are lost. `max_rel: 0.0` from an echo looks
  the same as real parity. `FlopDeviation.deviation_rel` also has no 5% bound in the
  contract.
- **Decision:** settle this before G1 freezes the contract, or record it explicitly as a U2
  MINOR bump.
- **Proposed regression test (if adopted):** `FlopParity` requires
  `kind ∈ {harness_self_test, workload_parity, not_run}`, and each deviation carries
  `fixture_id`, `channel` and a bounded `deviation_rel`.

### F9: NON-BLOCKING · human decision · nominal ModelSpec parameter counts are unsourced inputs that drive the oracle directly

- **Location:** `/tmp/u1-final-integration-84hif1_r/contract/fixtures/model_shapes/llama-3.1-8b.json:4,12`,
  `llama-3.1-70b.json:4,12`, `mixtral-8x7b.json:4,12`. `sources[].fields` omits
  `active_params`/`total_params`, and the `parameter_count_note` gives no URL.
- **Problem:** rk-sim's dense term is `2·active_params`, so these rounded numbers become
  oracle values. Measured offsets from shape-implied counts: Mixtral active
  **+0.156%** (12.9e9 vs 12,879,925,248) and 70b +0.066%. U-P3's graph computes from shape,
  so these offsets use part of the 0.5% budget before any real deviation (Mixtral uses about
  31%). They are honest and bounded by `check_parity` (1%), but they are a choice.
- **Decision:** keep the nominal values and plan a named U-P3 deviation, cite a source for
  them, or switch to exact implied counts (which requires regeneration).
- **Proposed regression test:** `test_nominal_param_offsets_are_recorded_and_bounded`, which
  asserts that each sidecar's |nominal−implied|/implied is below a stated threshold that
  the human chooses.

### F10: NON-BLOCKING (low) · implementation defect · `check_manifest` accepts a snapshot root that is itself a symlink

- **Location:** `/tmp/u1-final-integration-84hif1_r/scripts/vendor_rk.py:199-219` (symlinks
  are refused only below the root).
- **Reproducer K1:** replace `$SNAP` with a symlink to an out-of-tree copy. `--check` exits 0
  and the strict suite reports 153 passed. Local validation can pass while the tree would
  commit only a link. In CI the link would dangle or point elsewhere.
- **Proposed regression test:** `test_manifest_refuses_symlinked_root` (root or any
  ancestor under `contract/vendor` is a symlink → ValueError).

### F11: NON-BLOCKING (low) · implementation defect · CLI success messages cannot evidence the rerun and mislabel uncommitted trees

- **Location:** `/tmp/u1-final-integration-84hif1_r/scripts/vendor_rk.py:222-233` and `:451`.
  The same text, "vendored 19 files …; rerun is byte-checked", prints whether the
  destination was created or verified identical. `:440` prints "committed snapshot …
  verified" for any tree, including uncommitted copies (FINAL-VALIDATION also flags this).
- **Effect:** U-P2 acceptance 5 ("run twice … byte-identical") rests only on Javid's report
  (handoff line 59). The tool's own output cannot distinguish the second run's comparison
  from a fresh creation.
- **Proposed regression test:** `test_publish_reports_created_vs_verified`.
  `publish_snapshot` returns `"created"` or `"verified-identical"`, and `main` prints
  distinct messages. `--check` should say "snapshot manifest and matrix verified" without
  "committed".

### F12: NON-BLOCKING (low) · implementation gap · CI type-checks only 30 files and skips the Lane B deliverables

- **Location:** `/tmp/u1-final-integration-84hif1_r/.github/workflows/ci.yml:16` (`uv run mypy`)
  with `/tmp/u1-final-integration-84hif1_r/pyproject.toml:49` (`files` = src/rkuarch,
  contract/uarch_contract).
- **Evidence:** `uv run mypy` checks 30 files; `uv run mypy src contract scripts` checks 42.
  `scripts/vendor_rk.py` and `contract/tests/*` are type-checked only in local evidence runs.
- **Proposed regression test:** have CI run `uv run mypy src contract scripts`, or extend
  `[tool.mypy].files`. Add a CI-config test asserting that the scripts path is covered.

### F13: NON-BLOCKING (low) · implementation gap · vendor isolation is static-only

- **Location:** `/tmp/u1-final-integration-84hif1_r/.importlinter:8-17`.
- **Reproducer H':** each of the following, appended to `src/rkuarch/__init__.py` and
  `contract/uarch_contract/sourced.py`, leaves lint-imports at "2 kept, 0 broken":
  - `importlib.import_module('r'+'k')`
  - `exec(open('contract/vendor/rk-sim@…/rk/provenance.py').read())`
  - `from scripts.vendor_rk import PIN`

  Static `import rk`, `from rk…` and `from contract.tests…` are correctly reported BROKEN.
- **Proposed regression test:** `test_production_roots_never_reference_vendor_paths`, a
  source scan of `src/` and `contract/uarch_contract/` for `contract/vendor`, `rk-sim@`,
  `VendorLoader`, `import_module(` and `scripts.vendor_rk`. Add `scripts` to the forbidden
  modules.

### F14: NON-BLOCKING (low) · human decision / documentation · "read-only (chmod a-w)" does not survive Git

- **Location:** U-P2 1b (`/tmp/u1-final-integration-84hif1_r/docs/prompts/U-P2-vendored-snapshot-and-parity.md:17-18`);
  `/tmp/u1-final-integration-84hif1_r/docs/decisions/U0002-the-vendored-snapshot-and-parity-discipline.md:99-100`.
- **Evidence:** C2. Git records all 20 vendor paths as `100644`, and a clone has 0644 files.
  Directories are never write-protected, even locally. Nothing in CI checks the mode. The
  real protection is MANIFEST, the human-owned pre-commit hook and CODEOWNERS.
- **Decision:** accept that protection model and reword U-P2 and U0002, or add a check.
- **Proposed regression test (if a check is wanted):** a CI step asserting that
  `git ls-files -s contract/vendor` and the manifest are unchanged except in commits marked
  as human adoption. Otherwise none: documentation only.

### F15: NON-BLOCKING (low) · documentation · stale or ephemeral statements in Lane B docs and README

- **Location and issues:**
  - `/tmp/u1-final-integration-84hif1_r/contract/vendor/README.md:1-6` lists neither
    `GENERATOR.json`, `components/`, `model_shapes/` nor `parity/refusals.json`. It says the
    snapshot is "Written only by `make vendor-rk`", but the reviewed lifecycle adopts a
    candidate by directory rename. This is U-REVIEW check 11.
  - `/tmp/u1-final-integration-84hif1_r/docs/decisions/U0002-the-vendored-snapshot-and-parity-discipline.md:222-239,252-293`
    cites `/tmp/...` and home paths as evidence identities and keeps superseded counts
    ("33 passed, 5 skipped", "111/115", "Lane B's own tree still lacks A's models") inside an
    ADR intended for commit.
  - Neither U0002 nor the U-P2 handoff references U0019, although U0019 (lines 129-131) asks
    U1 workers to carry its ownership reference.
- **Proposed regression test:** `test_vendor_readme_lists_snapshot_layout`, asserting that
  every top-level snapshot entry is named in `contract/vendor/README.md`. The ADR wording is
  a documentation fix; no test.

### F16: NON-BLOCKING · later sprint (U0003 / U-P3, U2) · PARAMS precision set and prepared-input parity are not yet covered

- **Location:** `/tmp/u1-final-integration-84hif1_r/scripts/vendor_rk.py:40,44-45` (PARAMS
  components always run FP16/FP16 and FP16/FP8, and any unsupported precision fails the whole
  generation) and `/tmp/u1-final-integration-84hif1_r/contract/tests/parity.py:3-7`
  (callable signature `(ModelSpec, ModelShape, precision, query)`).
- **Issues:**
  - U-P3 builds `npu-l4` tables at bf16 (build-spec U-P3 acceptance 5). An npu-l4 component
    without an FP16 peak cannot be vendored, and no bf16 oracle exists for it.
  - Under U0019, the parity path for prepared or imported OpSpec bundles is unspecified.
- **Owner:** both belong to U0003 and U-P3, not U1. Record them there.
- **Proposed regression test (U2):** a PARAMS precision declaration per component that is
  validated against the component's declared peaks, and a parity adapter test for one
  prepared bundle.

---

## Claims verified, attributed or pending

| Claim (source) | Status |
|---|---|
| 153 strict / 157 full, no skips (FINAL-VALIDATION) | **Verified** (C1, C2) |
| mypy 42 / ruff / import-linter 2 kept / gen-check / vendor `--check` | **Verified** (C1). CI's own mypy covers 30 files (F12) |
| Candidate = 19 files, mode 0444, manifest `6b0d69c5…` | **Verified** (C3). Mode does not survive Git (F14) |
| Only GENERATOR.json and MANIFEST.json differ from the prior snapshot | **Verified** (C3) |
| 864 records = 6×144; six G2(c) decode points; two refusals | **Verified** |
| Vendored sources, schema bundle and components byte-identical to the clean pin | **Verified** (C3) |
| Sidecars sourced at immutable revisions, digests recorded | **Verified** against live fetch (C5) |
| Counts replica-scoped; durations one rank without collectives | **Verified** numerically and from source (C4) |
| Exact four-entry Channel map; name-only; null kept | **Verified** (C4, existing tests) |
| Stub-source divergence is narrow and explicit | **Verified** by differential (C6). Acceptance remains Javid's decision |
| Javid ran generation twice with byte-identical output | **Attributed only.** Not verifiable from artifacts or tool output (F11) |
| `contract` CI job green on hosted runners | **PENDING.** Not run; the snapshot is uncommitted |
| Joint exit criterion on the Linux box from a cold clone | **PENDING.** Local approximation only (C2) |
| U0001 / U0002 acceptance; adoption; publication; G1 | **PENDING** human steps. Not assessed as complete |

## Preservation

After all checks:
- All 253 files in `/tmp/u1-final-integration-84hif1_r` match `validated-tree-inventory.json`
  (0 changed).
- The coordinator is clean at `89313ee`.
- The Lane A and Lane B worktrees are at `af3b1bc` with their original uncommitted proposals.
- `rk-sim-u1-pin` is clean at `1e5706e`.
- `/tmp/u1-vendor-final-f96kn1fp/contract/vendor` has nothing newer than the evidence.

I did not regenerate, adopt or edit any artifact or ADR, and I made no commits in any real
repository. The only commit was inside a throwaway scratch repository used for the
cold-clone approximation.

---

## Stage 3 · ADJUDICATION (2026-10-06)

Reviewer: the Stage 1 reviewer above. I did not author any Lane A or Lane B code, docs or
artifacts. Per U-REVIEW Stage 3, this section checks the response only: (a) every finding
has a row, (b) rejections are reproducer-backed, (c) applied changes have regressions that
fail without them. It does not open a new review. Observations noted below are not new
findings.

| Input | Path / identity |
|---|---|
| Author response | `/home/jjaff/AI-infra-simulation/rk-uarch-u1-b/docs/reviews/U1-lane-B-response.md` |
| Updated handoff | `/home/jjaff/AI-infra-simulation/rk-uarch-u1-b/docs/reviews/U1-U-P2-handoff.md` |
| Updated combined candidate | `/tmp/u1-b-scope-integration-3d8bfs06` (abbreviated `N` below) |
| Validation evidence | `/tmp/u1-b-scope-evidence-5st8n19o/` |
| Revised generator | `N/scripts/vendor_rk.py`, SHA256 `4d2304002b262f2ee03dfe4f8fb338b350aacd80ea2488952849c416ee135317` |
| Oracle bridge | `ORACLE_PROGRAM`, SHA256 `9dd67d4883206f14b8a5a00fa3d0ced95bddaa395ba634d80e08a39813ea04fb` (unchanged) |
| Snapshot in `N` | byte-identical to `/tmp/u1-vendor-final-f96kn1fp` (manifest `6b0d69c5…8304`). Historical, not current. |

### Verdict

**NOT ACCEPTED: rows F3 and F7 are held open, pending replacement-artifact evidence.
Every other row is ACCEPTED.**

The response does not fail the three checks. All rows are present, nothing is REJECTED, F16
is a properly formed deferral, and every applied change has a regression that fails when
the change is reverted. F3 and F7 are held open because they cannot be closed by code
alone:

- **F3** (CI binds the generator fingerprint) works. That is exactly why the committed
  snapshot now fails it.
- **F7** (environment verified and recorded) has run only synthetically and against my
  toy environment. No real oracle-environment inventory has been provisioned or verified.

As instructed, I do not accept them because regeneration is planned. Re-adjudication is
limited to F3 and F7, against the evidence listed below. Humans should not tag `u01-end` on
this verdict. The integrated strict suite is currently not green by design (378 passed /
1 failed), so hosted CI would fail until a compatible replacement is published together
with this code.

**Finding status**

| Status | Rows |
|---|---|
| **Resolved** (code, tests or documentation verified; no artifact needed) | F1, F2, F4, F5, F6, F8, F9, F10, F11, F12, F13, F14, F15; cross-lane A-F12 |
| **Applied and test-verified; OPEN until replacement-artifact evidence exists** | **F3, F7** |
| **Deferred** (deferral accepted; owner and acceptance recorded) | F16 |

### Checks performed in Stage 3

All runs used disposable copies under my session scratchpad, with `UARCH_HUMAN` unset. I
generated no vendor artifact and executed no rk-sim code.

1. **Identity.**
   - All 23 Lane B paths in `N` are byte-identical to the Lane B worktree. `Makefile` is the
     exception: it is the recorded A+B merge.
   - The generator hash is `4d2304…`, and `ORACLE_PROGRAM` is unchanged.
   - Sidecars are unchanged against the Stage 1 target.
   - `PINNED_UV_LOCK_SHA256` (`d984e557…7577c`) equals both `sha256(uv.lock)` and
     `git show HEAD:uv.lock` at the pin.
   - `uv 0.12.9` supports `sync --check` and `--no-default-groups`.
2. **Independent rerun** (`uv sync --locked --extra dev --offline` in a copy of `N`):
   ```text
   pytest -q -rs contract/tests --require-vendor   → 1 failed, 378 passed
   pytest -q                                       → 1 failed, 382 passed
   only failure: test_current_snapshot_generator_compatibility
     "GENERATOR current incompatibility: generator script fingerprint differs; locked oracle environment metadata missing"
   vendor_rk.py --check                            → exit 1 (same message)
   vendor_rk.py --check --historical               → exit 0 "historical integrity and recorded identity ONLY; current compatibility not checked"
   mypy src contract scripts (CI command)          → no issues, 47 files
   ruff / lint-imports / generate --check          → pass / 2 kept 0 broken / fresh
   ```
   This matches the response's reported totals.
3. **Revert checks.** The selected fix was F1, since it was the blocking finding. I also
   reverted other fixes one at a time, each in its own scratch copy. Every revert makes
   the named regressions fail, beyond the deliberate compatibility failure:

   | Reverted fix | Failing regressions without the fix |
   |---|---|
   | **F1 (selected):** remove total-absolute cap, unnecessary and null/zero refusals; restore old pass rule | 8: `test_f1_stacking_is_capped_per_fixture_channel`, 5× `test_f1_unnecessary_null_zero_and_cancelling_adjustments_refused`, `test_f1_boundaries_and_four_reported_quantities`, `test_over_budget_stays_failed_and_later_fixture_is_reported`. The original reproducer passes again: `2x with 20x5% -> workload parity passed 1.0` |
   | F2: default `self_test=False` | `test_f2_default_cannot_claim_workload_parity` |
   | F3: disable current-compatibility block | 2× `test_f3_metadata_tampering…`, `test_f3_program_drift_fails_current…`, `test_f7_environment_metadata_is_required…` |
   | F4: absent ADR returns; constant check off | `test_f4_absent_adr_requires_explicit_preparation`, `test_f4_strict_integration_binds_adr_and_contract[missing,renamed,wrong_constant]` |
   | F5: matrix from rows only; sidecar inventory off | `test_f5_inventory_must_match_matrix[orphan_component,orphan_model]` |
   | F6: index-flag and ignored-file refusals off | `test_f6_real_index_flags_and_ignored_shadow_refused[--skip-worktree,--assume-unchanged,ignored]` (real Git index) |
   | F7: pre-execution environment verification removed | `test_oracle_bridge_synthetic_dispatch_self_test` (before/after count) |
   | F8: adapter defaults a missing kind | `test_f8_adapter_requires_explicit_structured_kind` |
   | F9: parameter record removed | `test_f9_nominal_parameter_offsets_are_recorded_without_correction` |
   | F10: ancestor/root symlink loop off | `test_f10_symlink_root_or_vendor_ancestor_refused[root,parent]` |
   | F11: always return `created` | `test_f11_publish_reports_created_and_verified` |
   | F12: CI back to bare `uv run mypy` | `test_f12_ci_typechecks_b_deliverables` |
   | F13: AST guard narrowed and `scripts` removed from import-linter | 4× `test_f13_dynamic_vendor_access…`. Also, lint-imports goes from "1 broken" to "2 kept" for `from scripts.vendor_rk import PIN` |
   | F14: prompt wording | `test_f14_docs_explain_checkout_modes` |
   | F15: README `uv.lock` entry | `test_f15_vendor_readme_documents_layout_and_lifecycle` |
   | A-F12: guard returns no reasons | 9 failures in `test_projection_scope.py` |
4. **Generator end-to-end strict dry run** (synthetic, in scratch). This closes a coverage
   gap: the existing synthetic bridge test only calls `check_manifest` on its output. I
   used the same fake bridge and fake Git as that test, the real pinned `uv.lock` bytes,
   and an environment record built from the lock, then ran `collect_snapshot` with
   `PARAMS=[]`. Result:
   - `publish 1: created`, `publish 2: verified-identical`, 20 files.
   - `check_manifest`, `check_snapshot_inputs` and `check_generator(current=True)` all
     **pass**.

   The reviewed generator's output format is self-consistent with the strict CI checks.
5. **Real helper code against a real uv environment** (toy Git project depending on
   pydantic 2.13.5, external environment, offline, no rk-sim):
   - In-sync base environment: `check_clone` before and after passes, and no ignored or
     untracked files are created.
   - `verify_oracle_environment` passes.
   - `record_oracle_environment` validates against the lock, including the editable project
     distribution, and is unchanged after execution.
   - An environment provisioned with `--extra dev` is **refused**.
   - With two same-named projects, `uv sync --locked --check` refuses an editable install
     pointing at a different checkout (exit 1, "environment is outdated"). The new `-I`
     no longer puts the checkout on `sys.path`, so this before/after check is what binds
     the executed `rk` to the verified checkout.
6. **A-F12 reproducer** on the unreverted candidate: the 70B shape, tp=16, kv_heads=8 →
   `outcome: failed`, coverage `unsupported_projection` ("kv_heads=8 requires replication
   at tp=16"). The candidate is **never called**. All 864 preserved fixtures remain
   eligible (`test_all_864_preserved_fixtures_retain_supported_coverage`).

### Assessment of the requested items

- **Approved absolute deviation budget (F1).** `parity.py:compare_counts` and A's
  `ParityChannelComparison` enforce the approved policy identically:
  - Σ|dᵢ| ≤ 5% per fixture/channel, and |raw − Σdᵢ| ≤ 0.5%.
  - Adjustments are refused inside raw tolerance and on zero or null references, and both
    signs consume the budget.
  - The four quantities are reported separately, and the carrier re-derives them.
  - My F1 reproducer now fails. Reverting brings it back.
- **Comparison classification (F2, F8).**
  - The default is `harness_self_test`. An oracle echo serializes as a self-test, including
    the 864×3 preserved comparisons.
  - `contract_payload` requires an explicit structured kind and complete passing coverage.
  - The carrier requires `oracle_manifest_sha256` and identities for `workload_parity`.
  - An explicit `workload_parity` remains a caller assertion (`authenticity:
    caller-declared`). U0002 lines 149-152 require U-P3 to supply identity and independent
    review evidence. That is the correct boundary, not a gap.
- **Strict fingerprint/environment policy (F3, F7).**
  - Three separate questions are checked separately: manifest integrity, recorded identity
    and current compatibility. Strict mode demands exact script and oracle equality plus
    environment metadata. `--historical` is clearly labelled and is not used by CI (the CI
    contract job remains strict).
  - Generation verifies the external environment before and after with `uv sync --locked
    --check`, records it, and refuses drift.
  - Implemented and tested. The artifact evidence is still owed (see below).
- **Carrier integration (F8).**
  - B's adapter targets A's captured carrier (`table.py` `0ddfdc94…`). All 7 carrier tests
    pass.
  - Fixture/channel/unit attribution, declarations and the four quantities survive
    serialization. Partial or nonpassing runs cannot enter the success carrier.
  - A's Stage 3 (`/tmp/u1-independent-reviews/U1-lane-A-review.md`) independently judged
    the carrier sound.
- **Pin checks (F4).**
  - Strict mode requires U0001's single reference line and
    `RK_SCHEMA_SNAPSHOT == PIN` (AST-parsed). Absence is allowed only under explicit
    `--pre-contract`, which pytest refuses to combine with `--require-vendor`.
  - The generation path checks the contract pin before running.
- **Nominal-input documentation (F9).** `docs/reviews/U1-U-P2-nominal-parameters.json`
  records nominal, implied, signed and relative values for all six parameters. The test
  recomputes them from A's `implied_params`. There is no new threshold or automatic
  correction. The values match my Stage 1 numbers.
- **Permission/immutability (F14).** U-P2, build-spec, U0002 and the README now say chmod is
  a local precaution and that Git restores 0644. Integrity rests on manifests, strict
  compatibility, human adoption and Git history. Two tests show 0444 and 0644 both pass
  integrity, and that edited bytes fail in either mode.
- **Cross-lane A-F12.** Resolved as Javid's interim policy: uniform `/tp` is eligible only
  for unreplicated, unpadded shard scope, and everything else is `unsupported_projection`
  before comparison, with complete coverage retained. A's legitimate shapes remain valid.
  This matches A's Stage 3 record ("discharged in this combined revision") and my own
  revert and reproducer check.
- **Embedding accounting.** It is not an exception anywhere. There is no embedding code
  path in `parity.py`. U0002 lines 106-110 and 145-147 state that the ≈6.54% share "cannot
  be split to evade this cap" and that it is a U2 workload-parity scope question. A
  synthetic +6.54% probe stays `failed` (`test_projection_scope.py`).
- **B-F16 deferral: accepted.**
  - The dependency is stated: U0003's component-precision interface and U-P3's
    prepared/imported-bundle adapter under U0019.
  - The owners are named: Lane B vendor/parity maintainer for the matrix, Lane A's U-P3
    owner for the adapter, and the U0003 author for the precision interface.
  - The acceptance requirement is concrete: a BF16-only npu-l4 PARAMS fixture validated
    against its declared compute peak with no substitute, plus adapter coverage of an
    actual prepared bundle.
  - It is recorded in U0002 lines 57-65, the handoff and the response.
  - Carry-forward note (not a finding): the record lives only in Lane B documents, and
    U-P3's context list does not load U0002. When U0003 is drafted at U2 kickoff, its
    prerequisite list should reference this item so the Lane A and U0003 owners see it.

### Evidence required to close F3 and F7

All of it must come from a single human-generated replacement candidate, produced from the
frozen reviewed tree.

1. **Frozen inputs, with hashes recorded before generation:**
   - `scripts/vendor_rk.py` = `4d2304002b26…5317`
   - `ORACLE_PROGRAM` = `9dd67d4883…ea04fb`
   - pin `1e5706e0…9963`
   - pinned `uv.lock` = `d984e557…7577c`
   - unchanged sidecars, and `PARAMS=''`
2. **Verified oracle environment (F7).** An external base-selection environment. Record the
   exit 0 of `uv sync --project <pin> --locked --check --no-default-groups --offline`.
   Record pristine-checkout output: `rev-parse` = pin, empty `status`, `ls-files -v`
   H-only, empty ignored list.
3. **Two human runs (F11 evidence for this candidate).** Logs showing `created: 20 files`
   and then `verified-identical: 20 files`.
4. **Strict compatibility (F3).** In the target reviewed tree, `vendor_rk.py --check`
   exits 0. The strict contract suite and the full suite pass with **zero** failures and
   no skips or xfails. The handoff's `PY_VERIFY` target-checker block passes on the
   candidate.
5. **GENERATOR.json content.** `script_sha256` and `oracle_program_sha256` as above, and
   `environment` present: CPython ≥ 3.12, every package in the pinned lock,
   `uv_lock_sha256` = `d984e557…`.
6. **Classified comparison against both preserved snapshots** (`6b0d69c5…`, `4caea65f…`).
   Expected:
   - changed or added files limited to `GENERATOR.json`, `MANIFEST.json` and the new
     `uv.lock`;
   - 864 records and 2 refusals, with no fixture additions or removals.

   Any changed existing count, duration, null or refusal outcome needs explicit human
   review. It must not be assumed equal.

Adoption approval, publication, hosted CI and the Linux-box cold clone remain separate
pending human steps after this evidence. They do not change F3 and F7 closure.

### Remaining generator-affecting corrections before human generation

**None identified.** The strict dry run (check 4) and the real-environment helper exercise
(check 5) found no defect in generation, metadata, inventory or verification. Two
constraints follow from the approved policy rather than from defects:

- The full-script fingerprint is strict, so **any** later byte change to
  `scripts/vendor_rk.py` invalidates a generated candidate. That includes comments or
  messages, and fixes driven by any later review. Freeze the script at `4d2304…` before
  generating.
- The actual rk-sim environment provisioning, and `ORACLE_PROGRAM` importing `rk` through
  that environment's editable install under `-I`, are exercised for the first time by the
  human run. Both fail closed (environment check or import failure). They cannot produce a
  silently wrong artifact.

### Observations (not new findings)

- The existing synthetic bridge test asserts only `check_manifest` on its output. Check 4
  above supplied the missing strict end-to-end evidence for this adjudication.
- In the F8 revert, removing the `outcome != "passed"` clause alone is not detected,
  because the per-entry status clause still enforces complete passing coverage. The
  protection is redundant, so there is no gap.
- The response's earlier totals (203/207, 360/364) are explicitly superseded by its latest
  section (378/382). That section is consistent with my rerun.

### Preservation (Stage 3)

- The candidate `N` has no files newer than its evidence audit.
- The snapshot in `N` equals `/tmp/u1-vendor-final-f96kn1fp` (manifest `6b0d69c5…`). The
  Lane B snapshot manifest is still `4caea65f…`.
- The coordinator is at `89313ee` with an empty `git status --porcelain` (pre-existing
  ignored caches only).
- `rk-sim-u1-pin` is clean at `1e5706e`, with no ignored files.

I edited no source, artifact, ADR or handoff, set no `UARCH_HUMAN`, and generated or adopted
nothing. The only change I made outside the scratchpad is this appended section.

---

## Stage 3 · F3/F7 re-adjudication (2026-10-06)

This is limited to the two rows held open above. It is not a new review. The earlier Stage 1
and Stage 3 text is preserved unchanged.

| Input | Path / identity |
|---|---|
| Replacement artifact and validated integration | `/tmp/u1-replacement-fzin2pif/staging` (abbreviated `ST`) |
| Saved evidence | `/tmp/u1-replacement-fzin2pif/evidence/` |
| Oracle environment (external) | `/tmp/u1-replacement-fzin2pif/oracle-env` |
| Replacement snapshot | `ST/contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963/`, MANIFEST SHA256 `b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d` |

### Result

**F3: RESOLVED. F7: RESOLVED.** Each closure criterion I listed above is met by the actual
artifact, which I checked independently. I did not rely on the saved logs alone.

### Checks against the closure criteria

All checks were read-only, or ran in my own disposable copy of `ST`, with `UARCH_HUMAN`
unset. I regenerated nothing and executed no rk-sim code.

1. **Frozen inputs.**
   - `ST` without its snapshot directory is byte-identical to the reviewed tree
     `/tmp/u1-b-scope-integration-3d8bfs06`. That tree is unchanged since its audit.
   - `ST/scripts/vendor_rk.py` = `4d2304002b26…5317`, and the sidecars are unchanged.
   - `PARAMS=''` (`evidence/human-operation.sh`), so the snapshot contains only the two
     required components.
   - The snapshot `uv.lock` is byte-identical to `git show HEAD:uv.lock` at pin `1e5706e…`
     (SHA256 `d984e557…7577c`).
2. **Verified oracle environment (F7).**
   - `evidence/oracle-provision.log` shows `uv sync --locked --no-default-groups` on CPython
     3.12.14, installing 27 packages, with `rk-sim` editable from
     `/home/jjaff/AI-infra-simulation/rk-sim-u1-pin`.
   - The preflight, post-generation and after-validation `uv sync --locked --check` records
     all show exit 0 and "Would make no changes". A read-only rerun of that check now shows
     the same (exit 0).
   - The environment inventory is identical at preflight, post-generation and
     after-validation, and equals `GENERATOR.json.environment`.
3. **The real environment record matches the pinned lock** (my own analysis, reading files
   only):
   - CPython 3.12.14, and `uv_lock_sha256` equals the snapshot lock and the pinned upstream
     lock.
   - All 27 recorded `(name, version)` pairs are in the lock.
   - The recorded set equals rk-sim's base-selection closure computed from the lock (markers
     evaluated for Linux CPython 3.12.14, including `uvicorn[standard]`'s extras). My first
     closure walk ignored dependency extras and showed a spurious 5-package gap; that error
     was mine. No rk-sim `dev` extra is present.
   - The record equals the 27 distributions actually installed in the oracle environment
     (dist-info METADATA). That environment has `include-system-site-packages = false`, and
     its `rk-sim` `direct_url.json` is editable at the pinned checkout path.
4. **Two human runs.**
   - `generation-first.log`: `created: 20 files at …`.
   - `generation-second.log`: `verified-identical: 20 files at …`.

   With the revised code, the second message is printed only after the oracle has been
   recomputed and found byte-equal to the existing output. The logs are attributed human
   evidence (`human-operation.sh`). They are consistent with the artifact and with the
   generator's code path.
5. **Strict compatibility (F3).** In my disposable copy of `ST` (`uv sync --locked --extra dev
   --offline`):
   ```text
   vendor_rk.py --check                        → exit 0 "snapshot manifest, matrix and current compatibility verified"
   pytest -q -rs contract/tests --require-vendor → 379 passed (no failures, no skips)
   pytest -q -rs                               → 383 passed (no failures, no skips)
   mypy src contract scripts                   → no issues, 47 files
   ruff / lint-imports / generate --check / prompt-sync → pass / 2 kept 0 broken / fresh / 2 passed
   ```
   This matches the saved logs. `test_current_snapshot_generator_compatibility`, which was
   the deliberate failure above, now passes. `evidence/target-verification-and-comparison.log`
   records the target-tree checker passing on the staged candidate. The staged tree is
   identical to the target, so I re-ran its checker directly; it passes.
6. **GENERATOR.json content.**
   - `script_sha256` = `4d2304…` and `oracle_program_sha256` = `9dd67d…`.
   - `rk_sha` is the pin, and the scopes are `replica` / `one_tp_rank_no_collectives`.
   - `environment` is present and is exactly the record described in item 3.
   - Against the final candidate's GENERATOR.json, the only non-environment change is
     `script_sha256` (`69a3e31f…` → `4d2304…`).
7. **The binding is live against this real artifact.** Each of these mutations, made in
   disposable copies, makes strict `--check` fail:
   - appending one comment line to `scripts/vendor_rk.py` ("generator script fingerprint
     differs");
   - changing one recorded package version to one absent from the lock, with the manifest
     recomputed ("environment package versions differ from the recorded lock");
   - deleting the environment record, with the manifest recomputed ("locked oracle
     environment metadata missing").
8. **Classified comparison against both preserved snapshots** (my own byte comparison,
   agreeing with `evidence/snapshot-comparison.json`):
   - Against the final candidate `6b0d69c5…` and the Lane B snapshot `4caea65f…`: **added**
     `uv.lock`; **changed** `GENERATOR.json` and `MANIFEST.json` only; nothing removed.
   - `parity/fixtures.json` (864 records) and `parity/refusals.json` (2 refusals) are
     **byte-identical** to both.
   - Upstream sources, schema bundle, components and sidecars are unchanged.

   No existing oracle value changed, so no value-change review is required. The replacement
   has 20 files, all mode 0444, no symlinks, and its manifest covers exactly the other 19.
9. **Preservation.**
   - Both old snapshots are intact (`6b0d69c5…` in `/tmp/u1-vendor-final-f96kn1fp` and in
     the reviewed tree; `4caea65f…` in the Lane B worktree).
   - `rk-sim-u1-pin` is at `1e5706e…`: empty status, every index entry `H`, no ignored
     files. This holds now and in the saved before, after-setup and after-verification
     records, and its checkout inventory is identical across preflight, post-generation and
     after-validation.
   - The coordinator is clean at `89313ee`.

### Updated overall Lane B verdict

**ACCEPTED.** This verdict covers Lane B's Stage 2 response under U-REVIEW Stage 3:

| Status | Rows |
|---|---|
| Resolved | F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12, F13, F14, F15, and cross-lane A-F12 (carried forward, plus F3 and F7 above) |
| Deferred (deferral accepted) | F16. Owners and acceptance criteria are recorded in U0002 lines 57-65. Carry it into U0003/U-P3 at U2 kickoff. |

The verdict applies to the combination I verified: reviewed code with
`scripts/vendor_rk.py` = `4d2304…`, plus replacement snapshot manifest `b3a575d0…`. Strict
compatibility requires adopting this complete 20-file directory into a tree whose generator
is byte-identical to `4d2304…`. Any later byte change to that script invalidates the
replacement.

### What this verdict is not

Reviewer acceptance of Lane B's findings is separate from each of the following, and none of
them is established here:

- **Snapshot adoption and first publication.** The replacement is still **unadopted** and
  uncommitted. Adoption needs Javid's explicit approval and the complete-directory procedure
  recording the old/new manifests (`6b0d69c5…`/`4caea65f…` → `b3a575d0…`), reason and
  approval. Publication is a separate human commit.
- **Complete U0002 acceptance.** U0002 remains **proposed**. Javid's specific policy
  approvals do not accept the whole ADR. The narrow stub-source exception remains proposed.
- **Hosted CI.** Not run, because nothing is committed or pushed. The local strict runs above
  are not a hosted result.
- **Linux-box cold-clone validation.** Pending. No self-hosted runner exists until U3, and the
  local scratch-repo approximation from Stage 1 is not that check.
- **G1/U1 closure.** Pending. It also requires U0001 acceptance, the contract CI job green on
  the committed revision, and the human gate decision. Embedding accounting remains an open
  U2 workload-parity question.
- **Tagging.** This verdict does not tag `u01-end`. Tagging is a human step after the gates
  above.

No stage of this review modified implementation or artifacts, set `UARCH_HUMAN`, accepted an
ADR, committed, or declared U1 complete.
