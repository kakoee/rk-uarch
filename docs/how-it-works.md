# How rk-uarch works

This describes the validated U1 implementation published at
`44559fb1672e4d3468b4b6fc930cfdf4b4c1e99e`. U1 provides the shared contracts, generated
schemas, a human-generated rk-sim evidence snapshot and a test-only parity harness.
There is no simulation engine, workload producer, working table/report CLI or engine
result yet. The [U1 closeout](reviews/U1-closeout.md) records validation and Javid's
2026-10-07 G1 approval and closeout acceptance. Closeout publication and `u01-end` tagging
remain separate pending steps.

## Contracts and their limits

The Python package [uarch_contract](../contract/uarch_contract/) defines
`uarch-contract/0.1`: sourced hardware values, HardwareSpec, ModelSpec/ModelShape,
operator vocabulary, precision, requests, rows/tables, model cards, error records and
canonical hashes. [U0001](decisions/U0001-the-integration-contract.md) is accepted in full.
The 69 committed [JSON Schemas](../contract/schema/) describe the wire structure;
Python validators additionally enforce cross-field semantics. Schema validity alone
cannot establish provenance truth, artifact identity or evidence applicability.
Round trips and schema freshness are pinned by `test_round_trip_all_models` and
`test_schema_freshness` in [the contract tests](../contract/tests/test_u_p1.py).

| Boundary | Implemented behavior and tests |
| --- | --- |
| Hardware provenance | Claims require provenance and, except stubs, a source; stipulations require rationale and are refused in reference hardware. Hardware leaf units are checked without conversion. See [source/refusal tests](../contract/tests/test_u_p1.py) and [unit-map regressions](../contract/tests/test_u_p1_review.py). |
| Pinned vocabulary | ModelSpec fields and PrecisionFormat members match the vendored pin. Five-field claims round-trip; stipulations cannot become upstream claims. The accepted exception is stricter stub handling: uarch requires `source=None`, while upstream accepts blank strings. No blank-to-null conversion occurs. See [vendored round trips](../contract/tests/test_vendored_round_trip.py). |
| DRAM origin | Explicit `direct`/`preset` timing mode is required. Preset claims bind to the named file and full SHA; no citation-string heuristic or fallback selects a preset. See `test_timing_mode_is_required_and_direct_has_no_preset` and preset regressions in [test_u_p1.py](../contract/tests/test_u_p1.py). |
| Shapes and requests | ModelShape checks total/active parameter consistency; requests validate shard divisibility and balanced KV replication. MoE's two FFN-width fields must agree. These validate descriptions; they do not build a workload. See [shape/shard tests](../contract/tests/test_u_p1.py) and [MoE regressions](../contract/tests/test_u_p1_review.py). |
| Fidelity | All-zero hardware detail is C0; C2 requires compute 2, NoC/DRAM 2 or 1+ts, exact sync and 1+ts shared SRAM if present. Other detailed combinations are C1. Omitted shared SRAM means physically absent; explicit null is refused. Approximate sync never promotes fidelity. See exhaustive composite tests and the no-SRAM C2 roofline test in [test_u_p1.py](../contract/tests/test_u_p1.py). These are carrier rules, not delivered engine fidelities. |
| Table identity and cycles | `hardware_spec_hash` is required, survives round-trip and participates in the table digest. Only `provenance.conditional_on[*].value` may echo hardware stipulations in cycles; results and derived params cannot. See [A-F1/A-F2 regressions](../contract/tests/test_u_p1_followup.py). Actual spec/path/value equality belongs to U-P3. |
| Hashes | Validated defaults, sorted object keys, normalized signed zero and preserved list order determine canonical identity; only the table's own top-level digest is excluded from its hash. See `test_hash_fresh_processes_and_key_order` in [test_u_p1.py](../contract/tests/test_u_p1.py), [canonicalization regressions](../contract/tests/test_u_p1_review.py), and [hardware digest coverage](../contract/tests/test_u_p1_followup.py). Parsing a digest string does not authenticate it. |
| Evidence carriers | Unsampled errors and unmodelled diagnostics remain null, not zero. Above-stub cards require evidence IDs, but the carrier does not load a ledger or promote a model. Energy needs its own evidence. See [null/default tests](../contract/tests/test_u_p1.py) and [badge/error/energy regressions](../contract/tests/test_u_p1_review.py). |

