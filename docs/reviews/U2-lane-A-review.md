# U2 · Lane A · Stage 1 adversarial review

Status: STAGE 1 COMPLETE (written incrementally). Stage 1 only; no fixes, no adjudication, no closure.

## Reviewer, target and independence

- Reviewer: fresh Claude Code session (Opus 5.5) started 2026-10-09 from the lane-A Stage 1 launch
  prompt. This session did not author any of the reviewed code.
- Integration repo: `/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration` (branch `u2/integration`).
- Target commit `769a1fef2320430386888bf450af579ea26cf664`, tree `926e3651b1a5f88a5b6d54e19453ce7d206482e8`
  — both verified by `git rev-parse HEAD HEAD^{tree}` at start; `git status --porcelain --untracked-files=no` empty.
- Base (peeled `u01-end`): `1e9e794a84c5173812c23a1cf2fc04b85e6f6831`. Full U2 diff: 7 commits, 670 files, +217259/−533.
- Scratch: an isolated `git clone --no-hardlinks` of the integration repo checked out detached at the
  target (`$SCRATCH/laneA-src`, `$SCRATCH` = this session's private scratchpad under `/tmp/claude-1000/...`).
  All generated outputs, mutation probes and test runs happen there. Small repro scripts/logs are copied to
  `docs/reviews/U2-final-review-A/`.

## Environment and commands actually executed (this session)

All runs: `/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python` (CPython 3.12.14), cwd = scratch clone at the
target, `PYTHONPATH=.:contract:src PYTHONDONTWRITEBYTECODE=1`, private `XDG_CACHE_HOME`/`TMPDIR`/mypy/ruff caches
under the session scratchpad, `pytest -p no:cacheprovider`. Host: ElfinKidsLaptop WSL2, Linux 6.6.87.2. No dependency
installation, network, oracle generation, `UARCH_HUMAN`, hook bypass, adoption, staging, commit or ref movement.

| # | Command (abridged) | Result |
|---|---|---|
| E1 | `python -B -m pytest -p no:cacheprovider -q --tb=short -rs` (whole repo) | **1019 passed, 0 skipped, exit 0**, 216.8 s ([summary](U2-final-review-A/full-suite-summary.txt)) |
| E2 | `ruff check .` (CI `lint` step, `ruff 0.16.9` = uv.lock) | **exit 1, 141 errors** at target; `All checks passed` at base → F1 |
| E3 | `mypy src contract scripts` (CI `typecheck` step, mypy 2.3.1 = uv.lock) | **exit 2** at target; success (47 files) at base → F1 |
| E4 | `mypy` (pyproject `files=`), `uarch_contract.generate --check`, `protocol.generate(check=True)`, `lint-imports` | pass (62 files) · fresh · `stale []` · 2 contracts kept |
| E5 | `e2e_cli.py` public-CLI harness (below) | all steps as expected after three declared harness deltas (A, B, C below) |
| E6 | `independent_formulas.py` on the CLI table | 16 rows / 272 ops, **0 mismatches**, max rel duration error 0.0 |

### E5 — public CLI end to end on the exact target (`U2-final-review-A/e2e_cli.py`, `scaffold.py`, `trap/`)

Grid: decode B∈{1,8} × context/seq∈{17,512}, prefill n∈{1,2} × L∈{32,512}, frequency_ratio∈{0.5,1.0} (16 points),
H1 `hw/designs/npu-l4.yaml`, `--model llama-3.1-8b --precision bf16`, tp1.

1. `uarch table hw/designs/npu-l4.yaml --model llama-3.1-8b --precision bf16 --engine analytic` (U-P3 acceptance 5,
   verbatim) → exit 2: `required: --output, --assumptions, --context, --model-card, --artifact-dir` (F3).
2. `uarch validate hw/designs/npu-l4.yaml` → exit 0. `uarch prepare … --grid … --output prepared.json` → exit 0.
3. Harness delta A (test-only): companions from the committed synthetic scaffolding
   `tests/integration/test_u2_a_replay.py::companions`, plus one synthetic family-registry entry for the H1 spec hash
   (the committed fixture registry names only the tiny test hardware). No real review/evidence.
4. `uarch table <yaml> … --context … --model-card … --artifact-dir … --assumptions …` → **exit 2
   `ArtifactMissing: sha256:3b7186…` (the H1 spec's own hash)** even though the spec is the positional input and is
   embedded in the bundle (F2). Harness delta B: write the spec as a canonical JSON companion into the artifact dir.
5. Fresh table from YAML twice; canonical saved `prepared.json` → `uarch table --prepared-input …` with an import trap
   (`trap/sitecustomize.py`, inherited by the engine subprocess) refusing `rkuarch.workload.prepare`, `rk`,
   nominal-candidate, `tests.u2_comparison`, `tests.u2_refresh`, `scripts.u2_inputs`; JSON hardware with recursively
   **reversed** and **rotated** mappings. Negative trap control (model route under trap) → exit 1, trap log records
   the blocked `rkuarch.workload.prepare` import; the saved replay attempted no trapped import.
   **All five tables byte-identical**: file sha256 `599da91d…fddf3`, `table_hash sha256:01d3d017…5ca2`, identical
   44-file packages. The analytic engine really executed in the replay (subprocess), so this is prepared-input
   analytic replay, not only a captured-result rebuild.
6. Harness delta C: report parent directories pre-created (B's writer requires existing parents).
   `uarch report` default and `--show-unvalidated-predictions` on the fresh and on the trapped replay table:
   byte-identical HTML/MD per mode. No `±` anywhere; default hides every prediction magnitude
   ("magnitude hidden · STUB … error unknown"); opt-in shows `0.015027924352 s · STUB — unvalidated model prediction;
   conditional on stipulated inputs; error unknown`; 1212 "not modelled" labels; energy "unverified".
7. `uarch characterize hw/designs/npu-m256.yaml --model llama-3.1-70b --precision fp8` (tp1) → honest refusal
   `WeightCapacityExceeded: 70553706496 > 32000000000.0`; with `--tp 8 --synthetic-assignment` twice → byte-identical.
8. `--workers 2` → `UnsupportedWorkers: analytic capture supports workers=1` (see check 8).

## Findings

| ID | Severity | Kind | Owner (proposed) | One line |
|---|---|---|---|---|
| F1 | **BLOCKING** (publication gate) | code/CI config | coordinator + B (CI) + A/B (`contract/tests`) | CI `lint` and `typecheck` steps fail on the exact target; pass at base |
| F2 | NON-BLOCKING | code | A (`cli.py`) | `uarch table` refuses its own positional/embedded hardware spec as `ArtifactMissing` |
| F3 | NON-BLOCKING | human-policy + docs | A + B + humans | Documented `uarch table …` exit command cannot run; companions have no public producer |
| F4 | NON-BLOCKING | code + unmet test coverage | A (`engines/protocol.py`, tests) | Result verifier never binds `u_c0_duration_ps`; no per_op ≥ aggregate property test |
| F5 | NON-BLOCKING | unmet test coverage | A (tests) | C10 offline export-binding mismatch branch has no committed regression |
| F6 | NON-BLOCKING | code (independent fixture) / possible human-policy | A (+ both humans: `contract/`) | Committed hand-authored "supported imported fixture" is refused by the public loader as committed |
| F7 | NON-BLOCKING | docs | A (READMEs) + humans (CLAUDE.md) + coordinator (Makefile) | READMEs/Makefile/CLAUDE.md describe table behaviour that is not true at U2 |
| F8 | NON-BLOCKING | human-policy (publication) | coordinator / humans | Normative accepted U0003 package prose is not in Git; ADR links dangle in a clone |

### F1 — BLOCKING: hosted CI on this exact commit will fail `lint` and `typecheck`

- **Requirement.** U0021 / execution-plan U2: fresh GitHub clone plus hosted Ubuntu CI on the **exact same published
  commit**. `.github/workflows/ci.yml:14` runs `uv run ruff check .`; `:16` runs `uv run mypy src contract scripts`.
- **Reproduce** (clean clone at `769a1fe`, tool versions equal to `uv.lock`: ruff 0.16.9, mypy 2.3.1):
  `ruff check --no-cache .` → **exit 1, "Found 141 errors"**; `mypy src contract scripts` → **exit 2**:
  `contract/tests/u2_comparison.py: error: Source file found twice under different module names:
  "tests.u2_comparison" and "contract.tests.u2_comparison"` (errors prevented further checking).
  At base `1e9e794`: `ruff` "All checks passed!", `mypy src contract scripts` "Success: no issues found in 47 source files".
  Logs: [`mypy-ci-form.log`](U2-final-review-A/mypy-ci-form.log), [`ruff-ci-form-by-file.txt`](U2-final-review-A/ruff-ci-form-by-file.txt).
- **Where.** All 141 ruff errors are in newly committed evidence scripts under `docs/reviews/**.py` (e.g.
  `U2-adoption-v2-execution/runtime_driver.py` 41, `U2-artifact-adoption-v2/audit.py` 15,
  `U2-adoption-v1-execution/prepared-replay.py` 14, `U2-A-RR-C1/*.py`) and seven copied historical rk files
  under `tests/fixtures/u2_b/historical-u1/rk/schema/*.py`. The mypy error is caused by the new
  `contract/tests/u2_comparison.py` (added in `a9facbb`) colliding with the new `tests/u2_comparison.py` module name.
- **Observed vs expected.** Observed red CI steps; expected both steps green as at base. The adoption receipts claim only
  "modified-test lint" and `mypy` via pyproject `files=` (which does pass, 62 files) — neither is CI's command.
  The 1019-pass suite does not cover these steps. This is not a product-logic defect, but it blocks the pending U0021
  gate unless fixed or a human changes the CI command/excludes (human-policy for evidence directories).

### F2 — `uarch table` cannot build from a fresh companion directory: its own hardware spec is "missing"

- **Requirement.** U-P3 item 6/9 and D3: high-level request → preparation → engine → table; "Embedded hardware and
  reconstructed request are indexed by their verified content hashes" (`table/artifacts.py:341-343` docstring).
- **Code.** `src/rkuarch/cli.py:238-241` inserts captured artifacts (incl. the bundle) directly into `files.loaded`,
  then runs `_complete_closure(context.context_hash, files)`. The side effect that registers the bundle's embedded
  `hardware_spec` under its hash exists only in `_Files.__getitem__` (`table/artifacts.py:129-133`), which is
  bypassed. Any metric dependency carrying `hardware_leaf` selectors (required by `metric_contributors`,
  `engines/analytic/core.py:306-318`) then resolves the spec from disk.
- **Reproduce.** `e2e_cli.py` step `table_fresh_yaml_without_spec_companion`: `uarch table hw/designs/npu-l4.yaml
  --model llama-3.1-8b --precision bf16 --grid … --engine analytic --assumptions … --context … --model-card …
  --artifact-dir <companions> --output …` → **exit 2 `ArtifactMissing: sha256:3b7186f3…07d9`** (= `spec_hash` of
  the positional H1 spec). Writing the spec as `<hash>.json` into the artifact dir makes the identical command pass.
- **Why tests miss it.** `tests/integration/test_u2_a_replay.py::test_engine_subprocess_and_cli_replay` passes
  `--artifact-dir original/artifacts`, a previously written package that already contains the spec file.
- **Expected.** The CLI registers the embedded/positional spec (as the loader does) or documents the requirement.

### F3 — The documented exit command cannot run; table companions have no public producer

- **Requirement.** Execution plan U2 joint exit (`docs/execution-plan.md:180`) and U-P3 acceptance 5:
  `uarch table hw/designs/npu-l4.yaml --model llama-3.1-8b --precision bf16 --engine analytic` writes a
  hash-stable C0 table; CLAUDE.md:13 documents `uv run uarch table <spec> --model <name> --precision <fmt> --engine …`.
- **Observed.** Verbatim command → exit 2 `required: --output, --assumptions, --context, --model-card, --artifact-dir`.
  No CLI or production module emits an `AssumptionSet`, `ReportContext`, `ModelCard`, family registry or metric
  dependencies; the only producers are test helpers (`tests/integration/test_u2_a_replay.py::companions`,
  `tests/u2_comparison.py::report_package`, `tests/u2_refresh.py::report_package`). The adopted v2 table/report
  exit was produced through `tests/u2_refresh.report_package` (runtime_driver phase `fresh_yaml_order_table_package`),
  not the public `uarch table` command.
- **Assessment.** D3 deliberately requires hash-bound external context, so refusing without companions is accepted
  behaviour; what is missing is an honest public path or documentation of how a user obtains reviewed companions
  (and that today only synthetic test scaffolding produces them). Human-policy choice: accept "test scaffolding only"
  for U2 and document the exact command chain, or add a public companion producer (would be new scope). Uncertainty:
  whether the "…" in the plan's exit text was meant to cover these companions.

### F4 — `validate_engine_result` does not bind `u_c0_duration_ps`; U-P3 acceptance 2 property test absent

- **Code.** `src/rkuarch/engines/protocol.py:138-148` recomputes the max-of-sums aggregate but only compares
  `duration_ps` (per mode) and attribution; `u_c0_duration_ps` is never checked against the aggregate or against
  `duration_ps`. `core.py:247` sets it correctly, so fresh in-process results are right; the gap affects captured
  results and the subprocess transport (`table/build.py:87` trusts this validator for subprocess output) and the
  offline loader (`table/artifacts.py:428`). `contract` only rejects `duration_s < u_c0_duration_s` for C2 rows.
- **Reproduce.** `probe_u_c0.py <prepared.json>`: rehashed result with `u_c0_duration_ps = 2 × duration_ps` →
  **ACCEPTED**; `u_c0_duration_ps = 0` → **ACCEPTED**; control `duration_ps / 2` → refused
  `EngineResultMismatch: duration_ps`.
- **Coverage.** U-P3 acceptance 2 ("per_op ≥ aggregate on every fixture query (a property test over random queries
  too)") has no committed test asserting the inequality (searched `tests/`, `contract/tests` for `u_c0`/aggregate
  property; the only hypothesis test is embedding conservation). My own probe (`probe_property.py`, 76 random points,
  H1/H2, three models, tp∈{1,2,8}, both modes) found **no violation**, so this is coverage/verification, not wrong
  arithmetic. Matters more from U3 when fork/native results flow through the same validator (invariant 6).

### F5 — C10: offline export-binding mismatch branch is untested

- **Code.** `src/rkuarch/table/artifacts.py:201-235` (ExportBinding closure: descriptor bytes/content, truth vs
  re-derived export, losses, design status, projected values).
- **Coverage.** No committed test produces `ComponentBindingMismatch`, `ParamsMismatch: bound export/derivation`,
  `descriptor content/bytes` or `unsupported projection pin` (repo-wide search of test files: zero hits).
  `contract/tests/test_u2_a2_export_consumer.py` exercises B's consumer, not this loader branch.
- **Executed now.** `probe_c10.py`: control actual H1 binding accepted; 10/10 consistently rehashed mismatches
  refused (peak changed, provenance upgraded to `spec_derived`+URL, extra param, efficiency 0.55, losses edited,
  other spec npu-m256, design_status reference, pin changed, other-spec derivation). Behaviour is correct; durable
  regression is missing.

### F6 — The committed hand-authored "supported imported fixture" does not execute as committed

- **Requirement.** U-P3 additional acceptance: "A hand-authored supported prepared fixture executes with no rk-sim
  clone or compiler"; exit text "imported supported fixtures run without rk-sim/compiler".
- **Reproduce.** `uarch characterize --prepared-input contract/tests/fixtures/u2/independent-bundle.json --output x.json`
  (and `uarch capture … --assumptions <current physical assumptions>`) under the producer trap → **exit 2
  `AssumptionMismatch: resolved-ops/1 algorithms/model`**. The fixture binds `assumptions_hash sha256:ede89012…`
  (proposal-era model `physical-resolved` version `1-proposed`); the current `physical_assumptions()` hash is
  `sha256:255afd1c…` with model implementation hash `sha256(core.py)`.
- **Why tests pass.** `tests/unit/test_u2_a_prepared.py:19-23` and `tests/unit/test_u2_a_shapes.py:17-21`
  rewrite `intent.assumptions_hash` and re-seal every hash before executing. A resealed copy runs via the public CLI
  under the trap and reproduces the hand-authored expectations (matrix 1184, read 1296, write 288 bytes).
- **Consequence.** The import path is demonstrated only on modified bytes. Also, because the intent binds the
  engine's file hash, every saved bundle stops executing after any byte change to `core.py` (residual risk for U3
  fixture reuse). Either commit a currently sealed fixture plus a public-CLI test that executes it unmodified, or have
  humans confirm this binding is intended and document that imports must be re-sealed per engine version.

### F7 — README / Makefile / CLAUDE.md statements not true at U2 (check 11)

- `src/rkuarch/table/README.md:3-7`: "runs points in a process pool … byte-identical at any worker count),
  interpolates exactly as declared, and measures its own errors: leave-one-out …, batch-composition reduction,
  layer reuse, and cold vs steady". At U2 `capture` refuses `workers≠1`, tables carry
  `interpolation: none/none/refuse`, and every measured error is null with `n_samples 0`.
- `src/rkuarch/workload/README.md:9`: "its error is measured by table/" (not at U2); "KV is read in pages of the
  request's block_size_tokens" conflicts with accepted D6 valid-token reads (T17 reads 17 tokens, not 32).
- `Makefile:17-18`: `table`/`report` still `echo "… lands in U-P3/U-P4"; exit 1`.
- `CLAUDE.md:13` table command (see F3; both-human file — propose only).

### F8 — Normative accepted U0003 package is not committed (human-policy, publication)

- `docs/decisions/U0003-one-chip-one-set-of-facts.md:7-10` makes "the immutable reviewed original ADR and 116-entry
  package" normative and links `../reviews/U2-inputs/A-R1-R2-proposal-8def4c6d2c27/…`. In a clean clone all six
  `U2-inputs/*` roots referenced by the accepted records are missing (`git ls-files docs/reviews/U2-inputs` → 1 file;
  `docs/reviews/U2-common-baseline-v1/` → 0 tracked files). Committed: `docs/reviews/U2-U0003-proposal/`
  `proposed.schema.json` (sha256 `e903f46b…`, matches acceptance) and `public-amendments-index.json` (`7bdc058f…`,
  matches), but not `interfaces.md`, `two-track-amendment.md`, `comparison-evidence-export.md`,
  `R1-R2-corrections.md`, `delivery.md` or the proposal ADR. The local archive's SHA256SUMS does verify
  (`8def4c6d…`, `sha256sum -c` exit 0). Not a code defect; after publication, cold-clone reviewers and CI cannot
  read the normative D1–D12/R1/R2 text. Humans decide whether to commit it before publication.

### Cross-lane observations for Lane B (not counted as lane-A findings)

- **X1 (B, report).** Exit text says the default report "shows 'conditional · N stipulations'". Default mode prints
  "Stipulation inventory count: magnitude hidden · STUB — input inventory; not a prediction"; only opt-in shows
  "59.0 stipulations" (count rendered as a float). Possibly an intended conservative policy; B should confirm.
- **X2 (B, report).** Identifier digits are redacted even in opt-in: `/request/model/name: llama[numeric text
  withheld][numeric text withheld]b`, `Mapping policy: analytic-ops@[numeric text withheld]`, rationale
  `B[numeric text withheld] hardware proposal`. Safe, but reduces report usefulness.

## U-REVIEW Stage 1 checks (lane A)

| # | Check | Applicability | What I did | Result |
|---|---|---|---|---|
| 1 | Joint exit from a cold clone | U2, **gate pending** | Local `git clone --no-hardlinks` at exact target; full suite; E5 public-CLI chain; adopted matrix re-run | Local: suite 1019/0/0; E5 chain passes after harness deltas (F2/F3). **CI-form lint/typecheck fail (F1).** U0021 fresh GitHub clone on ElfinKidsLaptop WSL2 + hosted Ubuntu CI on the same published commit: **not executed, pending publication**; U1 CI not reused |
| 2 | Numbers without badge; `±0` | U2 | Rendered default/opt-in from fresh and trapped replay tables; grep | No `±`; default hides all STUB magnitudes; opt-in values carry "STUB — unvalidated … error unknown"; diagnostics "not modelled"; energy "unverified". X1/X2 for B |
| 3 | Golden changes | U2 | `git diff --stat 1e9e794 HEAD -- tests/golden` | None (no `tests/golden/expected` content) |
| 4 | Numerical smells / three formulas | U2 | Code read + greps + independent calculator (below) | MAC=2 ops (`core.py:61`, `derive.py:107,166`); serial matrix+vector; ps only in engine, one ps→s site (`table/time_units.py:9`); no cycle counts outside engines; no set-order output; seed plumbed (`seed=0`, no randomness); diagnostics null; no DRAM preset read (timing/organisation listed unrepresented); no Rust/HashMap changes; tp: table.tp == request tp, rows are one rank. F4 only |
| 5 | Provenance | U2 | `uarch validate` H1; reference-status copy of H1; derivation/projection code; C10 probe | H1: 59 stipulations, 0 claims. Reference copy → exit 2 `clock_domains.core.freq_hz: a reference permits only claims`. Derived peaks stay `stipulation` (`derive.py:71-77`, worst real claim kept in `claim_badge`); projection downgrades every stipulation/measured/ineligible citation to `stub, source null` with recorded loss (`export.py:79-103`). Nominal npu-l4 efficiency 1.0 is a `claim/stub/source null` test input, matching accepted D2 |
| 6 | Evidence / ordering | U2 (no predictions) | Card in my table; `find validation -path '*predictions*'` | Card badge `stub`, `validated_error_band null`, evidence empty; measured errors null with `n_samples 0`. No L3 predictions exist; `validation/L3_silicon/check_ordering.py` does not exist and CI skips it — **not applicable until U5** |
| 7 | Fidelity / C2 rule | U2 | Table fields; code | `composite_fidelity C0`, levels 0/0/0, sync exact; analytic refuses any other fidelity (`core.py:121-129`, `prepared.py:56-63`). No C2 rows. u_c0 ≤ duration held on every point I ran (F4 is about verification of captured results) |
| 8 | Determinism 1 vs N workers | **Workers N unsupported in U2** | `--workers 2`; repeated runs; PYTHONHASHSEED 0/1/98765, OMP threads 4; key-order controls | `UnsupportedWorkers: analytic capture supports workers=1` (`build.py:72-73`) — process pool is U-P7 scope, so the 1-vs-N byte check is **not executable at U2** and is not claimed. All same-input runs byte-identical (`599da91d…`) across seeds and reversed/rotated hardware key order. Thread checks are U9 |
| 9 | Native vs fork | U6+ | — | Not applicable (no fork/native engine in U2) |
| 10 | Scope (§1.3 out list) | U2 | Diff review | No mapping search, interpolation, process pool, fork/native, SIMD/GPU/MPI, ONNX or web UI added; no dependency change (`pyproject.toml`, `uv.lock`, `native/Cargo.toml` unchanged). `uarch-prepared/1` reuses contract `OpSpec` as accepted by U0003 |
| 11 | READMEs true | U2 | Read lane-A READMEs, Makefile, CLAUDE.md | F7 |

## Independently derived formulas (no repository code used for expectations)

Conventions taken from accepted U0003 D6/D12 and U-P3, not from the implementation. All three were checked against
**every op of all 16 CLI rows (272 ops)** with exact rational arithmetic (`independent_formulas.py`): 0 mismatches.

1. **Projection work and traffic.** `matrix_ops = 2·M·K·N·instances`; DRAM bytes once per operand per instance:
   read `(M·K + K·N)·w`, write `M·N·w`. Example, llama-3.1-8b decode B=1, tp1, bf16 `q_projection`
   (×32 layers): matrix `2·1·4096·4096·32 = 1,073,741,824`; read `(4096 + 16,777,216)·2·32 = 1,074,003,968` B.
   `lm_head` uses `N = ⌈V/tp⌉` (physically executed padded width); prefill head uses all tokens unless declared `last`.
2. **Fused attention with paged valid-token KV.** `pairs = B·Hq·S·T` (full square; causal prefill
   `B·Hq·S(S+1)/2`, decode never halved); `matrix = 4·pairs·D`, `vector = 5·pairs`; DRAM moves only
   Q (`B·Hq·S·D`, read), K and V (`B·Hkv·T·D` each, read, valid tokens), O (write). Pages `⌈T/16⌉`, last page
   `1+(T−1) mod 16`. Example decode B=1, T=17, tp1: pairs 544, matrix 278,528/layer, vector 2,720/layer,
   reads `(4096 + 2·17,408)·2 = 77,824` B, write 8,192 B; pages 2, last page 1 token. Verified also for causal,
   tp2/tp16 (KV replicated: Hkv=1, replicas 2) in `probe_shards.py`.
3. **Roofline time and attribution.** `compute_s = matrix/(2·cores·MAC/cycle·f_core) + vector/(cores·ops/cycle·f_core)`,
   `memory_s = bytes/BW` (declared peak, no derating, DRAM not core-scaled on H1), per-op `max`; `per_op` row =
   Σ max, `u_c0` = max(Σcompute, Σmemory); attribution = Σ durations of compute-bound vs memory-bound ops.
   H1 at ratio 0.5: matrix peak `2·4·65536·5e8 = 2.62144e14` ops/s, vector `4·256·5e8 = 5.12e11`, BW `1e12` B/s.
   Row 0 (decode B=1, T=17, ratio 0.5): bytes `15,018,393,600 + 5,384,704` → `u_c0 = 0.015023778304 s`, exactly
   as emitted; `duration_s = 0.015027924352 s ≥ u_c0`; attribution compute `8.496e-06`, memory `0.015019428352`.
4. **Embedding and rank scope** (extra). Gather reads `hits[rank]·D·w`, writes `M·D·w`; tp2 M=1 uses `[1,0]`,
   `[1,1]` refused (`embedding assignment conservation`); rank1 with 0 hits reads 0 W bytes; equivalent ranks are
   exactly the ranks with equal hits at every point (`balanced_tp_selected_rank` when not all).

## Focus-area results (lane A)

- **Shard/rank** (`probe_shards.py`): tp2 explicit hits both ranks, tp2 synthetic balanced, tp16 KV replication
  (`N: global 1024, rank 128, replicas 2`), vocabulary 128257 over tp2 (rank0 logical 64129/physical 64129, rank1
  logical 64128/physical 64129), causal, last-token head: **0 count mismatches** vs independent calculator; tp3 →
  `ShardIndivisible` (`n_heads=32 is not divisible by tp=3`); no-assignment tp2 refused before preparation.
- **Prepared identity/imports** (`probe_imports.py`, 28 cases, all as expected): stale hash → `ContentHashMismatch`;
  consistently rehashed forgeries of op dims, `work_repeat`, decoder repeat, coverage (drop/duplicate point),
  hardware value with old intent hash (`SpecHashMismatch`), precision fp8 on bf16-only H1, `uarch-prepared/2`,
  detailed mapping scope/policy, rank/tp, embedding local tokens, KV pages, KV dtype, declared omissions, decode
  `lm_head_tokens`, unknown field, detailed fidelity, assumption hash, duplicate JSON key, `NaN` → all refused before
  execution. Controls (unchanged, moved, producer version bump, importer-declared causal) accepted and executed.
- **Producer traps.** CLI replay and both report modes ran with `rkuarch.workload.prepare`, `rk`, nominal candidate,
  comparison/refresh tooling and `scripts.u2_inputs` import-blocked (inherited by the engine subprocess); report
  replay additionally function-trapped `run_analytic`, `execute_prepared_point`, `prepare_engine_job`, `capture`.
  No trap fired except the negative control. Bytes identical to fresh outputs.
- **RR-C1** (claimed fixed): **verified on v2** with the public CLI and real engine execution — fresh YAML ×2,
  canonical saved bundle (trapped), reversed and rotated JSON hardware all give table `sha256:01d3d017…5ca2`, file
  `599da91d…`, identical 44-file packages. **Discriminating control:** in a scratch copy with `8b35302`'s one-line
  sort reverted, the same harness yields three different tables (`3cb3c658…`, `94bb2d59…`, `04fefc29…`).
- **Nominal isolation and adopted compatibility** (`run_adopted.py`, `probe_nominal_isolation.py`): adopted manifest
  `f8220c94…cc96e` re-hashed; 1008 nominal calls, 96 physical points, 6 H1 preparations; nominal
  `compatibility_pass`, evidence `refused` (four direct precision-refusal observations per track). Independent recheck
  from raw rows: duration and positive counts **exact (worst rel 0.0)**, **0 adjusted channels**, decode writes 504
  `modelled_absence`, vector 1008 `modelled_absence`, no null/absent channel numerically passed. All 1008 candidate
  outputs re-derived bit-identically under an audit hook blocking open/socket/subprocess/exec/import (none attempted).
  Physical track: 96 executed (discrepancies retained: matrix −6.5…+2.9 %, reads −6.5 %…+10,908 %, duration
  −6.5…+163 %), 48 `execution_failed` (WeightCapacityExceeded), 864 `not_run` (no approved physical HardwareSpec for
  retained components), gate `not_assessed`. These are honest discrepancy records, not failures of the superseded
  physical-to-nominal rule.
- **A-F12.** Nominal: `tests/u2_comparison.py:121-126` returns `pre_call_refusal` before building a candidate input;
  candidate itself refuses replicated/indivisible heads. Physical: `contract/tests/u2_prepared_adapter.py:37-48`
  refuses replicated KV / padded vocabulary before `execute_prepared_point`. Covered by
  `tests/unit/test_u2_b_comparison_orchestration.py::test_af12_refuses_before_candidate`,
  `::test_real_physical_af12_refuses_before_engine`, `tests/unit/test_u2_a_prepared.py::test_adapter_exact_selection_and_a_f12_before_core`,
  `contract/tests/test_projection_scope.py`. The adopted 1008 inventory itself contains no A-F12 case.
- **Hardware derivation/export/projection.** H1 bf16 peak `2·4·65536·1e9/1e12 = 524.288` TFLOPS, `hbm_bw 1.0` TB/s,
  `hbm_capacity 32.0` GB, `tdp 300` W — all `stipulation`; emitted oracle-compat bytes equal the adopted vendored
  `components/npu-l4.yaml` and `u2-inputs/components/npu-l4.yaml` (cmp). Pinned-loader round trip could not be
  re-executed locally (`VendorLoader` refuses `rk.schema` outside its declared closure); it rests on the received
  human generation.
- **Capability refusals.** Covered by `tests/unit/test_u2_a_derivation.py::test_capability_refusals[dram|zero|width|block|peak|kv]`
  and `::test_round_once_ties_to_even_and_extra_compute_map_refused` (both pass in E1).

## Case reconciliation (lane-A scope)

Read together: `tests/fixtures/u2_b/acceptance-cases.json` (index, "test_index_not_runtime_ledger"),
`docs/reviews/U2-B-real-report-exits-v1/case-reconciliation.json` (B64 overlays) and
`docs/reviews/U2-adoption-v2-execution/case-evidence-update.json` (retains **56 executed / 8 pending**:
B05, S10, R202, C04, C06, C07, C09, C10). The B64 namespace (B/S/D/R1/R2/C ids) is distinct from the original-26
preparation list and from the proof77 / revision42 / P-R3 nine namespaces; nothing below re-numbers or promotes
those. **I do not change the ledger**; these are recommendations for the coordinator.

| Case | Setup (abridged) | Evidence now (I = executed in this review, T = identified committed test, R = received) | Recommendation |
|---|---|---|---|
| **C04** | A-F12 for replicated/padded/uneven counts; no fabricated rank counts | T: `test_af12_refuses_before_candidate`, `test_real_physical_af12_refuses_before_engine`, `test_adapter_exact_selection_and_a_f12_before_core`, `contract/tests/test_projection_scope.py` (11 test functions), `test_selected_rank_embedding_is_explicit_and_conserved`, `test_d7_selected_unequal_hits_are_preserved_and_conserved`. I: E1 passes them; shard probes show physical work uses actual rank counts (no ÷tp of actuals). | **Covered by identified existing tests** for the accepted D7 meaning (uneven embedding hits are allowed only explicit/conserved). Not exercised by the 1008 adopted inventory (no A-F12 row) — state that limit. |
| **C06** | Split/unknown efficiency, zero clock, scalable DRAM, block-scale | T: `test_capability_refusals[dram,zero,width,block,peak,kv]`, `test_round_once_ties_to_even_and_extra_compute_map_refused`, `contract/tests/test_u2_nominal_candidate.py::test_split_memory_and_retained_point55`; `ExecutionModelInput` validator refuses non-(0,1] or split/scalar mismatch (`contract/uarch_contract/exports.py:52-59`). Physical engine consumes no efficiency at all. | **Covered by identified tests**, except "unknown efficiency": unrepresentable by schema (value required, (0,1]) — record as accepted unsupported rather than missing. |
| **C07** | Full-square/all-token head, vector algebra, operand traffic, valid-token paged KV, partial residency unknown | I: E6 (272 ops exact), `probe_shards.py` (causal/last-token/paged/replication/padding), property probe; T: `test_u2_a_shapes.py` (literal decoder, prefill attention/head literals, vocab padding/KV replication, capacity), `test_u2_a_analytic.py` (literal counts/timing, half-byte, fractional ps). Residency: `peak_resident_bytes` null everywhere and loader refuses non-null (`table/artifacts.py:441-444`); no .55 in physical path. | **Executed now for H1 scope** + identified tests. Retained-component physical runs are **accepted unsupported** (no approved physical HardwareSpecs; 864 `not_run` honestly recorded). |
| **C09** | Invalid/unsupported formats, duplicate or missing compute/KV pairs | T: `contract/tests/test_u2_precision_matrix.py::test_B2_explicit_bindings_reject_missing_duplicate_and_inferred_inputs`, `::test_proposed_selection_is_1008_unique_queries_with_four_separate_refusals`; A side `validate_storage` (`derive.py:23-29`) and `test_capability_refusals[width,peak,kv]`. I: adopted run consumed exactly 7 pairs/1008 + 4 direct refusals per track. | Mostly **B-owned boundary**; A half covered. The full original descriptor negative composite is not re-run — B/coordinator to decide; not a missing A behaviour. |
| **C10** | Truth with stipulations; mismatched spec/projection/bytes/execution binding; pinned-loader round trip | I: `probe_c10.py` 10/10 mismatches refused + control accepted; emitted bytes == adopted component bytes. T: `test_export_truth_projection_bytes_bindings_and_efficiency`, `test_rehashed_wrong_derivation_and_wrong_execution_are_refused`, B `test_AB2_C1_*`. R: human pinned-loader generation (v1/v2). | **Executed now (behaviour)**, but **genuinely missing durable regression** for the loader branch → F5. Pinned-loader round trip: received evidence only (cannot be re-run without rk-sim). |
| **C11** (engine half) | Nominal candidate under expected-access trap; physical adapter with prepare disabled | I: 1008 candidate re-derivations under a full I/O-blocking audit hook; trapped CLI replay and trapped report replay. T: `test_execution_has_no_file_network_or_prohibited_import_access`, `test_candidate_cannot_read_expected_files`, `test_physical_adapter_uses_saved_bundle_with_prepare_disabled`. | Ledger already **executed**; my runs independently confirm the engine half. |
| **B-F16** (engine half) | Precision/export/adapter, prepared-bundle parity | I: export/derivation literals, emitted-bytes identity, adopted 1008/4 matrix, prepared replay identity (E5). | Engine-half technical evidence **sufficient**; physical accuracy not established (as accepted). F6 must be resolved for the "imported supported fixture" leg. |
| **R202** | Recipe omission/rehash negative at complete-package scale | Lane B (report/recipe closure). A side: `IncompleteMetricContributors` paths in `table/artifacts.py:270-333` tested by `test_u2_a_artifacts.py`/`test_u2_a_loader.py`. | Leave to B review; A-side required-contributor check exists and is tested. |
| B05, S10 | Real L4/history; nonempty energy | Outside lane A. A-side: `consumed_energy_families` is known-empty and requires `energy` in `unrepresented` (`build.py:217-221`); no energy quantity emitted. | Accepted unsupported scope (B to confirm). |

## What was executed here vs inherited vs not executed

- **Executed by me on the exact target:** E1–E6; `probe_shards.py`; `probe_imports.py`; `probe_u_c0.py`;
  `probe_property.py`; `probe_c10.py`; `run_adopted.py` (fresh 1008/96/6 adopted execution, independent gate recheck);
  `probe_nominal_isolation.py`; `probe_report_trapped.py`; RR-C1 discriminating revert in a separate scratch clone;
  PYTHONHASHSEED/OMP determinism; `uarch validate` on a reference-status spec; independent bundle via CLI
  (as committed: refused; resealed: runs).
- **Harness deltas (declared):** companions from committed synthetic test scaffolding plus one synthetic registry
  entry for H1; spec written as a content-addressed companion (F2); report output parent dirs pre-created (B's
  writer requires existing parents); `run_adopted.py` uses only `refresh.consume_adopted` (no preflight git asserts,
  no writes into `docs/reviews/U2-adoption-v2-execution/` — the original driver rewrites `output-location.json` and
  `runtime-progress.json` there, so it was **not** run in place).
- **Inherited, inspected, not re-executed:** the 25-phase v2 runtime (3,310-file package, 40,320 comparisons,
  serialized-surface checks, capability refusals) — I re-executed its producer phase, the RR-C1 identity and report
  repeat at my own (16-row) scale, not the 24-row/40,320-comparison package; human pinned-loader generation;
  wheel/ZIP resource validation (pending per AD-C2 record). The optional large outputs in
  `/tmp/u2-adoption-v2-runtime-rxh7iex5/outputs` were **not used** and not authenticated.
- **Not executed / not executable at U2:** 1-vs-N worker determinism (unsupported until U-P7); thread determinism (U9);
  native-vs-fork (U6); check_ordering (no predictions until U5).

## Pending publication gates (not closed by this review)

1. Fix or human-disposition of **F1** (CI lint/typecheck) before any publication attempt.
2. U0021: fresh GitHub clone on ElfinKidsLaptop WSL2 **and** hosted Ubuntu CI on the **exact same published
   commit**, distinguishing executed checks from no-op jobs (golden/determinism/ordering/perf jobs are currently
   "nothing yet" no-ops). Local clean-clone results here are not that gate; U1 CI is not reused.
3. Stage 2 author responses and Stage 3 adjudication; human tag/closure. U3 performance-host requirements remain.

## Residual risks (no finding raised)

- Counts are binary64 (`contract/uarch_contract/table.py:62-66`, `NonNegativeFloat`). Values above 2^53 lose
  integer exactness: e.g. a llama-70b prefill n=16, L=4096 row at tp1 has total matrix ops ≈ 2·70.6e9·65,536 ≈
  9.25e15 > 2^53 ≈ 9.007e15 (its largest single op, `ffn_up` ×80 layers, is 2.46e15 and still exact). Both 32 GB
  designs (H1, H2) refuse that model at tp1 for capacity, so no U2 row I produced reaches it; U3 G2(c) "exact integer
  expectations" should check exactness explicitly.
- Saved prepared bundles bind the engine file hash through `assumptions_hash` (F6); any `core.py` byte change makes
  every saved bundle and fixture non-executable — a reuse hazard for the U3 fork adapter and Rust protocol fixtures.
- `validate_engine_result` tolerances (`rel_tol 1e-9`, `abs_tol 1e-3 ps`) are looser than the exact arithmetic the
  engine performs; acceptable for U-C0, worth tightening when other engines use the boundary.
- Capacity refusal happens at preparation/import (`validate_execution_bundle` → `capacity_summary`), so a
  capacity-exceeding request yields no table at all rather than an explicit refused row (22/60 random requests in
  `probe_property.py`). Honest, but the table carries no record of the refusal.
- The report renderer output for 16 small rows is ~10.8 MB per file; the adopted 24-row package was ~621 MB of
  replay stream. Scale is a U4 risk, not a U2 defect.

## Required author response (Stage 2)

Answer every finding F1–F8 as APPLIED (with a regression test that fails without it), REJECTED (with a reason a
stranger can evaluate) or DEFERRED (with where it is recorded). F1 is BLOCKING for the publication gate. F3 and F8
need a human-policy decision recorded by the coordinator; F6 may need one (is binding the engine file hash into
imported intents intended?). X1/X2 go to Lane B. Cross-lane owners: F1 (coordinator/B/both-human `contract/`),
F7 CLAUDE.md (both humans), F8 (coordinator/humans).

Status: **STAGE 1 COMPLETE** — 1 BLOCKING, 7 NON-BLOCKING. No fix, adjudication, ledger change or closure made.

## Evidence files

Scripts: `U2-final-review-A/{e2e_cli,scaffold,independent_formulas,probe_shards,probe_imports,probe_u_c0,probe_property,probe_c10,run_adopted,probe_nominal_isolation,probe_report_trapped}.py`,
`U2-final-review-A/trap/sitecustomize.py` (active only when `REVIEW_TRAP_MODULES` is set).
Receipts: `U2-final-review-A/results/*.json` (E5 results for the target and for the RR-C1-reverted scratch copy,
independent-formula comparison, every probe's output, adopted re-run summary), `full-suite-summary.txt`,
`mypy-ci-form.log`, `ruff-ci-form-by-file.txt`. Large generated tables/reports stayed in the session scratchpad.

---

# Stage 3 adjudication — 2026-10-09 (same independent lane-A reviewer)

Stage 1 text above is unchanged (its SHA256 before this append, `b54fc9be…a96228`, equals the hash the author
recorded at entry in `U2-A-stage2/baseline.json`). Stage 3 checks only (a) a row per finding, (b) REJECTED reasons,
(c) APPLIED changes have a test that fails without them, plus one random revert. No new findings are raised.

## Identities verified

- Reviewed commit `769a1fef…`; author HEAD is still that commit with uncommitted changes. Coordinator review tree
  `5c2b7f1d4a8a5bee47a702b1740fcb5fac484051`: `git diff 769a1fe 5c2b7f1d` touches exactly the 10 paths in
  `A-stage2-reconciliation.json` (`cli.py` +4, `engines/protocol.py` +2, two READMEs, three new test modules, the
  `tests/fixtures/u2_a/current-import/` fixture). All 10 blobs match the live author files byte for byte (no drift).
- Author response SHA256 `2bdb8756…5128` and `changes.patch` `e05a53e5…a137` match the receipt.
- **Exact tested tree:** `git archive 5c2b7f1d | tar -x` into a private scratch dir; its `HEAD^{tree}` is
  `5c2b7f1d4a8a5bee47a702b1740fcb5fac484051`. Receipts: `docs/reviews/U2-final-review-A-stage3/`.

## Runs executed by me (distinct from the author's 38 / 277 / 9-baseline receipts and the old 1019 suite)

| Run (tree) | Result |
|---|---|
| Three new modules on `5c2b7f1d` | **38 passed** (40.4 s) |
| Same 38 tests, `cli.py` + `protocol.py` reverted to reviewed bytes (baseline production + new tests/fixture) | **9 failed / 29 passed** — reproduces the author's baseline claim (2 F2 + 7 F4) |
| **Random revert — F2** (selection `secrets.SystemRandom().choice(['F2','F4'])` → F2, logged): only the 4 `cli.py` lines reverted, `cli.py` sha256 back to reviewed `24cd82b8…`; `pytest tests/integration/test_u2_a_stage2_cli.py` | **2 failed / 4 passed** — both `test_table_indexes_own_hardware_in_fresh_companions[intent,prepared]` fail with `ArtifactMissing: sha256:cb2687…` (the Stage 1 symptom); with the fix all 6 pass |
| Supplementary revert — F4 (2 `protocol.py` lines) | **7 failed / 1 passed** — all six rehashed-U-C0 cases and the subprocess forgery fail; the property test passes either way (engine arithmetic was already right) |
| My Stage 1 `probe_u_c0.py` on `5c2b7f1d` | U-C0 = 2×duration and U-C0 = 0 now **refused** `EngineResultMismatch: u_c0_duration_ps`; halved-duration control still refused |
| F5 branch-disabling mutation (`table/artifacts.py` export-binding branch → `if False and …`) | **22 failed / 2 passed** — every new negative fails, the two controls pass, so the tests reach and pin the branch |
| F6: public CLI on the exact committed-to-be fixture under my wider import trap | `characterize` and `capture` exit 0; fixture and assumptions hashes identical before/after (`c1291483…`, `a57d6ae2…`); decode 1184/572/1296/288 (1,892,000 ps; U-C0 1,584,000 ps), prefill 672/252/1040/288; historical fixture still `AssumptionMismatch`; negative trap control blocked |
| F1 exact CI forms on `5c2b7f1d` | `ruff check .` **exit 1, 141 errors**; `mypy src contract scripts` **exit 2** (same collision) — unchanged from Stage 1 |
| **Full suite on `5c2b7f1d`** | **1053 passed, 4 failed** (1057 = 1019 + 38), 197.6 s — see below |

The four full-suite failures on the review tree, named by a targeted re-run:

1. `contract/tests/test_committed_snapshot.py::test_current_snapshot_generator_compatibility` — strict support
   refusal `input support changed: src/rkuarch/cli.py` (**disclosed**, intended gate).
2. `contract/tests/test_u2_historical_snapshot.py::test_current_canonical_is_exact_adopted_1008_four_real_refusals`
   — same strict-support refusal (same root cause; **not separately listed** by the author, whose snapshot run
   covered only `test_committed_snapshot.py`).
3. `tests/unit/test_u2_b_report_adapter.py::test_proposed_A4_report_invocation` and
4. `::test_proposed_report_help_and_original_validate_registration` — B's A4 report-adapter test pins
   `src/rkuarch/cli.py` to `{before, proposed_after}` hashes (`24cd82b8…` is the reviewed file); the F2 edit
   (`f14f10c2…`) necessarily trips it. **Not disclosed** in the response (its 277-test selection excluded this
   file); the response's "no unexplained final regression in the executed selections" is true only for those
   selections. This is an identity pin of the same class as the support gate, B-owned, so A could not re-pin it;
   it is recorded here as a reconciliation requirement, not a new finding.

## Per-finding adjudication

| Finding | Response | (a) row | (b)/(c) check | Stage 3 disposition |
|---|---|---|---|---|
| F1 (BLOCKING) | DEFERRED | yes | Deferral is concrete: unapplied shared CI/config proposal, enumerated 21 historical lint files, and the 160 contract-test typing errors in nine files it exposes; owners coordinator + B + both-human `contract/`; states F1 remains BLOCKING. My rerun confirms both CI forms still red. | **Deferral accepted as a response; F1 is NOT resolved and remains an open BLOCKING finding.** Configured mypy and scoped lint do not substitute. Publication stays blocked until the exact CI forms pass and that fix is adjudicated. |
| F2 | APPLIED | yes | Discriminating test confirmed by the **random revert** (2 fail without / pass with); wrong-spec refusal retained. | **Accepted.** Condition: the two B adapter-pin failures it causes must enter the coordinator's reconciliation with the support freeze (B re-pin or adapter update); they must not be bypassed or left undisclosed. |
| F3 | DEFERRED | yes | Concrete public-chain proposal (assumptions → prepare → capture → draft companions → real external review → assembly), owners coordinator + B, Javid decision for any unreviewed alternative; explicitly not a documentation waiver. | **Deferral accepted; F3 remains open.** The documented `uarch table …` exit command still refuses; U-P3 acceptance 5 / joint public CLI exit is not met by this response. |
| F4 | APPLIED | yes | Discriminating tests confirmed (supplementary revert 7 fail / pass with); property test added (25 derandomized examples, tiny independently specified hardware). | **Accepted.** Tolerances unchanged as stated. |
| F5 | APPLIED (tests only) | yes | Per the launch scope, no implementation revert demanded; branch-disabling mutation makes 22/22 new negatives fail, so coverage is genuine. Uses both public disk and memory loaders. | **Accepted.** Reviewer correction: my Stage 1 text said "10/10" C10 mismatches; my `probe_c10.py` actually had **1 control + 9 mutations** (the author is right). The new tests add truth and content-hash cases (11 negatives per boundary). |
| F6 | APPLIED (additive fixture) | yes | New fixture differs from the historical one only in `intent.assumptions_hash`, `intent_hash`, `bundle_hash` (my structural diff); expectations are the pre-existing independent literals in `contract/tests/fixtures/u2/expected.json` (decode and `prefill_L1`); executes unchanged via the public CLI with preparation trapped and no runtime resealing; historical fixture unchanged and still refused. Passing on baseline production is expected for an additive fixture. | **Accepted.** The strict engine-implementation binding (any `core.py` change requires a reviewed fixture rebind) remains a documented residual risk, not changed policy. |
| F7 | DEFERRED (A-owned prose corrected) | yes | Table/workload README text now matches behaviour I executed (workers=1 refusal, `none/none/refuse`, null zero-sample errors, T17 valid-token reads); Makefile/CLAUDE.md left to coordinator/humans pending F3. | **Partial: A-owned README part accepted; Makefile `table`/`report` targets and `CLAUDE.md:13` remain open** (deferred, owners named). |
| F8 | DEFERRED | yes | Six normative texts identified with verified hashes against manifest `8def4c6d…`; next step (exact Git addition or reviewed link repair) assigned to coordinator/humans. | **Deferral accepted; F8 remains open** — a clean clone still cannot follow the normative links. |

No row is REJECTED, so check (b) is vacuous. Every finding has a row (a). Every APPLIED row has a test that fails
without its change or, for the coverage-only/additive rows, demonstrably reaches the intended behaviour (c).

## Verdict

**ACCEPTED** — scoped to the Stage 3 response checks (a)–(c) on review tree `5c2b7f1d4a8a5bee47a702b1740fcb5fac484051`.

What this acceptance is **not**:

- It does **not** resolve F1. F1 remains an open **BLOCKING** finding; the exact CI forms are still red on the
  review tree. U2 publication, the U0021 fresh GitHub clone + same-published-commit hosted Ubuntu CI gate, tagging
  and closure remain blocked on F1 regardless of this verdict, and its eventual fix needs its own adjudication.
- F3, F8 and the shared part of F7 (Makefile, CLAUDE.md) remain open dependencies with named owners.
- The review tree's full suite is **not green**: 4 failures (2 strict-support gate, 2 B adapter `cli.py` pin).
  Integrating these source fixes requires the coordinated support freeze / human artifact lifecycle **and** a B-owned
  adapter re-pin; neither gate may be bypassed. The old 1019-test suite and v2 full-report receipts bind the old
  source and do not cover this tree.
- No artifact-dependent acceptance, hosted CI, cold published clone or sprint closure is claimed. No B finding is
  adjudicated here.

---

# Stage 3 follow-up: public companions — 2026-10-10 (same independent lane-A reviewer)

The 49,385-byte prefix of this file (SHA256 `955f277a…d397`, Stage 1 + first Stage 3) is unchanged; this section is
appended. Scope: the standing Stage 3 checks (a)–(c) over the original A-F1…F8 rows, using the earlier response plus
the public-companion addenda. No new findings, no fixes, no ledger change. Receipts:
`docs/reviews/U2-final-review-A-companions/`.

## Identities verified

- **Exact reviewed tree `57e975842bf70583680c68e19e80af77bb42d8d0`** (a tree, not a commit); installed baseline tree
  `b5e530e17d3b7511216a229c56263ca9be3b902c`; original commit `769a1fef…`. `git diff b5e530e1 57e97584` = exactly the
  9 implementation paths in `U2-public-companions-final-reconciliation.json` (A: `src/rkuarch/cli.py`,
  `src/rkuarch/table/companions.{py,md}`, `tests/unit/test_u2_a_companions.py`,
  `tests/integration/test_u2_a_companions_cli.py`, `tests/u2_a_companion_inputs.py`; B: three peer paths, not
  attributed to A). Private `git archive` export; its `HEAD^{tree}` equals `57e97584…`.
- Handoff hashes match the reconciliation: A initial `b4a29063…`, B `84e8f96a…`, A follow-up `f978fc87…`.
  Approval `U2-final-corrections-v1` (exact three patches + draft/review/assembly implementation; explicitly not a
  general protected-path waiver and not an evidence review) and the install receipts were read; not re-litigated.
- B's `assemble_stub_context(captured, *, dependencies, registry, model_card, comparison_hashes, artifacts)` matches
  A's call keyword for keyword (`provenance/companions.py:136-144` vs `cli.py` assemble).

## Runs executed by me on `57e97584` (distinct from author/coordinator receipts)

| Run | Result |
|---|---|
| Coordinator's 124-test selection (`test_u2_a_companions`, `test_u2_a_companions_cli`, `test_u2_b_companions`, `test_u2_a_stage2_cli`, `test_u2_a_cli`, `test_u2_b_report_adapter`, `test_u2_b_complete_report`) | **124 passed, 0 failed, 0 errors, 0 skipped**, 228 s — no pending-peer skip |
| Independent public chain (`companions_e2e.py`): H1 `npu-l4` × llama-3.1-8b bf16, my Stage 1 16-point grid, every product step a CLI subprocess: `assumptions` → `prepare` → `capture` (engine executes) → `companions draft` (trapped) → **SYNTHETIC** declaration review via the committed test helper → `companions assemble --no-comparisons` → `table --capture-dir` → `report` default / opt-in, all trapped | All steps as expected. Two fresh runs: all 140 common files byte-identical (fresh-a additionally holds only my three negative-control inputs). Relocated saved inputs regenerated under the trap: all 140 files identical to fresh-b. Trap negative control (capture under trap) refuses. Rows equal my Stage 1 CLI rows exactly (same 16 ordered result hashes, every row field); table `C0`, `comparison_state not_attempted`, card `stub`, band/energy null |
| Intake/review negatives (public CLI, no output written) | no intake flag and both flags → `ComparisonIntake`; resealed `decision: rejected` and resealed `independent: false` recipe reviews → `UnacceptedReview` (B helper); declaration edited after review and resealed → `ReviewSubjectMismatch` |
| Capture-dir boundary (public CLI, copies) | exact copy → table byte-identical; missing result → `CaptureCoverageMismatch`; valid self-identified extra member (context JSON) → `CaptureMembershipMismatch`; malformed hash-named member → `CaptureArtifactInvalid`; non-hash file → `CaptureArtifactName`; `--capture-dir` with `--model` route and with `--workers 2` → `CaptureReplay` before preparation |
| **PC-C1** | Default HTML and Markdown twins are distinct files; default hides magnitudes (4,049 "magnitude hidden", 0 shown durations), opt-in shows them with STUB labels; re-rendering opt-in onto the default twins refuses `OutputConflict` and both default files are unchanged |
| **PC-C2** (via selection) | `test_real_cli_rejects_wrong_indexes_or_missing_attempts[wrong-index]` → `bound comparison identity`; `[omit]` → `ComparisonIntakeMismatch`; canonical index order is explicitly re-reviewed (SYNTHETIC) before use — passes on this tree |
| Raw-source retention at public `uarch table --capture-dir` (`raw_retention.py`, committed test construction: B's bounded adopted selection + actual analytic H1/llama-3.1-70b/TP1 `WeightCapacityExceeded: 141107412992 > 32000000000.0`, SYNTHETIC reviews) | assemble + table exit 0; **all 62 input artifacts (9 raw blobs) present byte-for-byte** in the saved package; original full-rows blob retained as raw bytes; capacity comparison and refusal record equal; 3 comparisons each with 4 precision-refusal observations; band/energy null; error samples 0. Deleting the rows blob → `IncompleteMetricContributors: adopted reference original full rows blob required…`; deleting the refusal record → `ArtifactMissing`; **no table written** in either case |

The capacity refusal is an actual analytic preparation refusal; every review record in these runs is synthetic test
scaffolding and is shown as "Reviewer: SYNTHETIC B assembly test" in the rendered reports. None of this is the pending
real external declaration-review demonstration.

## Random revert/restore (required) and supplementary revert

- **Candidate set** (newly applied A behavioural changes, exact hunks): R1 `cli.py:251`
  `files.loaded.update(read_artifact_directory(args.artifact_dir, raw_blobs=True))`; R2 `cli.py:207-209`
  CaptureReplay guard; R3 `table/companions.py:139-143` exact capture membership; R4 `cli.py:466-467`
  `if bool(comparison) == no_comparisons: raise ValueError("ComparisonIntake: …")`; R5 `cli.py:489-491`
  ReviewBindingMismatch. `secrets.SystemRandom().choice` → **R4** (logged with timestamp).
- **Revert** (only those two lines, private copy; `R4-revert.diff`):
  `pytest tests/integration/test_u2_a_companions_cli.py::test_assembly_requires_explicit_comparison_intake` →
  **1 failed**: `assert result.exit_code == 2` got **0** — assembly silently proceeded with implicit empty intake and
  wrote a context. Behavioural failure, not import/setup.
- **Restore** (`git checkout` in the same copy; `cli.py` sha256 `39f4745c…9a18` = target blob = reconciliation hash):
  same node **1 passed**.
- **Supplementary, not the random check — R1 raw-closure hook** (comment + 1 line removed): my `raw_retention.py`
  then shows assembly still succeeds but public `uarch table --capture-dir` **refuses**
  `IncompleteMetricContributors: adopted reference original full rows blob required for selected inventory` although
  the blob is present in `--artifact-dir`; `test_real_cli_capacity_failure_prior_comparisons_and_refusals_survive`
  fails at that table step (line 809). With the hook it passes and the 62-artifact retention above holds. This
  confirms the author's before/after regression is discriminating; it is not represented as fixed by tests alone —
  I reproduced the behaviour at the public boundary.

## A-F1 evidence from the installed CI correction (existing finding, not a new one)

Installed `.github/workflows/ci.yml` typecheck now runs `mypy src contract/uarch_contract scripts` and
`mypy --no-explicit-package-bases contract/tests`; it sets **no** `PYTHONPATH`. On `57e97584`: `ruff check .` passes;
production mypy passes (68 files) without `PYTHONPATH`; `lint-imports` 2 kept. But the contract-tests command:

| Environment | Result |
|---|---|
| `PYTHONPATH=.:contract:src` (coordinator receipt environment) | Success, 28 files |
| `PYTHONPATH` = repo root only | Success |
| no `PYTHONPATH` | **206 errors in 4 files**, exit 1 |
| `PYTHONPATH` = target `src`:`contract` only (what a `uv sync` editable install exposes) | **206 errors in 4 files**, exit 1 |
| installed baseline `b5e530e1`, no `PYTHONPATH` | **206 errors in 4 files**, exit 1 |

Errors are in repo-root modules imported from `contract/tests`: `tests/unit/test_u2_a_shapes.py` (A-owned),
`tests/u2_comparison.py`, `tests/u2_refresh.py`, `tests/fixtures/u2_b/b2_support.py`
(`mypy-contract-tests-target.log`). With the repo root on the interpreter path, mypy treats those imports as
installed-package modules and suppresses their errors, so the coordinator's local "pass" depends on an environment
the CI job does not provide. Uncertainty: I cannot run hosted CI; the conclusion rests on `uv run` not adding the repo
root to the path, consistent with the installed editable layout (`packages = ["src/rkuarch",
"contract/uarch_contract"]`). The strict vendor/support gate still refuses (`input support inventory changed`), as
expected and unbypassed.

## Per-original-finding adjudication (response set = Stage 2 response + public-companion addenda)

| Finding | Response now | Stage 3 disposition |
|---|---|---|
| **A-F1** (BLOCKING) | Proposed CI correction installed under approval; "locally checked"; hosted CI open | **Row at fault.** The installed correction is not shown to make the exact CI typecheck step pass under CI conditions: its second command passes only with the repo root on `PYTHONPATH`, which `ci.yml` does not set, and fails with 206 errors otherwise (table above). F1 remains an **open BLOCKING** finding; the local receipt must not be used as evidence that CI will be green. |
| A-F2 | APPLIED, accepted 2026-10-09 | Not reopened. The raw-closure hook intersects its path; `test_u2_a_stage2_cli.py` passes in the 124 selection and my fresh-companion chain builds tables. Note: `--artifact-dir` must now contain only hash-named members (stricter reader), consistent with the documented package rule. |
| **A-F3** | Earlier DEFERRED; now APPLIED (software portion): `assumptions`, `companions draft`, `companions assemble` via B's exact helper, `table --capture-dir` | **Software portion accepted**: discriminating tests verified by the random R4 revert and the supplementary R1 revert; behaviour reproduced at the public CLI (fresh ×2, relocation, producer trap, unreviewed/rejected/not-independent/stale refusals, capture membership, PC-C1, PC-C2, lossless raw retention with refusal-before-output). **Remaining open:** the real public demonstration with actual independent recipe/registry declaration reviews; the abbreviated `uarch table <spec> --model … --engine analytic` still (by design) cannot supply reviewed companions, so U-P3 acceptance 5 / the joint public exit are not met by synthetic-review runs. |
| A-F4, A-F5, A-F6 | APPLIED, accepted 2026-10-09 | Not reopened; their tests pass within the 124 selection where included. |
| A-F7 | Partial: A READMEs fixed earlier; new A-owned `table/companions.md` guide | A-owned part accepted. **Open:** `Makefile` `table`/`report` targets, `CLAUDE.md:13` and `docs/how-it-works.md` command text are unchanged in `57e97584` (coordinator/humans). |
| A-F8 | DEFERRED | **Open:** none of the normative U0003 prose files are in `57e97584`; clean-clone links still dangle (coordinator/humans). |

(a) every original row has a disposition; (b) no row is REJECTED; (c) A-F3's newly applied behaviour has
discriminating tests (verified), but A-F1's installed correction fails its own check under CI conditions.

## Verdict

**NOT ACCEPTED — row at fault: A-F1** (as above). The **A-F3 software portion is accepted** on its merits for tree
`57e975842bf70583680c68e19e80af77bb42d8d0`.

Precise remaining scope, none of which this adjudication closes: A-F1 CI typecheck under CI's environment, then hosted
Ubuntu CI on the exact published commit and the U0021 fresh GitHub clone on ElfinKidsLaptop WSL2; the real external
declaration-review demonstration (A-F3); `Makefile`/`CLAUDE.md`/how-it-works command docs (A-F7 shared); normative
text publication / link repair (A-F8); both strict-support gates pending the combined source/input freeze and human
artifact lifecycle (no support hash rebound here). Nothing here is a full suite, full 1,008-case matrix, artifact
adoption, hosted CI or closure claim; the old 1,287-pass/2-fail suite binds `b5e530e1`, not this tree.

Cross-lane observation for B's own loop (not adjudicated here): with only synthetic *declaration* reviews in the
closure, opt-in output is byte-identical apart from the RenderSpec hash with or without
`--allow-synthetic-presentation`; the reviewer identity is visibly labelled SYNTHETIC in both. Whether that permission
should gate this case is B's display policy.

---

# Stage 3 recheck: CI typing, vendor entry and isolation — 2026-10-10 (same independent lane-A reviewer)

The 61,786-byte prefix of this file (SHA256 `77f2cf20…a74c`) is unchanged; this section is appended. Scope: standing
Stage 3 checks (a)–(c) on the original A rows for the nine-path correction set; no new findings, no fixes, no ledger
change. Receipts: `docs/reviews/U2-final-review-A-ci-isolation-recheck/`.

## Identities

- **Exact reviewed tree `53f9f21b7cc3f84c0cbdb5f3f1e74e6e4aeca522`** (tree, not a commit; HEAD `769a1fef…`).
  `git diff 57e97584 53f9f21b` = exactly nine paths (A: `src/rkuarch/cli.py`, `tests/unit/test_u2_a_shapes.py`,
  `tests/integration/test_u2_a_companions_cli.py`; B: `tests/u2_comparison.py`, `tests/u2_refresh.py`,
  `tests/fixtures/u2_b/b2_support.py`, `tests/unit/test_u2_b_companions.py`, `scripts/vendor_rk.py`,
  `tests/unit/test_vendor_script_entry.py`); `git diff 0fb1900a 53f9f21b` = only the two vendor-entry paths.
  Private `git archive` export; its `HEAD^{tree}` equals `53f9f21b…`.
- Handoff hashes match the receipt: A `1731d974…`, B companions `a798eddd…`, B vendor `54b7a32f…`, VE-C1 `9b27b059…`.
  Isolation guard test `contract/tests/test_u_p2_review.py` = `856aa220…` (unchanged since `b5e530e1`); guard helper
  `contract/tests/vendor_support.py` = `f56e666e…` (unchanged since `769a1fe`). No `pyproject.toml`, CI or config path
  is in the delta.

## Commands I ran (exact tree; distinct from the coordinator's 1,383/2 suite on `0fb1900a` and its 95/2 receipt)

Static, cwd = export root, **`PYTHONPATH` and `MYPYPATH` unset**, fresh `MYPY_CACHE_DIR` per command:

| Command | Result |
|---|---|
| `ruff check --no-cache .` | All checks passed |
| `mypy src contract/uarch_contract scripts` | Success, 68 source files |
| `mypy --no-explicit-package-bases contract/tests` | **Success, 28 source files** |
| Same contract-tests command on `57e97584`, same environment (before control) | **206 errors in 4 files** |
| `lint-imports --no-cache` (`PYTHONPATH` = export `src:contract`) | 2 kept, 0 broken |
| `python -m uarch_contract.generate --check` | schemas fresh |

Delta audit: 0 added `type: ignore`; 20 `cast(` and 3 `Any` additions, all in B's test helpers (B-owned; not
re-adjudicated here); the 3 removed `assert` lines are rewrites (peer-absent assertion moved into its parameter
branch; the 60 and 144 arithmetic checks split into `None`-narrowed variables with identical literals). A's shape
wrapper keeps call-time lookup of `rkuarch.workload.prepare.prepare`, so producer traps still apply; all literals
(1184, 596, 96, 60, 128, 144, …) unchanged.

Runtime, `PYTHONPATH` = export `src:contract` only (never repo root; `import-locations.log` shows `rkuarch`,
`uarch_contract` and `rkuarch.provenance.companions` resolve inside the export, not the old editable main checkout):

| Selection | Result |
|---|---|
| `test_production_isolation` + `test_missing_peer_refuses_without_breaking_other_commands[2]` + `tests/unit/test_u2_a_shapes.py` | **30 passed** |
| `tests/unit/test_u2_a_companions.py`, `tests/integration/test_u2_a_companions_cli.py`, `tests/unit/test_u2_b_companions.py` (real B helper) | **96 passed, 0 failed/errors/skipped** |
| `tests/unit/test_vendor_script_entry.py` | **9 passed** |
| `test_vendor_tooling.py`, `test_u_p2_review.py`, `test_u2_historical_snapshot.py`, `test_committed_snapshot.py` | **86 passed, 2 failed** — exactly `test_current_canonical_is_exact_adopted_1008_four_real_refusals` and `test_current_snapshot_generator_compatibility`, both `ValueError: input support inventory changed` (expected, unbypassed) |
| `python -B scripts/vendor_rk.py --check` (direct) | exit 1, `vendor-rk: input support inventory changed` — real support refusal, no import failure |
| `python -B scripts/vendor_rk.py --check --historical` | exit 0, "historical integrity and recorded identity ONLY; current compatibility not checked" |
| `test_production_isolation` on `57e97584` (before control) | **failed**: `production vendor isolation: …/src/rkuarch/cli.py:[447, 510]` |

Reviewer correction: my 2026-10-10 companion adjudication accepted the A-F3 software portion on `57e97584` without
running `test_production_isolation` (it was not in the 124-test selection); that tree in fact violated the unchanged
production-isolation guard via the dynamic peer import. The author's static-import correction fixes it here.

## Random revert/restore and supplementary revert

- Candidates (relevant applied behavioural changes): **S1** `cli.py` static
  `from rkuarch.provenance.companions import assemble_stub_context` replacing `importlib.import_module`;
  **V1** `scripts/vendor_rk.py` `import sys` + `if not __package__: sys.path.insert(0, str(ROOT))` in `__main__`.
  `secrets.SystemRandom().choice` → **S1** (logged with timestamp).
- **S1 revert** (exact reverse hunk in `S1-revert.patch`; reverted `cli.py` sha256 `39f4745c…` = the `57e97584` blob):
  `test_production_isolation` **fails** (isolation violation), both `test_missing_peer_…` parameters **fail**
  (`assert [] == [('assemble_stub_context',)]` — no static import attempt observed), while both real-peer
  `test_real_cli_rejects_wrong_indexes_or_missing_attempts` controls still pass → **3 failed / 2 passed**. Behavioural,
  not setup. **Restore** (`git checkout`; `cli.py` sha256 `b26ddf92…` = target and reconciliation hash): **5 passed**.
- **Supplementary V1 revert** (`vendor_rk.py` = `0fb1900a` blob `992c3762…`): `test_vendor_script_entry.py`
  **2 failed / 7 passed**, exactly the two `[direct]` cases with `ModuleNotFoundError: No module named 'scripts'`;
  the actual direct command fails the same way, while `python -m scripts.vendor_rk --check` still reaches the real
  support refusal. Restore (`787d30d5…`): **9 passed**. A targeted import-failure regression, as required.
- B's `test_re_reviewed_subset_cannot_erase_supplied_capacity_failure` keeps the authentic capacity input in the
  store, removes it from intake with re-indexed, re-reviewed recipes, and requires the specific
  `ComparisonIntakeMismatch` — it distinguishes acceptance from a different refusal. It passes in my 96-test run;
  its hook-removal discrimination belongs to B's own reviewer.

## Per-original-row adjudication

| Row | Response now | Stage 3 disposition |
|---|---|---|
| **A-F1** (BLOCKING) | Installed CI correction plus typing corrections (A 107, B 99 diagnostics) and shared vendor direct-entry fix | **Software response accepted.** The row at fault on 2026-10-10 (contract-tests typecheck failed under CI conditions) is corrected: both exact CI mypy commands, `ruff check .` and import contracts pass with `PYTHONPATH`/`MYPYPATH` unset, against a 206-error before control, with no ignores or config masking; the direct vendor command now reaches the real support refusal (V1 discriminating). **The finding stays OPEN as an exit gate:** hosted Ubuntu CI on the identical published commit and the U0021 fresh GitHub clone on ElfinKidsLaptop WSL2 are unexecuted, and CI's `tests` step marker expression collects both strict-support failures, so hosted CI on this source cannot be green until the combined freeze and human generation/adoption lifecycle. |
| A-F2, A-F4, A-F5, A-F6 | Accepted earlier | Not reopened; their tests in the selections above pass. |
| **A-F3** | Software portion accepted 2026-10-10; isolation regression corrected by S1 | **Software portion re-accepted on `53f9f21b`:** static peer boundary passes the isolation guard, exact-peer absence still gives `PeerImplementationMissing`, transitive import failures propagate, and the real-peer companion workflow (96 tests) is preserved; S1 random revert discriminates. **Open:** the real public demonstration with actual independent recipe/registry declaration reviews. |
| A-F7 | A-owned docs accepted; shared docs deferred | **Open:** `Makefile`, `CLAUDE.md`, `docs/how-it-works.md` command text are outside this delta and unchanged. |
| A-F8 | Deferred | **Open:** normative U0003 prose/link repair not in this delta. |

(a) every original row has a disposition; (b) no row is REJECTED; (c) the applied changes in scope have
discriminating tests (S1 random revert; V1 supplementary revert; typing verified against a before control).

## Verdict

**ACCEPTED** for the Stage 3 response checks on tree `53f9f21b7cc3f84c0cbdb5f3f1e74e6e4aeca522` — no original row is
at fault in this recheck. This is software-response adequacy only. It does **not** close A-F1 (BLOCKING) or any exit
gate: strict-support currentness (two failures, unbypassed), the combined source/input freeze and human
generation/adoption, the actual external recipe/registry review and public demonstration (A-F3), normative/link text
(A-F8) and shared command docs (A-F7), the U0021 fresh GitHub clone on ElfinKidsLaptop WSL2 with hosted Ubuntu CI on
the identical published commit, and separately controlled publication/tag/closure all remain open. A local archive
or U1 CI cannot satisfy U0021. No full suite, full 1,008-case matrix or hosted-CI pass is claimed here.
