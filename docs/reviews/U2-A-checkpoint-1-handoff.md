> **A1-C1/C2 correction update:** the corrected checkpoint is pending coordinator recheck.
> [Correction handoff](U2-A-checkpoint-1-corrections/handoff.md) contains both dispositions,
> observed coordinator-probe refusals, 538 passes/four A2 skips, and the old/new SHA256 delta.
> Public signatures and schema bytes are unchanged. The original A1 record below and its
> earlier logs describe the preserved `bff5aa5743ab` checkpoint; they are not new test results.

# U2 A1 — executable shared contract checkpoint

For Javid to transfer to the coordinator/B. Uncommitted A1 implementation for review;
this is not A2 execution, physical parity, evidence promotion, rendering, or sprint closure.
The accepted S direction, thresholds, matrix, D1–D12 and R1/R2 remain the governing choices.

## Base, immutable inputs and complete file identities

Worktree `/home/jjaff/AI-infra-simulation/rk-uarch-u2-a`, branch `u2/analytic`.
Base and current HEAD: `1e9e794a84c5173812c23a1cf2fc04b85e6f6831` (peeled `u01-end`).
No commit, tag, push, dependency installation, agent, vendor adoption/generation command,
public-document overlay, hardware/report implementation or other-worktree edit was performed.

- Common baseline: 262 entries verified; manifest
  `8ce7b0d6ee152df698543d5be98dc2f2733533a7ed679bcbfa53335303e8370e`.
- Embedded accepted proposal and local original: all 116 manifest entries verified;
  original manifest `8def4c6d2c275010719525bc7f39b463675284791122def8c38001889c0ea4d6`.
- The local proposal, original ADR and previous handoff/evidence remain byte-identical.
  Entry-state fingerprints and final verification are in
  [entry-state.json](U2-A-checkpoint-1/entry-state.json) and
  [immutable-verification.json](U2-A-checkpoint-1/immutable-verification.json).
- Generic `hardware.py`, `sourced.py`, `operators.py`, `precision.py`, `model_shape.py`,
  `model_card.py` and `fidelity.py` remain byte-identical to HEAD.
- [SHA256SUMS](U2-A-checkpoint-1/SHA256SUMS) covers **every modified/untracked file relative
  to HEAD**, including this handoff and the preserved pre-existing proposal. As usual,
  it excludes itself; its detached digest is returned with the handoff. No deleted paths.
- [changed-paths.json](U2-A-checkpoint-1/changed-paths.json) records base SHA256 for modified
  tracked paths and separates preserved pre-existing untracked inputs from A1 changes.
  [checkpoint-paths.txt](U2-A-checkpoint-1/checkpoint-paths.txt) is the proposed **A1-only**
  checkpoint file list, not an instruction to stage the pre-existing proposal.

The common accepted documents govern. Historical PROPOSED labels and captured identities
inside the preserved proposal/fixtures were not rewritten.

## Delivered authority and import surface

Static Pydantic Python classes are the maintained authority; no production code reads the
proposal schema or uses a second runtime schema implementation. Generated mirrors come from
`uarch_contract.generate` and `rkuarch.engines.protocol.schemas/generate`.

[api-and-field-map.json](U2-A-checkpoint-1/api-and-field-map.json) records exact import paths,
callable signatures, fields, required sets and schema paths. All 125 corresponding model roots
have exactly the accepted field names and required-field sets. Inline closed objects have
ordinary Python helper names; JSON wire fields remain unchanged. `Query` is the discriminated
`DecodeQuery | PrefillQuery` alias. Required nullable values remain explicit nulls.

| Authority | Shared roots / entry points |
| --- | --- |
| `uarch_contract.request` | `RequestIntent`, current `CharacterizationRequest` (0.2); explicit `LegacyCharacterizationRequest` (0.1) |
| `uarch_contract.prepared` | `Producer`, `RankScope`, `Query`, `Padding`, `Replication`, `KvAccess`, `PreparedOp`, `OpGroup`, `PreparedGraph`, `PreparedPoint`, `PreparedBundle`; `validate_prepared_op`, `validate_prepared_bundle` |
| `uarch_contract.table` | Current `Row`, `DecodeRow`, `PrefillRow`, `Interpolation`, `UarchCostTable`; `ReportScope`, `OpResult`, `ArtifactBindings`; `validate_table_bindings`; explicit historical inspectors |
| `uarch_contract.derivation`, `.assumptions` | `DerivedParameter`, `Derivation`, `ModelIdentity`, `AssumptionSet` |
| `uarch_contract.exports` | `ComponentExport`, `ExportBinding`, `UpstreamComponentBinding`, `ExecutionModelInput`, `ComponentPrecision`, `ExplicitPrecision`, `ProjectionLoss`, `FiveFieldValue` |
| `uarch_contract.comparison` | `ComparisonArtifact`, `ReferenceInventory`, channels/values/fixtures, expected refusals and input/trace/observation carriers; `validate_channel`, `reduce_outcomes`, `validate_precision_observations`, `validate_comparison` |
| `uarch_contract.evidence`, `.registry` | `EvidenceRecord`, `SourceRecord`, `ReviewRecord`, `OrderingRecord`, `VerificationRecord`, typed scopes and pointers; `FamilyRegistry` |
| `uarch_contract.report_context` | `ReportContext`, `MetricDependencies`, `MetricRecipe`, `SourceMetricRecipe`, `DependencySelector`, `RenderSpec`; `validate_metric_dependencies`, `validate_report_context` |
| `uarch_contract.hashing` | Canonical/strict JSON; content, request, point, bundle, execution and legacy hashes; self identity, review subject, artifact/pointer resolution and declared transitive identity closure |
| `rkuarch.engines.protocol` | Sole definitions of `EngineIdentity`, `ResolvedHardware`, `EngineJob`, `EngineResult`; `validate_engine_job`, `validate_engine_result`, schema generation/freshness |

