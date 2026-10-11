# Phase 2 delivery proposal

Status PROPOSED, conditional on the coordinator identifying accepted U0003 bytes and Javid
resolving D1–D12. No runtime/public contract edits are authorized by this package.

## Exact ownership and public changes

A41/B35 are historical hours, not commitments. CODEOWNERS remains authoritative; Javid
acts as human reviewer for both lanes without asserting Reza approval. Contract changes
are drafted by the assigned author and accepted/integrated by the coordinator under that
human authority. No whole-directory overlay is proposed.

| Owner | Exact proposed paths / changes |
| --- | --- |
| A, human contract acceptance | contract/uarch_contract/prepared.py (new envelope/intent/graph); request.py (0.2 binding); table.py (0.2 row/report fields and interpolation none); derivation.py (new); hashing.py (new identity functions); common.py (version); errors.py (named refusals); __init__.py and generate.py (exports/freshness). operators.py, hardware.py, sourced.py, precision.py, model_shape.py, model_card.py generic semantics remain unchanged; new report-context evidence closure is explicit below. |
| A, schema generation after acceptance | contract/schema/CharacterizationRequest.json, Row.json, DecodeRow.json, PrefillRow.json, Interpolation.json, UarchCostTable.json change. New contract/schema/RequestIntent.json, Producer.json, RankScope.json, Query.json, Padding.json, Replication.json, KvAccess.json, PreparedOp.json, OpGroup.json, PreparedGraph.json, PreparedPoint.json, PreparedBundle.json, DerivedParameter.json, Derivation.json, ReportScope.json, OpResult.json, ArtifactBindings.json. Nested schema definitions of these roots must remain synchronized; exact generated inventory reviewed before acceptance of implementation. |
| A protocol | src/rkuarch/engines/protocol.py; src/rkuarch/engines/schema/EngineJob.json, EngineResult.json, EngineIdentity.json, ResolvedHardware.json (new). Import shared contract types; no second definitions. |
| A runtime | src/rkuarch/hw/derive.py, export.py; src/rkuarch/workload/prepare.py, prepared.py, identity.py, characterize.py, deviations.py; src/rkuarch/engines/analytic/core.py, __main__.py; src/rkuarch/table/build.py, time_units.py, artifacts.py; src/rkuarch/cli.py. Existing package __init__.py files only for needed exports. No mapping/, fork/, native/ or third_party/ work. |
| A tests | tests/unit/test_u2_a_derivation.py, test_u2_a_shapes.py, test_u2_a_prepared.py, test_u2_a_analytic.py, test_u2_a_artifacts.py; tests/integration/test_u2_a_replay.py; contract/tests/test_u2_prepared_contract.py, test_u2_schema_freshness.py; contract/tests/u2_prepared_adapter.py and test_u2_physical_discrepancies.py (actual A adapter and its independent tests). |
| A contract fixture proposals | contract/tests/fixtures/u2/independent-bundle.json, request.json, engine-job.json, engine-result.json, toy-table.json, negative-cases.json, expected.json. The U1 toy fixture remains historical 0.1. Independent expected fixture authorship must precede producer code; B may submit counterexamples under B-specific filenames. |
| B hardware | hw/designs/npu-l4.yaml, hw/designs/npu-m256.yaml, hw/references/tpu-v5e.yaml, hw/references/blackhole-p100a.yaml; hw/U2-sourcing-inventory.md. A supplies formulas/consumption checks, never parallel duplicate spec edits. |
| B evidence/report | src/rkuarch/provenance/badge.py, model_card.py, applicability.py; src/rkuarch/report/render.py, badged.py, templates/report.html.j2, templates/report.md.j2; tests/unit/test_u2_b_badges.py, test_u2_b_report.py, test_u2_b_applicability.py; tests/fixtures/u2_b/ (B proposes exact independently authored evidence fixture filenames with its handoff). B owns U0004 proposal/acceptance path. |
| B vendor/parity, human artifact acceptance | scripts/vendor_rk.py; contract/tests/parity.py, vendor_support.py, test_u2_precision_matrix.py, test_u2_parity_channels.py; contract/tests/fixtures/u2_b/component-precisions.json; contract/vendor/ entire replacement revision only through approved human lifecycle. B consumes the A-owned shared ComponentPrecision binding; B owns matrix selections and tests, not a competing type. |
| Coordinator shared hunks | Makefile generation/check targets; .github/workflows/ci.yml (B proposes CI hunk); docs/build-spec.md §§2.3–2.6/5/6/7/8 U-P3/U-P4; docs/prompts/U-P3-hardware-workload-and-the-analytic-engine.md and U-P4-the-honesty-layer-and-report.md; contract/README.md; src/rkuarch/engines/README.md; workload/README.md; table/README.md; docs/execution-plan.md and how-it-works.md. No dependency change proposed. |

