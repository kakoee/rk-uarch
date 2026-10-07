# U1 Lane B → Lane A: proposed flop_parity carrier revision

Stage 2 handoff, 2026-10-06. Javid approved **scope before G1**, not a completed schema.
A owns the contract, schemas and toy table. B has not edited them. U0002 remains proposed.
This handoff uses the approved total-absolute adjustment policy; it does not replace
U0019/U0003 preparation ownership or introduce a workload generator.

## Requested interface

Preserve a typed record; do not infer classification or attribution from free-text labels.
The top-level proposed `FlopParity` fields are:

| Field | Meaning / constraints |
| --- | --- |
| `kind` | `not_run`, `harness_self_test`, or `workload_parity`; never default to workload parity |
| `reference_basis` | `rk_sim_aggregate_divided_by_tp`; explicitly an approximation, not a physical rank-local correctness claim |
| `fixture_set_id` | Required nonblank identity for compared inputs, or null when not_run |
| `oracle_manifest_sha256` | Full manifest digest for actual workload comparison; synthetic self-tests may use null |
| `candidate_identity` | Nonblank implementation/revision identifier for the supplied callable, or null when not_run; caller-provided, not automatically authenticated |
| `n_fixtures` | Number of distinct fixture ids represented; positive when run, zero when not_run |
| `max_rel` | Maximum absolute **raw** relative error across positive-reference comparisons; null if not_run or no such comparisons. Not an accuracy/error-band field |
| `comparisons` | Sequence of named per-fixture/channel records below; empty iff not_run |

Each proposed `ParityChannelComparison` contains:

| Field | Meaning / constraints |
| --- | --- |
| `fixture_id`, `channel` | Unique pair; channel is a compared Row.counts name, currently matrix_ops/memory_read_bytes/memory_write_bytes |
| `unit` | `op` for matrix/vector operations, `byte` for memory; unit is the same for actual/reference; one MAC is two operations |
| `actual`, `reference` | Nonnegative finite counts, or null for unmodelled counts; explicit unit field removes ambiguity |
| `reference_state` | `positive`, `zero`, `unmodelled`; must match reference |
| `raw_rel` | (actual-reference)/reference when reference >0; otherwise null |
| `signed_adjustment_rel` | Sum of declared signed ratios; positive means more work than reference |
| `absolute_adjustment_rel` | Sum of absolute declared ratios; bound ≤0.05 per fixture/channel |
| `residual_rel` | raw_rel - signed_adjustment_rel; absolute bound ≤0.005 when defined |
| `declared_deviations` | Sequence `{id, deviation_rel, reason}`; unique nonblank ids and nonblank physical reasons within this comparison |

All `_rel` values are dimensionless ratios, not percentage-point numbers. The denominator
is the **positive projected oracle reference for this exact fixture/channel**. No cross-channel,
fixture or model budget pooling. Report raw, signed, absolute and residual separately.

Positive-reference cases with abs(raw_rel) ≤0.005 require no declarations. Otherwise,
all declarations spend absolute budget including opposing terms; abs(residual_rel) ≤0.005
and absolute_adjustment_rel ≤0.05. Zero reference requires actual=0, no declarations,
raw/residual=null and signed/absolute adjustments=0. Unmodelled reference requires
actual=null, no declarations, raw/residual=null and signed/absolute adjustments=0.
The known absence of adjustment does not turn an unmodelled count into zero.

`not_run` requires empty comparisons, zero n_fixtures, null max_rel and null input/candidate
identities. A self-test cannot be serialized as workload_parity merely by removing its kind.
Actual workload classification needs the later producer's reviewed adapter and implementation
identity; no validator can authenticate an arbitrary callable. A rejected comparison must
raise or be stored as separately typed failure evidence, not as a successful FlopParity.

## Representative payloads and B adapter handoff

[Payloads](U1-lane-B-flop-parity-payloads.json) contain synthetic examples for not_run,
a self-test with a +5.5% raw delta explained by +3%/+2%, a null channel, an exact-zero
channel, an unadjusted +0.4% channel, and a **hypothetical** workload-classified example.
The workload sample is interface data, not a reported workload result. No real oracle
values, sources, hashes or artifact identities are claimed by these samples.

