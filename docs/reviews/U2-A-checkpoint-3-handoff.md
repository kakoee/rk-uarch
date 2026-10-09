# A remaining-A2 checkpoint — coordinator reconciliation

Status: A-owned remaining runtime checkpoint, uncommitted. This is not a B report,
independent U-REVIEW, generator/adoption exit, publication or sprint closure.

The starting boundary was the cleared 344-entry A2 manifest
`38e6f3b74d3b13599b9035909e794f43787caa337f20c4f400ec802569784dfa`.
All 344 payloads verified in live A before edits. `received-baseline.json` records
648 tracked/untracked file hashes, branch `u2/analytic`, HEAD
`1e9e794a84c5173812c23a1cf2fc04b85e6f6831` and the full received status.
Historical proposal/A1/A2 handoffs, logs and manifests remain unchanged. The original
116-entry proposal and preserved snapshots are immutable history; an old live-root
manifest is not regenerated to describe these newer source bytes.

Only three existing paths advance against A2: `src/rkuarch/cli.py`,
`src/rkuarch/workload/prepared.py` and `src/rkuarch/table/artifacts.py`.
Other runtime/test/checkpoint paths are additions. The exact old/new hashes and full
file list are in `U2-A-checkpoint-3/changes-from-A2.json` and `checkpoint-paths.txt`.
The full dirty-payload manifest includes received A1/A2 work, not just this delta.
No stage, commit, push, tag, dependency change, agent/message, cleanup, other-worktree
edit, human flag or adopted/vendor artifact write occurred.

## Delivered preparation and physical behavior

`workload.prepare.prepare(intent, hardware, *, rank_index=0, embedding_hits=None,
synthetic_assignment=False, attention_mask="full_square", lm_head="all",
fused_attention=True)` returns the accepted `PreparedBundle`. ModelSpec/ModelShape
parity and TP divisibility are enforced through RequestIntent. The producer uses
only declared model/shape/precision/query/hardware inputs, without oracle or expected
fixture lookup. The local sidecar loader reads explicit existing model and shape
objects and checks parity; it does not fetch model data.

Points use declared decode B/context/frequency then prefill n/L/frequency order.
D7 hit vectors conserve tokens. TP>1 requires supplied counts or explicit synthetic
assignment; the latter assigns remainder tokens to the lowest ranks. Equivalence
is the exact set with equal captured work across every point. A selected rank with
zero local embedding hits reads zero embedding weight bytes while still writing
the full masked activation. No all-token-per-rank inference occurs. Default attention
is fused/full-square, default prefill head covers all tokens; explicit causal,
unfused/materialized-score and last-token cases remain distinct captured work.

Imports never call the producer. They retain producer identity, op IDs/order,
dependencies, shapes, accesses, padding, replication, multiplicities and omissions.
Checks now include explicit KV replication and paging, padding logical/physical
correspondence, group completion dependencies, unfused score/probability connections,
Q/K/V/append/output extents and connected FFN padding. Rehashing an invalid graph
cannot repair these invariants. A valid explicitly padded imported FFN executes its
larger physical work, rather than being regenerated to the producer's default.

`capacity_summary(bundle, point)` returns `CapacitySummary(weight_bytes, kv_bytes,
total_peak_bytes, warnings)`. Known allocations include distinct layer weights,
all stored experts once, replicated routers, tied embedding/head sharing once and
page-rounded KV. Active expert work is separate from stored expert allocation.
Weight overflow refuses; weights plus KV overflow warns. `total_peak_bytes` and
both table peak fields remain null because activation lifetimes are unmodelled.
The 372-parameter BF16 literal has 744 weight bytes and 512 page-rounded decode KV
bytes at T=17/block16. Its actual counts remain 1184 matrix, 572 vector, 1296 read
and 288 write bytes, with 1,892,000 ps per-op and 1,584,000 ps aggregate duration.

`characterize(bundle)` emits raw captured EngineJobs/EngineResults and partial
capacity summaries for workload selection. It is not a proof or rendered report.
`unmeasured_errors()` keeps all four error families unsampled/null; observing equal
cold/steady numbers does not turn that into a measured error experiment.

## Table, subprocess and offline package

`api-inventory.json` contains every exact signature and Python return field.
All 31 A1 plus 16 delivered A2 signatures are unchanged. `VerifiedReportInputs`
retains exactly its 20 existing fields and shared carrier types. There are no
production schema changes, private evidence types or alternate report wire formats.

- `prepare_engine_job(bundle, point_hash, *, assumptions)` validates the full capture
  and returns the shared EngineJob without running preparation or an engine.
  Existing `execute_prepared_point` remains the in-process boundary with its old signature.