| A shared carriers | contract/uarch_contract/comparison.py (ComparisonArtifact, ReferenceInventory, statuses); evidence.py (EvidenceRecord, SourceRecord, ReviewRecord, OrderingRecord, VerificationRecord); report_context.py (ReportContext, MetricDependencies, DependencySelector, MetricRecipe, RenderSpec); registry.py (FamilyRegistry); exports.py (ComponentExport, ExportBinding, UpstreamComponentBinding, ExecutionModelInput, ComponentPrecision); assumptions.py (ModelIdentity, AssumptionSet). A extends table/artifacts.py::load_verified_report_inputs for complete offline closure. B reviews exact fields before human baseline acceptance. |
| A schema mirrors | contract/schema/{ComparisonArtifact,ReferenceInventory,EvidenceRecord,SourceRecord,ReviewRecord,OrderingRecord,VerificationRecord,ReportContext,MetricDependencies,FamilyRegistry,RenderSpec,ComponentExport,ExportBinding,UpstreamComponentBinding,ExecutionModelInput,ComponentPrecision,AssumptionSet,ModelIdentity}.json; nested definitions generated from shared carriers. No private B ledger schema. |
| A additional test-only model | contract/tests/nominal_candidate.py; contract/tests/test_u2_nominal_candidate.py; contract/tests/fixtures/u2/nominal-input.expected.json. NominalInput/Output carriers and generated schemas live under contract/tests/fixtures/u2/, not selectable production engine types. No src import permitted. |
| B two-track tooling | contract/tests/u2_comparison.py; test_u2_nominal_compatibility.py; test_u2_comparison_inventory.py; test_u2_physical_discrepancy_reporting.py. B preserves failures/null/absence/refusals, invokes A's isolated nominal candidate and actual captured-bundle adapter, and binds complete comparison records. Existing parity.py changes are shared review hunks under B authorship. |
| B evidence fixtures/tests | tests/fixtures/u2_b/evidence-no-band.json, evidence-scope-cases.json, family-registry.json, metric-dependencies.json, report-context.json, render-default.json, render-opt-in.json; test_u2_b_evidence_closure.py and test_u2_b_display_permissions.py. Independent B cases supplement, never overwrite A's fixtures. |
| Coordinator amendment integration | public-amendments.patch is review-only: U-P3/U-P4/U-P5 and build-spec copies, execution-plan U2/G2(c), workload/engine/contract/table/provenance/report READMEs, docs/how-it-works.md, additive U0001/U0002/U0019/U0021 scope records. No historical authorization rewrite. U0021 host remains settled. |

No CLAUDE.md, CODEOWNERS, production or public contract edits occur in this turn. Exact path
partition and generated root inventory must be accepted before coding. Public command changes
are prepare/replay, explicit rk-component truth/projection and execution-model input, offline
artifact resolution, characterize and explicit report opt-in; no production nominal selector.
No dependency installation or change is proposed. Existing human/codeowner authority remains.

## Acceptance sequencing and tests

1. Javid accepts exact shared package bytes and each consequential decision listed in the
   handoff. B checks the revised shared interfaces before coordinator freeze; no unspecified
   field decisions are deferred to private implementation. Initial S selection is not acceptance.
2. Write independent physical expectations, nominal literals/isolation mutants and evidence/
   export/display/refusal tests first. A implements the physical producer/engine/artifact loader
   and separate test candidate; B implements badges/renderer and comparison tooling against
   those exact carriers. Preserve independent prepared import and disabled-producer replay.
3. Run all independent physical shape/count/timing tests and full captured-bundle discrepancies.
   Run nominal comparison over every adopted fixture, with unchanged thresholds. Exact test
   scope/old-new gate deltas are in two-track-amendment.md, not a promised physical parity pass.
4. B stages the full generator/matrix/PARAMS inventory and commands. Javid alone generates
   twice from reviewed identical frozen inputs, then separately reviews/adopts the complete
   artifact revision. Include all retained/new bytes, metadata, source/oracle fingerprints,
   sidecars, counts/durations/nulls/refusals. Actual npu-l4 absent now: B-F16 remains open.
5. Author tests/static/schema/prompt checks, integrated table/report/characterize and two fresh
   independent Stage1 → author Stage2 → original reviewer Stage3 loops. After separate
   publication authorization, validate fresh GitHub WSL2 clone and hosted Ubuntu CI at the
   exact same published commit, recording all commands/environments/no-op jobs. No publication,
   generation, adoption, commit or agent reviews are performed by this proposal turn.