B reports now have an explicit `comparison_kind` independent of the human-readable label,
n_fixtures, max_rel and a nested comparisons map containing same-run actual/reference/unit
and all four quantities. `contract_payload` flattens records and validates them through A's
actual FlopParity. It never reruns the candidate or infers authenticity from equality.
A independently implemented this proposed interface; B captured that complete A proposal
(initial identity `aa568a839e401047a242f24b176274fc144ac364e8d9924ca4880480b1a03258`) and
added seven passing cross-lane tests. This remains a reviewed-proposal boundary, not ADR acceptance.

## Integration and acceptance tests

1. Completed: A supplied the carrier/validators/schema/toy proposal, copied unchanged into
   `/tmp/u1-b-response-carrier-9sinndh2`. A owns any further model revisions.
2. Completed: B adapter plus seven cross-lane tests, with 6 failing/1 passing before the
   adapter and all 7 passing afterward. They preserve classification, fixture/channel/unit,
   declarations and all four quantities, including exact zero/null, cancellation spending,
   the +5.5% boundary and serialization of all 864 oracle echoes as self-tests. Missing
   structured classification fails; a human-readable label cannot substitute for it.
3. Pending: independent review/adjudication and full ADR acceptance. Further A changes
   require a fresh captured integration. No actual U2 workload parity is claimed; even the
   explicit workload-classification test is synthetic protocol data, not a workload result.
4. No A worktree was modified by B. Complete G1 remains pending the human gates and a
   reviewed current-compatible human-generated artifact.

## Approved A-F12 scope and separate embedding decision

**A-F12 interim scope policy approved by Javid:** uniform division by tp is eligible
only for the declared unreplicated, unpadded shard scope. Known KV replication or
nondivisible vocabulary/head/FFN shard dimensions produce `unsupported_projection`
before the candidate is called or numerical agreement is considered. Missing required
scope dimensions also fail closed. This guard neither rejects all tp>1 nor certifies
physical correctness; A's broader legitimate request shapes remain valid contracts.
A component-aware projection remains future reviewed work for U-P3.

The frozen oracle is evidence of rk-sim's aggregate calculation. No existing workload
result is relabelled aggregate compatibility, and no new physical-correctness certification
is introduced. `rank_counts` is diagnostic arithmetic only, not an eligibility check.
The harness implements no diagnostic bypass that can satisfy the workload-parity gate.

`run_parity` retains every requested fixture in `coverage`, with `passed`, `failed`, or
`unsupported_projection` and explicit reasons. Any nonpassing entry raises `ParityFailure`
carrying the complete report; later fixtures are still evaluated. Supported numerical or
candidate implementation failures remain `failed`, never relabelled unsupported. Reports
retain available actual/reference values and all four adjustment quantities even for an
over-budget numerical failure. No partial run can enter A's successful FlopParity carrier:
B's adapter requires complete passing coverage and preserves the caller's explicit kind.
Default oracle echoes remain harness self-tests. All 864 baseline fixtures are eligible;
no frozen value, nominal input, fixture or approved tolerance changes.

**Embedding accounting is separately pending.** The approximately 6.54% nominal 8B
embedding parameter share is not an observed operation/duration offset. Preserve nominal
U1 inputs and report actual discrepancies explicitly under the approved budget. An ordinary
above-budget numerical error remains a visible failure. Only a documented scope incompatibility
can justify unsupported status; the replication/padding decision is not an embedding exception.

The current captured A revision and exact interface hashes are recorded in the latest
response/handoff validation section. Failed/unsupported run reports are separate evidence,
not a new Lane A schema or a successful FlopParity payload.

Latest aligned complete A content identity:
`3f408194c6e26165770e35675b72939469dfe74d660b7e5d6b778bad18a3f773`, HEAD af3b1bc.
Fresh integration `/tmp/u1-b-scope-integration-3d8bfs06` validates the same carrier code/schema
with A's latest handoff and regressions. Scope/failure reporting is B-owned; A's successful
carrier remains unchanged. See the response for exact per-file interface hashes and results.