- `capture(bundle, *, assumptions, workers=1, subprocess_engine=False)` returns
  `CapturedWork(bundle, assumptions, request, derivation, jobs, results)`.
  Only workers=1 is supported. CLI table/capture uses the JSON subprocess route;
  the optional in-process route invokes the same core. The child accepts one strict
  EngineJob and emits one canonical EngineResult plus LF; failure is nonzero with
  stderr diagnostics. A test disables the parent engine and still executes the child.
- `build_table(captured, *, context, model_card, artifacts)` returns
  `TablePackage(table, artifacts)`. It requires the externally supplied reviewed
  context/card/closure; it manufactures neither a review nor evidence eligibility.
  Failed comparisons in the supplied context remain bound as attempted comparisons.
- `write_table(package, path)` validates the full package before writing the table
  and exact hash-named companions. Every supplied companion, including unused raw
  bytes, must have a valid identity/name. Differing existing destinations refuse.
  All bytes are canonical JSON plus LF except explicitly raw companions.
- `verify_report_inputs(table, artifacts)` adds an in-memory counterpart to the
  unchanged disk loader. Both use the same captured-record/source validation body;
  memory verification has no filesystem fallback.
- `ps_to_seconds(x)` is the one production table conversion, exactly x/1e12.
  Rows copy counts and OpResults without reinterpreting per-op estimates as aggregate
  row times. Duration, U-C0 and critical-path attribution convert once. Fractional
  picoseconds remain finite floats. Diagnostics/extended counts/total peaks stay null.

CLI commands are `prepare`, `capture`, `table`, `characterize` and `rk-component`.
Prepare/table/characterize accept a captured bundle, an explicit RequestIntent plus
hardware, or named/local model sidecar plus hardware. These routes are mutually
exclusive. Imported overrides refuse even when the supplied value is zero.
Named-model convenience defaults are explicit captured inputs: TP1, one decode
sequence/context1, one prefill prompt/token1, frequency1, steady, per_op, block16,
seed0 and layer reuse. `--grid`, `--tp`, `--precision`, `--kv-precision`,
`--initial-state` and `--analytic-mode` select alternatives before preparation.
TP>1 still needs explicit assignment input/opt-in. Checkout-local named sidecars are
llama-3.1-8b, llama-3.1-70b and mixtral-8x7b; explicit local sidecar paths are supported.

`rk-component` consumes an explicit execution-model file, writes truth/derivation,
and optionally the test projection/binding. The actual accepted H1 export test uses
component ID `compute.asic.npu-l4` and reproduces the prior descriptor bytes exactly.
Its accepted claim/stub nominal1.0 input is unchanged. The B rejection remains
B-owned U2-AB2-C1; neither hardware nor the retained .55 input was changed for it.

## Exact raw capture for B

`table_recipes(captured, *, generic_rows=False)` returns tuples of shared
MetricRecipe and SourceMetricRecipe declarations for external review. Every actual
result channel has its own result hash, pointer, independent model identity,
purpose, granularity and dimensions. Coverage includes four row counts, row/U-C0
duration, all five attribution parts and the existing fourteen numeric OpResult
surfaces. A generic `/rows/*/...` recipe explicitly lists the exact corresponding
source from every row; wildcard source lookup or substitution is not implied.
The loader still requires each row's exact actual source, full terminal contributors
and recursive independent source purpose/model/scope.

`computation_sources(job, bundle)` supplies captured DependencySelectors;
`source_scopes(captured, *, family)` maps `(result_hash, source_pointer)` to tuples
of accepted EvidenceScopeCase fields. Operator sources have one operator scope;
whole-iteration sources retain every executed operator scope. The fields include
exact hardware/bundle/model identity, frequency, state, KV block size, op class,
compute/KV/operand precisions, array-fill and intensity regimes. Mapping correspondence,
mapping-match and unrepresented load regimes remain null. B supplies the family from
its reviewed registry, and owns expansion/applicability/proof interpretation.

`legacy_model_id(job, bundle)` projects exact engine/version/fidelity/mapping fields
for B without badge inference. `consumed_energy_families(captured)` returns `()`:
this physical analytic engine consumes no energy coefficient, including static power.
Builder context must agree. Energy verification eligibility and display remain B's.
A consumer can reconstruct CapturedWork directly from the unchanged loader's bundle,
assumptions, request, derivation, jobs and results. These helpers capture inputs;
they confer no independence, silicon validation or numeric-display permission.

## Executed evidence and limits

The final check records, saved table-replay results, API inventory and immutable-input
verification are under `U2-A-checkpoint-3/`. Exact final counts/timings and table hashes
are summarized in `completion-results.json`; old A2 logs are not presented as new.
The check runner records argv, cwd, environment, return code, elapsed time and source
hashes at start. The two late narrow refusal fixes have separate tests-first and
follow-up records; their source hashes are distinguished from that initial run.