The matrix preserves 864 retained successes (placeholder two pairs, H100 four), plus npu-l4
BF16/BF16 144 =1008. Refusals: placeholder BF16/BF16 and FP8/FP8, npu-l4 FP16/FP16 and FP8/FP8,
all direct peak UnsupportedPrecision in generator; private adapter wraps missing selected
peaks as EngineError. Optional npu-l4 BF16/FP8 +144 needs explicit storage declaration and
acceptance. Unknown format is ValidationError; chip KV support is an extra bridge check.
Require explicit unique pairs, upstream-only vs uarch projection bindings, no fake spec hash,
no filename FP16 fallback and no expected-duration computation by A or B.

Actual-bundle adapter selects a captured fixture point by exact query/model/shape/precision/tp
and component identity, verifies hashes, then invokes the same analytic boundary as table.
A-F12 runs before that call. It never prepares a replacement or returns frozen rank_counts.
Imported authoritative work cannot be changed to match a reference. Candidate nominal
function receives only NominalInput and cannot read expected artifacts; B owns reference
selection and record assembly outside that isolated boundary. Discrepancy records and all
unavailable channels bind reports even when nominal compatibility succeeds.

## Revised person-hour estimate, not elapsed schedule

A's original 104–164 included author integration/review responses. B's latest consolidated
90–138 replaces overlapping 82–120 and 90–142 estimates; **do not add those historical ranges**.
C2–C5 B closure work is already included in B90–138. New S work is charged explicitly below.
No independent full physical reference project is hidden in these estimates.

| Package | A hours | B hours | Included once |
| --- | ---: | ---: | --- |
| Existing U2 scope | 104–164 | 90–138 | Original A scope plus B's seven consolidated work packages below |
| Additional shared carriers/verified closure | 8–12 | 0 | A implementation/test-support interfaces; B closure already in base |
| S nominal candidate implementation | 8–14 | 0 | Test-only input/output/isolation; no production engine |
| S independent nominal tests and mutants | 10–16 | 0 | Literal algebra, parameter perturbations, expected-access traps |
| S physical complete-discrepancy adapter and rank scope | 6–10 | 0 | Captured/imported cases, conservation, capability coverage |
| S comparison/report integration | 4–6 | 10–16 | A integration; B inventory/reductions/two-track report tests |
| **Revised author totals** | **140–222** | **100–154** | **240–376 author hours** |
| Fresh independent reviewers |  | **16–24 total** | Two fresh review loops, including S model/source isolation and amendment consistency; separate from author fixes |
| **Engineering incl. fresh review** |  | **256–400 total** | Conditional planning range, no delivery commitment |
| Javid active decisions/generation/adoption |  | **2–4 provisional** | Not engineering effort; elapsed human waits unknown |

B90–138 breakdown retained exactly: preparation/shared decisions10–16; badges/applicability/
report/evidence24–34; hardware12–20; matrix/export/parity12–18; independent B tests12–18;
artifact staging6–10; integration/review responses/U0021 support14–22. Historical planning
hours are not claimed actual elapsed work. Integration support does not count fresh reviewer
labor. Re-estimate after accepted exact scope and actual hardware/source inventory.

Critical serial dependencies: package acceptance → implementation/tests → frozen tooling/input
review → Javid's two generation runs → whole-artifact adoption → integrated review/fixes →
publication and same-commit U0021 checks. Human wait has no bounded calendar estimate.
H has no credible completion estimate with existing conflicts; R acquisition/validation is
unbounded and excluded. U3 proposed G2(c) change adds indicative A6–10/B4–6 hours for independent
fork same-work expectations, separate from U2; no fork work here. Previously estimated U4
mapped replay impact remains A+20–32/B+8–14, separately scoped at U4.

## Checks in this drafting turn

See validation.json and loader-probe-results.json for actually executed checks. Structural
proposal schema/hash/arithmetic audits and full synthetic loader selection are not runtime
replay, nominal comparison, real npu-l4 evidence or badge/display implementation tests.
All future runtime tests listed above remain planned. No full runtime suite is warranted
for a proposal-only change; the unchanged prompt-sync check is run. Review fixtures and
scripts live only under docs/reviews and remain uncommitted.

## R1/R2 correction within the existing estimate

A’s comparison.py also owns ExpectedPrecisionRefusal, PrecisionCheckInput, PrecisionCheckTrace
and PrecisionRefusalObservation; report_context.py owns SourceMetricRecipe within the existing
MetricDependencies carrier. Their standalone generated roots, when emitted, are
contract/schema/{PrecisionCheckInput,PrecisionCheckTrace,PrecisionRefusalObservation}.json.
B’s already named inventory/comparison/evidence tests cover R1-R2-corrections.md’s exact cases.
No new owner, model, dependency, phase or hours: A140–222/B100–154 plus review16–24 unchanged.
