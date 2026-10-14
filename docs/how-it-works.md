# How rk-uarch works

rk-uarch currently runs a stateless Python analytic model of one chip's resolved workload.
It can prepare inputs, replay saved work, and package **v1** estimates into tables and
provenance-aware reports. U3 adds explicit RoPE **v2** preparation, admission, execution
and raw capture/replay, plus standalone analytic verification reports. Native execution
remains future work.

This narrative targets implementation **`7afba9b16d954fd46684711764cb3718170e53aa`** plus
the five reviewed documentation postimages in
[closeout review.json](reviews/U3-closeout-documents-v1/review.json), whose
[patch](reviews/U3-closeout-documents-v1/closeout.patch) has SHA256
`2b0bc1934020e1d0da2d21ab3514d26c1595a780d3d539b300f79a05286d9416`.
Those postimages and this narrative were published in
`390ec9aa06eef33da6274eb28ae6ca1c3ae3d623`; the package’s original installation-pending
text remains historical. [Published validation](reviews/U3-published-validation-v1/README.md)
records the fresh GitHub clone and hosted CI on that exact revision.
[Javid’s technical acceptance](reviews/U3-closeout-acceptance.json) records U3 design/technical
closeout with the limitations below. Final record publication and `u03-end` tagging remain
separate; **U4 is not authorized**. [Closeout](reviews/U3-closeout.md) records the remaining steps.

## Inputs, scope and arithmetic

Hardware declarations distinguish sourced claims from reasoned stipulations. The accepted
examples below are proposed designs, not measured products. Their current no-evidence
analytic classification is C0 / STUB; these are not executed golden-table CI results.
[Hardware/provenance tests](../tests/unit/test_u2_b_badges.py) pin validation and badge rules.
The reproduction command below reads every sourced leaf and prints this inventory.

| Design | Grid | Declared formats | Stipulations | Current analytic composite / badge |
| --- | --- | --- | ---: | --- |
| H1 [npu-l4](../hw/designs/npu-l4.yaml) | 2 × 2 | BF16 | 59 | C0 / STUB |
| H2 [npu-m256](../hw/designs/npu-m256.yaml) | 16 × 16 | BF16, FP8 | 67 | C0 / STUB |

A prediction covers one chip's tensor-parallel shard, one iteration and all model layers,
excluding inter-chip collectives. Decode produces one token per active sequence; prefill
uses its declared prompt count and length. KV traffic uses valid tokens; allocation uses
page capacity. Fused attention omits a score-matrix spill. MoE uses active-parameter
dense-equivalent work and omits routing/communication. These are explicit accounting
choices, not measured efficiencies ([shape/count tests](../tests/unit/test_u2_a_shapes.py)).
Saved prepared input is authoritative: replay validates it without silently rebuilding
mapping or dividing the shard again ([prepared-input tests](../tests/unit/test_u2_a_prepared.py),
[public import test](../tests/integration/test_u2_a_stage2_cli.py)).

Both analytic versions calculate operator compute time as matrix work divided by matrix
rate **plus** vector work divided by vector rate. Memory time is read-plus-write bytes
divided by DRAM bandwidth. `per_op` sums each operator's maximum of compute and memory;
`aggregate` takes the maximum of the two whole-query sums. That aggregate is the U-C0
floor for the same resolved work, not a second physical timing oracle. Result admission
checks that arithmetic and attribution conservation
([literal arithmetic](../tests/unit/test_u2_a_analytic.py),
[aggregate/per_op regressions](../tests/unit/test_u2_a_stage2_result.py),
[v2 result/count checks](../tests/rotary_v2/test_boundary.py)).

C0 means compute, NoC and DRAM detail zero, with exact sync in the declared fidelity vector.
It does not mean accuracy. No modeled queues, cache history, DMA contention, placement,
physical utilization, energy or inter-chip communication can be inferred from these
rooflines. Attribution partitions the estimate; its zero NoC/overhead shares are not
measurements of those mechanisms. Unmodeled diagnostics and busy-time observations remain
null. Higher-detail analytic requests refuse
([v1 refusal](../tests/unit/test_u2_a_analytic.py),
[v2 admission and nulls](../tests/rotary_v2/test_boundary.py),
[composite contract](../contract/tests/test_u_p1.py)).