Tests were written and run before the producer, table/time/CLI/subprocess bodies and
before each later defect correction. Snapshots and red logs are preserved. The initial
MoE test miscounted router parameters and was corrected before the producer body.
The H2 test initially serialized forbidden shared_sram=null, and the export test used
a different component ID; both fixture corrections are separately visible. The first
table run exposed canonical_json's string return and was interrupted after that failure;
its log is not a green check. Raw-artifact and zero-override regressions failed before
fixes. One formatted-in-flight traceback has changed source line presentation; the
saved tests-first snapshot identifies the actual test semantics. The first saved
replay probe had a missing test-helper import path; that failed attempt is preserved.

Actual standalone table creation, saved prepared-input replay with producer/oracle
imports trapped, subprocess execution and thread/hash-seed1/4 byte comparisons are
recorded by `table-replay-probe.py.txt`. The actual table has comparison_state=not_attempted. The table numbers come from executed prepared
operators. Its external review records are explicitly **synthetic test scaffolding**,
not a B runtime report, real independent review or evidence of model accuracy. All
companion bytes as well as table bytes are compared. `h2-characterize.json` separately
records actual npu-m256 × Llama-3.1-70B × FP8/TP8 execution with synthetic assignment.

Executed physical tests include selected rank/conservation, MoE/tied/router residency,
weight refusal/KV warning, causal/full-square and all/last head cases, materialized
unfused traffic, connected physical padding, KV replication/paging, explicit-layer
versus reused-layer work, cold/steady identity, H2 FP8, independently checked 8B/Mixtral projection counts, mixed BF16-compute/FP8-KV roles, frequency .5/1/1.5/2 and a
12-example deterministic conservation property test. Earlier precision/frequency/
fidelity/block-geometry refusals and independent one/fractional-ps tests remain in
regression. The five-channel physical-versus-nominal test retains 1184 vs1288 matrix,
572 vsnull vector, 1296 vs1016 read, 288 vsnull write and 1.892µs vs1.016µs duration.
It is an independent synthetic observation, not adopted-oracle coverage or physical parity.

A minimal carrier limit is explicit: a selected rank with an empty logical vocabulary
shard cannot express padding using accepted `Padding.logical >= 1`. It now refuses
rather than fabricating a logical slot. Supporting that case would require a separately
reviewed carrier relaxation/representation; no schema or policy was silently changed.
General arbitrary mapped graphs, multithreaded scheduling, workers>1, detailed fidelity,
scalable-DRAM nonbase rates and nonzero block-scale geometry are not claimed supported.
No exhaustive all-shape/frequency property proof, cold clone or hosted CI was executed.

B-reviewed runtime/report integration, B's exact full comparison inventory and refusal
matrix, generator fingerprint correction, accepted-input B helper correction, adopted
nominal fixtures, human two-run generation/adoption and final independent U-REVIEW
remain separate. No complete report, physical accuracy gate or sprint closure is claimed.
No substantiated person-hour change: A140–222/B100–154 plus fresh reviewer16–24 remains
planning scope, not elapsed execution time or a delivery promise.

Proposed message (not committed):
`feat(u2): complete standalone preparation, physical table and captured replay`

Stop for coordinator reconciliation. The proposed file list is the exact authored delta;
all prior uncommitted work stays preserved.

## Final observed results

638 distinct collected tests are covered by successful executed runs, with zero skips:
34 affected tests (473.54 s), 600 regression tests (202.04 s), and the documented
38/5/1 follow-up runs, with overlap explicitly accounted for in completion-results.json.
This is a union of executed runs, not a claim of a single 638-test invocation. Mypy
49 files, ruff, both schema freshness checks and whitespace passed. C1 refuses as
IncompleteMetricContributors; C2 refuses as RefusalSourceMismatch. Valid controls
remain in the passing preserved artifact/loader regressions.

Standalone and producer-disabled replay table bytes SHA256:
`bcf51e2fa00e4e42e5a05e3de696a9d6df86fd8aee8b358d5a91589b5866cdf9`.
Table content identity:
`sha256:9dcd81441b580dcf49e93813411163a04383dd5d5f5717a6f2d3a067a68040a2`.
All 15 companion files also match across the three saved CLI runs. The standalone
run took63.175s; trapped replay took64.100s and63.311s. These are local observations,
not a performance target or accuracy claim.

Original proposal116/common262/B1-addition45/corrected-A1262/cleared-A2344 all verify
at their identified roots. All301 earlier document files and133 production schemas
remain byte-identical to the received A2 worktree. H1 remains
`41731f6ac7fe99aaf221edaf917ffdd03cd0fcdd8149ee5f5110bfe42a5911c0`; H2 remains
`e12d08d40e7b3c0e7ab1443141745a6c082ee544ecfc43c5609c8cd289a35d9e`.