There are **129 contract schema roots plus four protocol roots**, listed exactly in
[schema-audit.json](U2-A-checkpoint-1/schema-audit.json). Six explicitly named Legacy roots
preserve historical inspection. `NominalInput`, `NominalOutput` and `NominalCounts` remain
scheduled for the isolated A2 test-only candidate; no nominal production engine selector exists.
An analytic EngineIdentity carrying the nominal model is explicitly refused.

Parsing a carrier does **not** confer verified closure. Consumers must call the relevant
verification functions with their complete offline hash-to-artifact mapping. These functions
never prepare work, execute candidates, fetch sources or render output. Identity closure alone
also does not confer provenance eligibility, physical correctness or permission to display.

## Semantic coverage and remaining owners

| Boundary | Implemented in A1 | Remaining accepted owner/work |
| --- | --- | --- |
| Structural contract | Closed fields, finite numeric carriers, numeric bool/string refusals, current-version literals, required nulls, reference/produced states, uniqueness, retained U1 table constraints | Generic pinned sourced/hardware/precision/card semantics unchanged |
| Identities | Canonical exclusions; nested point/bundle identities; explicit JSON duplicate-key refusal; content/review-subject verification; offline pointers; declared companion closure and raw-blob hashes; request/job/table/result bindings | A2 filesystem loader, raw source acquisition/capture adapters and complete execution/report readiness orchestration |
| Prepared input | Inner/outer hashes, original spec hash, supported precision, rank/hit conservation/equivalence, declared padding/replication, ordered DAG edges, operator operand axes/access/reductions, fusion, KV page accounting, exact grid/state/frequency coverage, layer/expert multipliers and omissions | A2 full global-to-rank projection extent checks, imported unfused triplet correspondence, full MoE/storage/residency/capability checks and D12 refusal integration before execution |
| Protocol/table | Physical-only engine identity; job duplicate-input joins; captured counts conservation, per-op bound/duration, aggregate/per-op reduction and attribution; unknown analytic busy time/diagnostics; row conversion and ordered execution identity | A2 compute original physical work, derive/check every resolved hardware number, roofline algorithms, complete residency, model-card/condition/provenance agreement and producer-disabled runtime replay |
| R1 | Stable expected-ID/source-index bijection, primary named join refusals, input/binding/upstream/source-list and observed trace correspondence; extra-refusal rules; numerical/zero/null/absence policies; evidence severity; separate nominal and physical-record gates; exact captured source/query/precision/rank/model joins | B invokes and captures actual checks, assembles inventory/comparisons, verifies source/execution authenticity and runs adopted nominal compatibility; A2 supplies isolated nominal candidate and captured physical adapter |
| R2 | Reviewed body includes source recipes; unique source target, missing/cyclic/purpose refusal, original terminal union, independent source-model binding, declared physical timing contributor requirements, exact comparison channel-index/purpose and actual-source joins | A2 runtime verifies complete contributors against actual derivation/computation; B evaluates each source model's purpose/granularity/full scope, claims/conditions, error bands and display permission |
| Evidence/export/registry | Complete accepted carriers; source/review identity helpers, family uniqueness, explicit precision pairs/bindings and execution-model shape; no implicit family or model substitution | A2 export/derivation/descriptor source and byte agreement; B evidence independence/order/rung/applicability, registry review eligibility, badges and rendering |

These remaining checks are mandatory before A2 import/execution or an actual U-P4 report.
The A1 entry points are not advertised as a complete execution-ready or report-ready loader.
`validate_metric_dependencies` returns terminal selectors for top-level recipes; source recipes
never become display recipes. B must retain their source-model/scope requirements when applying
eligibility. `validate_report_context` supplies the exact comparison-index/channel-purpose join.