## Additive RoPE and preserved legacy behavior

The old `uarch-engine/1`, `resolved-ops/1`, `physical-resolved/1` route remains unchanged.
It accounts for its captured graph and **excludes RoPE rotation/conversion work and
coefficient traffic**. Its durations are not complete RoPE-equipped decoder estimates.
The explicit [dispatcher](../src/rkuarch/engines/analytic/dispatch.py) sends v1 jobs to
the original core; v2 requires its bundle and active assumptions. Wrong tags, mixed
versions and missing closure refuse, with no fallback or automatic upgrade
([routing/replay tests](../tests/rotary_v2/test_routing.py)).

The v2 route uses `uarch-prepared/2`, `uarch-engine/2`, `resolved-ops/2` and
`physical-resolved/2`. Preparation requires explicit position semantics and supplied
FP32 coefficient bits. It supplies no trigonometric coefficient generator or named-model
RoPE defaults. It rotates Q and newly appended K, declares rotated-before-store cache
keys, binds positions/profile/coefficient identity, and accounts for layer multiplicity,
local heads and KV replication. Existing cache encoding is declared, not numerically
authenticated. Logical projection-to-rotary element correspondence does not establish
physical layout equivalence or a free transpose
([admission adversaries](../tests/rotary_v2/test_adversarial.py),
[preparation and rank tests](../tests/rotary_v2/test_preparation.py)).

For E rotated elements, RoPE charges 3E scalar arithmetic operations and, for BF16/FP16,
2E casts through FP32. Unrotated tails still transfer; FP32 coefficients are read per
node/token/layer without retention or per-head duplication. Coefficient allocation is
known, while total peak residency remains unknown. These are scalar accounting laws,
not an executed numerical kernel or hardware instruction counts. Same-format FP32,
BF16 or FP16 activation/KV is required; RoPE FP8 is not admitted merely because H2
advertises an FP8 matrix rate. BF16-only hardware can hold the specified FP32 coefficient
table without an FP32 matrix engine
([literal counts](../tests/rotary_v2/test_boundary.py),
[precision/tail/preparation cases](../tests/rotary_v2/test_preparation.py),
[normative numerical reference tests](../tests/rotary_v2/test_pairing_reference.py)).

V2 execution identity binds the conservative local Python import closure, including
legacy dispatch dependencies. Changed source with unchanged version strings refuses old
jobs; changing loaded source requires process restart. This is distinct from installed
Python-package/environment identity and the broader U0002 artifact support inventory
([dependency-byte tests](../tests/rotary_v2/test_preparation.py)).
The current v2 implementation hash is
`sha256:c5420668fb3db8781168f4b8b9495a28474f001356cff10f1df9915158f8cdf6`;
the preserved v1 core hash is
`sha256:fa3938f8c009c7b80700d35feba7504e4b4da06e628d2e387480c358963974ea`.

## Tables, reports and what a badge permits

The existing [public workflow](u2-workflow.md) is prepare → capture → draft companions →
independent declaration review → assemble → table → report. It supports analytic v1 with
`workers=1`. Keep the adjacent artifacts directory with the table. Hashes bind hardware,
prepared work, assumptions, captures, recipes and report context; they establish content
identity, not performance accuracy. Producer-disabled replay and repeat bytes are tested
by the reproduced demonstration below and
[public companion CLI regressions](../tests/integration/test_u2_a_companions_cli.py).

Assembly needs actual accepted independent reviews of the exact recipe and registry
subjects. Missing, rejected or mismatched reviews refuse. Supplied failed comparison
attempts cannot be removed through a favorable subset; intake cannot authenticate an
attempt withheld from every supplied input
([assembly tests](../tests/unit/test_u2_b_companions.py),
[reference contributor tests](../tests/unit/test_u2_b_stage2_reference.py)).
The demonstration's existing reviews are explicitly **AI declaration reviews**, not
independent human review or measurement. Synthetic administrative records used in tests
supply no external authority.