A future table represents one chip's shard, one iteration, all layers, without collectives.
The table consumer must not divide already-sharded work by tp again. These are accepted
[seam requirements](decisions/U0001-the-integration-contract.md#the-nine-seam-rules), not
implemented reader behavior. The existing [toy table](../contract/tests/fixtures/toy_table.json)
is handwritten synthetic carrier data with synthetic identities; it is not an engine run.
Its nulls and explicit `not_run` parity classification are checked by
[the toy tests](../contract/tests/test_u_p1.py) and
[parity-carrier regressions](../contract/tests/test_u_p1_followup.py).

## Vendored evidence and isolation

The committed [snapshot](../contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963/)
binds upstream `1e5706e0ebfcc67c1a7333079a35b75f693e9963` to manifest SHA256
`b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d` and the publication
commit above. It contains 20 files: upstream sources/schema/lock, two component inputs,
three attributed model-shape sidecars, generator metadata, 864 oracle records, two precision
refusals and the manifest. Counts, coverage, component digests, sidecar attribution and
refusals are checked by [test_committed_snapshot.py](../contract/tests/test_committed_snapshot.py).
Exact generator and oracle identities are in [the closeout](reviews/U1-closeout.md#publication-and-artifact-identity).

The oracle records came from pinned rk-sim `iteration_cost()` through human-operated
[vendoring](../scripts/vendor_rk.py). Javid's two saved runs report
[created](reviews/U1-publication-records/generation-first.log) and
[verified-identical](reviews/U1-publication-records/generation-second.log).
They cover three models, tp 1/8, and 24 decode/prefill queries across six
component/precision groups. Placeholder inputs are stub arithmetic fixtures. Oracle
counts are replica-wide; oracle durations describe one representative tp rank without
collectives. They are rk-sim reference evidence, not rk-uarch predictions or hardware
accuracy measurements. Coverage and recorded scopes are pinned by
[committed-snapshot tests](../contract/tests/test_committed_snapshot.py) and
[vendor-tooling tests](../contract/tests/test_vendor_tooling.py).

Strict verification separately checks manifest integrity, recorded identity and current
compatibility with the exact generator/oracle fingerprints and locked generation-environment
metadata. A matching manifest alone proves neither adoption nor authenticity. Tests load
vendored classes privately; production imports of rk/vendor/test helpers are forbidden.
CI consumes committed bytes without an upstream checkout, oracle rerun or credentials.
See [U0002](decisions/U0002-the-vendored-snapshot-and-parity-discipline.md),
[strict compatibility/isolation regressions](../contract/tests/test_u_p2_review.py), and
[the workflow](../.github/workflows/ci.yml). Any later generator change requires the
reviewed human artifact-refresh lifecycle, including at the same upstream SHA.

## What the parity harness proves

[The harness](../contract/tests/parity.py) compares a candidate's counts with a uniform
replica/tp projection only within supported unreplicated, unpadded scope. It refuses
replicated KV, padding and missing scope dimensions before calling the candidate,
retains every fixture's outcome, and prevents incomplete coverage from entering a success
carrier. An ordinary numerical failure remains failed. See
[projection and coverage tests](../contract/tests/test_projection_scope.py).

For each positive-reference fixture/channel, raw error is `(actual-reference)/reference`.
Named adjustments consume a total absolute budget of at most 5%; the residual after signed
adjustments must be within 0.5%. Splitting or cancellation cannot recover budget. Zero/null
references have no relative-error denominator and permit no adjustments. Tests pin these
boundaries in [test_u_p2_review.py](../contract/tests/test_u_p2_review.py) and
[test_u_p1_followup.py](../contract/tests/test_u_p1_followup.py).

The harness preserves fixture/channel attribution, raw error, signed adjustment, absolute
spend and residual in the contract carrier. Its default is `harness_self_test`; even a
frozen-oracle echo remains a self-test after serialization. A caller-supplied
`workload_parity` label and identities cannot authenticate an arbitrary implementation.
See [carrier integration tests](../contract/tests/test_parity_carrier.py). All current
parity runs test the harness, not an actual U2 workload. The test-only Channel translation
changes names without scaling, tp division or null conversion, as checked in
[test_vendor_tooling.py](../contract/tests/test_vendor_tooling.py).

## Validation and what comes next

The exact publication passed 379 strict contract tests, 385 full-suite tests, four
prompt-sync checks, mypy (47 source files), Ruff, two import contracts, schema freshness
and strict vendor verification. Exact commands and outputs are in the durable
[cold-clone report](reviews/U1-cold-clone-evidence/report.txt) and
[closeout command table](reviews/U1-closeout.md#published-revision-validation).
Same-commit [hosted CI](https://github.com/kakoee/rk-uarch/actions/runs/37585143201) succeeded.
Its golden, determinism, native, perf, ordering and patch checks were conditional no-ops;
the closeout distinguishes them from executed checks.

There are no real engine rows to quote, no golden designs with a composite or badge, and
no engine stipulation count or measured error band. Those sprint-refresh requirements are
inapplicable to U1; neither the toy nor the oracle echo substitutes for them. Engine
L0/L0m/L1, worker/thread determinism, native/fork comparison, silicon validation and
performance-host measurements are also inapplicable. Error remains unknown and energy
unverified; passing contract tests does not raise an accuracy badge.

[U0019](decisions/U0019-standalone-preparation-and-prepared-input-replay.md) fixes standalone
preparation and prepared-input replay ownership. G1 is approved; at U2 kickoff, U0003 must settle
concrete payloads, identities and compatibility before U2 implementations diverge. U2
then owns producers, U-C0, actual workload parity, table/report paths, artifact-aware
checks and replay acceptance. Read the [U2 kickoff obligations](reviews/U2-kickoff-obligations.md)
and [closeout carry-forward](reviews/U1-closeout.md#u2-obligations-and-later-boundaries),
including B-F16, A-F9 and unresolved embedding accounting. No U2 implementation is included
in this refresh.