R1 is implemented as captured-record verification: all 13 preserved semantic cases execute,
including four matches, wrong boundary/class, unexpected success/refusal, execution failure,
not-run, missing/duplicate/unknown IDs, source mismatch and inventory defects. Matching expected
refusals retain refused evidence. A required not-run cannot produce a complete physical record.
Separate checks exercise isolated nominal refusal obligations and the full evidence severity
order. Numerical failures remain serializable; invalid adjustment policy refuses verification.

R2's seven preserved discriminators execute with their exact expected refusals, including a
re-reviewed missing bandwidth contributor. An additional re-reviewed wrong-purpose case binds
the actual duration channel index. The synthetic count and timing recipes retain separate models;
timing retains original bandwidth, while count recipes do not inherit timing hardware. No test
claims that B's eligible L3 badge or report rendering has run.

## Tests-first evidence and final checks

The independently authored seven fixture files were copied byte-for-byte into the authorized
`contract/tests/fixtures/u2` paths before production carriers existed. Initial tests failed on
missing modules/APIs, as recorded in [tests-first.txt](U2-A-checkpoint-1/tests-first.txt),
[semantic-tests-first.txt](U2-A-checkpoint-1/semantic-tests-first.txt) and
[boundary-tests-first.txt](U2-A-checkpoint-1/boundary-tests-first.txt).
[pre-schema-generation.txt](U2-A-checkpoint-1/pre-schema-generation.txt) records 109 passing
cases, four deferred cases and the expected freshness failure before mirror generation.
Expectations were not computed by a producer, analytic engine or nominal candidate.

Final exact commands, Python/environment, exit codes and log paths are recorded in
[check-results.json](U2-A-checkpoint-1/check-results.json). They include:

- Full contract suite plus relevant prompt/third-party and A artifact tests: **502 passed,
  four skipped**. The four skips are the two nominal input and two nominal output literals
  reserved for A2, not waived production validation failures.
- Strict mypy across the configured source/contract scope: 38 files, pass.
- Ruff across `src`, `contract` and the A artifact tests: pass.
- Exact contract and protocol schema freshness: pass; `git diff --check`: pass.
- Independent system Draft 2020-12 validation: all 133 schema roots and 59 accepted typed
  fixtures pass. The existing system jsonschema installation was used; nothing was installed.
- Exact accepted fields/required sets and immutable input/generic-source fingerprints: pass.

The independent decode result asserts 1184 matrix ops, 572 vector ops, 1296 read bytes,
288 write bytes, 31 represented invocations and 1,892,000 ps. These are captured literal
carrier/arithmetic checks, not a producer run or physical-reference parity measurement.
The original 0.1 toy fixture and all vendor/reference bytes remain unchanged.

## Deviations and review boundary

No new gate, threshold, matrix selection, field/default policy, model owner or public-document
amendment is proposed. Existing estimate ranges remain unchanged; no elapsed engineering-hour
claim is made.

A narrow path expansion was necessary for existing regressions: five historical test files
(`test_u_p1.py`, `test_u_p1_followup.py`, `test_u_p1_review.py`, `test_projection_scope.py`,
`test_vendored_round_trip.py`) now explicitly use Legacy inspectors/hash helpers. U1 model
coverage is pinned separately from the new U2 fixture catalog, and its unit scan recognizes
the accepted per-byte rates. The first full run exposed 52 old-name migration failures; their
logs are retained. No historical payload was upgraded or parity tooling algorithm changed.
This test-only migration is called out for coordinator review against the original new-path list.

Remaining semantic coverage is stated above rather than inferred from successful schema parsing.
No additional human decision on shared field semantics is currently requested. Coordinator review
of this exact A1 package precedes A2; no runtime producer/engine/CLI work has started.

Proposed local checkpoint commit message (not executed):

```text
Implement accepted U2 A1 shared carriers and captured-artifact validation

Add accepted 0.2 request/prepared/table, derivation, export, comparison,
evidence, report-context, registry and assumption types with a single
engine protocol authority and generated standalone schemas.

Preserve explicit 0.1 inspection and migrate historical test references
without changing their fixtures. Verify canonical and transitive identities,
prepared graph boundaries, captured job/result/table arithmetic, R1 refusal
joins and separate reductions, and R2 reviewed source-recipe closure.

Add independent literal and semantic-negative tests, field/API mapping,
schema inventory, immutable input verification and the A1 handoff manifest.
Keep physical production/replay, isolated nominal execution and B evidence
eligibility/rendering at their accepted later boundaries.

Validation: 502 tests passed, 4 A2 nominal cases explicitly skipped;
mypy, ruff, schema freshness, independent schema audit and diff checks pass.
```