Default HTML/Markdown hide unvalidated predictions. Explicit
`--show-unvalidated-predictions` reveals eligible finite executed estimates with STUB,
unknown error and conditions; it never upgrades the badge. Contributor closure applies
across all display surfaces
([display permissions](../tests/unit/test_u2_b_display_permissions.py),
[identity/stipulation display](../tests/unit/test_u2_b_stage2_display.py)).
Proposed designs cannot exceed estimated under
[U0004](decisions/U0004-stipulated-values-and-the-estimated-ceiling.md), and present results
remain STUB. L0–L2 verification is not silicon validation. Positive measurement/history
card eligibility and nonempty energy verification are unsupported; forged positive claims
refuse at build, memory, disk and CLI boundaries
([card regressions](../tests/unit/test_u2_b_stage2_cards.py)).
Error is **unknown**, confidence bands are null, and energy is **unverified**, never zero.

V2 currently stops at authenticated `CapturedWorkV2`: bundle, assumptions, request, ordered
jobs and results. Capture permits only one worker. There is **no public v2 table/report or
model-card/evidence attachment**. V1 carriers reject v2 data
([raw capture implementation](../src/rkuarch/table/capture_v2.py),
[routing tests](../tests/rotary_v2/test_routing.py)). A public v2 artifact therefore needs
accepted additive product carriers, CLI/build/report integration, v2 model/source/review
eligibility and conservative coefficient/contributor closure. No saved v1 review or
standalone v1 report can supply those missing dependencies. The v2 example below is a
real execution result, not a fabricated public table.

## Reproduce the current numbers

Run these commands from this repository root using the existing locked `.venv` (no sync,
installation or oracle generation). The bounded immutable probes write generated bulk
only under `/tmp`; they are documentation evidence, not maintained producer tooling.
The [evidence probe](reviews/U3-final-documentation-refresh/check-evidence.py.txt) prints
hardware inventory, active identities, v2 results and retained-report observations.
The [v1 probe](reviews/U3-final-documentation-refresh/reproduce-v1.py.txt) reconstructs
only the existing public demonstration, asserts every captured input byte against its
original receipt before reusing its actual reviews, and checks repeat/replay equality.
Changed subjects require a new review; do not bypass the assertions.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src:contract .venv/bin/python -B \
  docs/reviews/U3-final-documentation-refresh/check-evidence.py.txt \
  --output /tmp/u3-doc-evidence.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:contract .venv/bin/python -B \
  docs/reviews/U3-final-documentation-refresh/reproduce-v1.py.txt \
  /tmp/u3-doc-v1-summary.json
```

The v1 example is H1/Llama-3.1-8B, BF16 compute/KV, tp=1, nominal frequency,
steady stateless `per_op`, all layers, no collectives: **C0 / STUB prediction,
conditional on 59 stipulations, error unknown, energy unverified**.

| Public table row | Batch | Context per sequence | Duration (s), STUB | U-C0 (s), STUB |
| --- | ---: | ---: | ---: | ---: |
| v1 decode | 1 | 128 | 0.015038327296 | 0.015038327296 |

Table hash: `sha256:d55dfc66a0d33aff209a82353eba7e5316db20eb8cb51d56c9d6ab75124ba6be`.
Complete row content hash: `sha256:e2f0c393c09b90c0a3ff7761d7b2e6b529a493b4830032a8562138d860843467`
(a computed digest, not a new schema field). The probe runs the existing eight-point
demonstration twice and replays its saved capture with producers disabled. Its empty
comparison intake is scoped to that demonstration, not the broader comparison matrix.
[Review scope and identities](reviews/U2-public-demo-v1/external-review/review.md).

The v2 probe uses the **existing synthetic-d4 contract literal**, with its explicit
synthetic coefficient bits, and binds active assumptions exactly as the
[installed runtime regression](../tests/rotary_v2/test_boundary.py) does. It does not
prepare a named-model workload or generate coefficients. Conditions: BF16 compute/KV,
tp=1/rank0, steady stateless, two layers, two Q heads, one KV head, head dimension 2,
rotary dimension 2, adjacent pairing, nominal frequency, decode batch 1 with context 17. The fixture has
**zero stipulations**, but its test hardware claims are stub inputs; zero stipulations
is not evidence of measured hardware. This remains **C0 / STUB, synthetic-input analytic
prediction, error unknown, energy unverified**, with no product card attached.

| Raw v2 decode result | Matrix ops | Vector ops | Read bytes | Write bytes | Duration (s), STUB | U-C0 (s), STUB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| aggregate | 1184 | 632 | 1352 | 312 | 0.000001664 | 0.000001664 |
| per_op | 1184 | 632 | 1352 | 312 | 0.000001972 | 0.000001664 |

Aggregate `result_hash`: `sha256:e64c51900d4650458a40b8a8fc37fd34001f460d50f5edd87066e3b23ad2267d`.
Per-op `result_hash`: `sha256:7ff7c22f2ff8de71cfd96f89811d33ee706f0b4630ae155c99f416b56268982f`.
These identify complete engine results, not public table rows. The probe also saves
and executes both prefill results, authenticates ordered replay, and compares each public
subprocess dispatch result byte-for-byte. Its JSON records exact argv and stdin paths
under the printed temporary output root. No native timing or throughput follows from
these durations.

## Verification evidence has a scope

The [standalone analytic reporter](../validation/reporting/analytic_report.py) registers
L0 and L0m relations for both aggregate and per_op **model v1**. It binds the plan, corpus,
implementation, environment, jobs/results and all observed discovery/replay/mutant calls.
Validation requires caller-pinned expectations. Failed discovery survives later passing
replay; errors and shortfalls are not passes or mutant kills. NaN/opaque invalid returns
retain explicit diagnostics, rather than disappearing from the journal
([report regressions](../validation/reporting/test_analytic_report.py)).
This standalone source does not install production evidence/card eligibility.

The preserved [SR-C1 reports](reviews/U3-B-SR-C1/README.md) bind implementation
`85a5ad29820bc1c8638d844e192c6e4d778c107b`. The evidence command hashes their decompressed
bytes and reads the reductions; it does **not** rerun discovery or their qualifying replays.

| Retained report | Relation pass / skip / not_run | Whole rung | Duration purpose |
| --- | --- | --- | --- |
| L0 | 14 / 14 / 0 | partial / not_run | passed |
| L0m | 9 / 13 / 5 | partial / not_run | not_run |

The L0m aggregate-clock cell has **22 distinct admitted cases of 24 required**; repeated
inputs remain recorded. Deferred unused-stipulation and DRAM-clock cells remain not_run.
A whole-query reciprocal-clock law is not valid for per_op work containing memory-only
embedding and KV writes; the accepted aggregate remedy is not per_op evidence
([capability tests](../validation/L0_invariants/test_analytic_capabilities.py),
[accepted verification design](reviews/U3-native-stage-design-v2/verification.md)).

Canonical raw report SHA256 values are
`694682267f0d8d6fe30f150815313e1a00a36c35e565ac54ad2e9eea5d92b7e7` (L0) and
`2a57c5033aaf748087320cdad56ffd7f1a8a5a47118afaf3feb3f63baab79c84` (L0m).
At the current implementation, both public validator attempts with those historical pins
**refuse: `Implementation bytes changed`**. The binding includes source, contract and
validation execution bytes; additive RoPE and later changes fall within it. Reading valid
historical hashes is not current implementation validation. Revalidation requires the
compatible historical checkout/environment, or separately recorded fresh reports on a
clean committed current implementation. This dirty documentation workspace is not that
qualifying generation context. The probe records these refusals without weakening the
validator ([implementation-binding tests](../validation/reporting/test_analytic_report.py)).

## Installed artifacts and the prospective policy

Production does not import rk-sim. Vendored outputs provide test-only nominal compatibility,
separate from physical correctness, as required by
[U0003](decisions/U0003-one-chip-one-set-of-facts.md)
([nominal tests](../contract/tests/test_u2_nominal_candidate.py),
[physical discrepancy tests](../contract/tests/test_u2_physical_discrepancies.py),
[isolation tests](../contract/tests/test_u2_resource_isolation.py)).
The U3 [human adoption record](../tests/fixtures/u3_rope/received-adoption-review.json)
updates support binding for RoPE, not physical-v2 oracle coverage or silicon accuracy.

Current adopted manifest SHA256:
`1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a`.
Frozen-input SHA256SUMS digest:
`27c6238d42e57dc4f2b1baf0c8846c11f1eec2968176dcefcdc463beb64bc80f`.
The installed support inventory contains **97 files**. The evidence command reproduces
these identities and runs strict current verification; the direct command is:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/vendor_rk.py --check
```

Installed enforcement still enumerates the complete prescribed source/script support set,
locks and explicit inputs, and checks current bytes. Historical integrity mode does not
replace strict currentness
([enumerator](../scripts/u2_inputs.py),
[vendor/currentness tests](../contract/tests/test_vendor_tooling.py),
[adopted snapshot tests](../contract/tests/test_u2_historical_snapshot.py)).

The selected [prospective U0002 policy](decisions/U0002-the-vendored-snapshot-and-parity-discipline.md)
separates immutable generation provenance, artifact integrity and current compatibility.
Only future human-generated/adopted inputs with the exact versioned policy may use its
conservative generator/verifier import-and-data closure. It includes initializers,
function-local imports, all scripts and reserved local modules, guards new top-level
import names before non-bootstrap imports, and refuses unresolved dependencies, ambiguity,
symlinks and drift. Its reviewed bootstrap premises do not create a sandbox against
malicious interpreter hooks. Labels such as “report” or “native” never justify exclusions
if those bytes contribute to generation or verification.

That repair remains **unapplied**. Existing unversioned inputs retain complete enumeration;
the current valid source/artifact pair remains authoritative. Actual mapped-schema closure
must be audited before a separately authorized migration. A future transition still needs
exact source/policy/input freeze, human generation twice, full provenance/semantic audit
and separate complete-candidate adoption. No regeneration is needed just to document this
U3 decision. [Exact repair and limits](reviews/U3-B-U0002-bootstrap-followup-v1/README.md).

## What the native design does not implement yet

[Accepted U0011](decisions/U0011-the-native-engine-core.md) defines one progressive Rust
timing simulator, retaining the analytic baseline and Python preparation/product layers.
M prepares mapped carriers; K1 builds the internal kernel; K2 connects installed public
carriers; B supplies a bounded component model; R admits the actual reference suite;
T supplies full product tables. This is accepted design, not executed native evidence.
The [native workspace](../native/Cargo.toml) has no crates, and
[golden coverage](../tests/golden/README.md) has no committed expected tables. Empty jobs
cannot establish correctness, performance or replay coverage.

B initially targets a bounded npu-l4 BF16 q_projection component slice with explicit
DMA/unicast/barriers, at most C1. It cannot supply decoder, full-model, RoPE, FP8 or steady
product predictions. Exact mapped schema installation precedes K2; immutable toolchain,
license and build decisions precede K1. Numeric performance budgets remain proposals.
Independent component expectations and public-boundary faults are future acceptance work,
not newly executed tests in this refresh.

R establishes usable reference input and measurement scope before prediction freeze.
TPU/Blackhole draft reference unknowns remain explicit
([sourcing inventory](../hw/U2-sourcing-inventory.md)); no hardware access, silicon results
or successful validation is inferred. Full tables first serve **U7/G3b**; rk-sim integration
is **U10**, requiring its separately accepted boundary plus G6/G3b. G5 correctness,
performance and automation are distinct outcomes. Missing silicon success does not by
itself prevent honest tables; missing controlled-host performance and executed nightly
still prevent full G5 and performance claims
([execution plan](execution-plan.md), [host policy](decisions/U0023-consumer-driven-delivery-and-validation-readiness.md)).

This refresh reproduces local analytic behavior and preserves inherited evidence scope.
It is not fresh hosted/local same-published-commit validation, a runner/nightly receipt,
a native result, a dependency migration, G2 acceptance or U3 closure.
