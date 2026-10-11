# U2 B — bounded R1/R2 recheck

**READY FOR HUMAN DECISION.** R1 and R2 are resolved at the proposal-interface level in the
exact corrected package identified below. No blocking contradiction was found in this delta
or its direct dependencies. This does not accept the package, change an operative gate,
authorize implementation, or constitute the later fresh U-REVIEW.

Javid selected S for drafting only and remains human decision-maker for both lanes. The
remaining explicit policy choices are retained below and in the prior B report. Runtime
acceptance tests, actual npu-l4 generation/adoption and independent implementation reviews
remain outstanding. Estimate impact: **none**.

## Exact inputs and scope

B worktree: `/home/jjaff/AI-infra-simulation/rk-uarch-u2-b`.
**A/** below means the preserved repository-relative root
`/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-inputs/A-R1-R2-proposal-8def4c6d2c27/`.
**P/** means `A/docs/reviews/U2-U0003-proposal/`; **F/** means `P/fixtures/`.
Schema pointers refer to P/proposed.schema.json.

Verified corrected manifest SHA256
`8def4c6d2c275010719525bc7f39b463675284791122def8c38001889c0ea4d6`
and all **116 payload entries**. Independently verified the preserved parent manifest and
its 81 payloads, manifest SHA256
`59d9d3889e8687128bd0da0a2a39cf25c4a44b9da01e0ed4793c27673d5d24f8`.
The actual delta is **18 changed payloads, 35 additions, 63 unchanged, no removals**.
Every declared old/new hash in changes-from-81-entry.json agrees where supplied. Its summary
counts the manifest as the nineteenth change; its self/current-manifest hash exclusions are
intentional, with the final manifest and externally supplied digest providing the bindings.

The blocking report remains unchanged:
[U2-B-S-revision-check.md](U2-B-S-revision-check.md), SHA256
`20863fb6c5e90753f4c637db672d9c330f95b683048ff4ae10293c25661218a3`.
Also verified unchanged preparation hash
`12c38ea9f9ae6d64ff59b69aab6e5ee4e1e5761414d1a94daba037e0efa58dbf`
and initial compatibility hash
`a4ef227c7ac563d6b02e4197137e30cef773dd8565aa1b14f00c7904a8099fb8`.
Coordinator intake SHA256:
`1030fa31c262314db57cfe5c30441f79c250d910427d6287d303f32b204982e1`.
Attached instruction bytes SHA256:
`f660b4765bce21579577a6c5160bf4a04ebbb7626c4ae25d49669d4ba1529535`.

Read the corrected handoff, correction document, change inventory, current validation record,
new carriers/cases and direct prose/hash dependencies. Used the preserved snapshot, not live
A files. Did not rerun any proposal script; independent checks were inline, read-only and in
memory. The sandbox failed to start because of the /mnt/wslg/distro mount; approved escalated
commands were used without installing dependencies.

## R1 — resolved at proposal level

Precise interface references:

- `#/$defs/ArtifactPointer`, `ExpectedPrecisionRefusal`, `PrecisionCheckInput`,
  `PrecisionCheckTrace`, `PrecisionRefusalObservation`;
- `#/$defs/ReferenceInventory/properties/refusal_inventory_source` and `/refusals`;
- `#/$defs/ComparisonArtifact/properties/precision_refusal_observations`;
- P/R1-R2-corrections.md, the four R1 sections; P/comparison-evidence-export.md,
  “Comparison artifacts”; P/two-track-amendment.md complete-inventory rules;
- F/comparison-inventory.json, comparison-physical.json, r1-input/trace/observation-0..3.json,
  r1-recorded-probe-*.json, r1-semantic-cases.json, r1-outcomes.expected.json and r1-channels.json.

The prior missing observation interface now exists. Expected component obligations bind
stable refusal IDs, the complete source refusal list and unique source indices, component
bindings, explicit precision, callable/boundary and expected error class. Observations bind
input and trace independently of those expectations and retain observed boundary/error,
execution, match result and evidence result. Input records bind the upstream pin and callable
source digest. The source-list and expected-ID joins must be bijective before reduction.
There is no fabricated query, numerical result or successful EngineResult for a component
check. Query A-F12 remains separate.

Independently checked all four source-entry/input/expectation correspondences and their
observations/traces, including the callable digest against pinned compute.py. All four are
explicitly synthetic. The two npu-l4 roles use the bound BF16 synthetic descriptor as a
surrogate and say so; they cannot discharge actual npu-l4 checks or adoption.

The additional historical example is correctly narrower: its input is reconstructed, its
trace is a captured probe, and capture_source selects `/cases/1` of the unchanged loader
record. Error class and message agree exactly. The original probe selected BF16 for the
adapter and then made a direct FP16 peak lookup; the reconstructed FP16/BF16 input explains
that distinction and KV's irrelevance to the direct call. A null refusal_id marks an auxiliary
unexpected event, not an adopted fourth or fifth expected obligation. No fresh loader run is
claimed or performed.

The correction specifies the validation order and keeps malformed evidence outside trusted
reduction: duplicate expectations/source indices, source-list mismatch, duplicate observations,
unknown nonnull IDs, missing observations and input/trace mismatch have named refusals. A
null ID permits only a fully recorded unexpected refusal, not a bypass for an unknown expected
ID. A claimed serialized outcome is untrusted if verification fails; the caller records the
refusal and not_assessed instead of manufacturing a verified artifact result.

I checked the 13 materialized inventory/comparison pairs structurally, verified their hashes
and additional trace bindings, and independently checked each supplied mutation against the
stated join/reduction rules. The resulting diagnoses agree with the declared expectations:

| Materialized case | Evidence/verification result | Physical recording gate |
| --- | --- | --- |
| Four correct refusals | Refused observations; base artifact failed because its matrix comparisons fail | discrepancy_record_complete |
| Wrong boundary | Refused observation, wrong_boundary | discrepancy_record_complete |
| Wrong error class | Refused observation, wrong_error_class | discrepancy_record_complete |
| Unexpected success | Passed execution evidence, unexpected_success; expected-refusal obligation fails | discrepancy_record_complete |
| Execution failure | execution_failed dominates artifact evidence | discrepancy_record_complete |
| Required not_run | Unassessed observation; other base failures still dominate artifact evidence | not_assessed |
| Unexpected auxiliary refusal | Refused evidence, unexpected_refusal | discrepancy_record_complete |
| Missing observation | RefusalObservationMissing; no verified evidence reduction | not_assessed |
| Duplicate observation | DuplicateRefusalObservation; no verified evidence reduction | not_assessed |
| Unknown nonnull observation ID | UnknownExpectedRefusal; no verified evidence reduction | not_assessed |
| Extra expected source entry | RefusalInventoryMismatch; no verified evidence reduction | not_assessed |
| Duplicate expected ID | DuplicateExpectedRefusal; no verified evidence reduction | not_assessed |
| Input/source mismatch | RefusalSourceMismatch; no verified evidence reduction | not_assessed |

The nominal column in the source expectations is explicitly an **isolated obligation** with
all other checks assumed passing. Only the correctly matched refusals satisfy that isolated
obligation; wrong boundary/class, unexpected success/refusal, execution failure and not_run
fail it. The actual materialized base remains physical-discrepancy data with numerical
failures, not a materialized passing nominal run. The six malformed cases are verifier
refusals, not ordinary compatibility_fail artifacts.

The channel rules now remove the earlier failed/unassessed ambiguity. Known reference with
unavailable actual is unassessed evidence and a failed nominal obligation. Known zero needs
actual zero. Null/absent reference retains actual without numeric validation; an unavailable
model-required output cannot hide behind unknown reference. Only a declared nominal omission
may use modelled_absence, normalized to unassessed above channel level. Execution overrides
precede arithmetic. Fixture reduction and then artifact reduction use
execution_failed > failed > refused > unassessed > passed; only all-passed artifact evidence
maps to complete_pass. Refusal matching remains a separate gate predicate.

All five isolated channel payloads validate; known source values resolve. Their stated
zero/unknown/null/absent distinctions agree with the rules. The nominal-omission example is
conditional: it uses a generic matrix_ops channel and does not itself supply a model that
omits matrix work. It must not be treated as evidence that either proposed model may omit
matrix_ops. Implementation acceptance must exercise a genuinely declared vector/decode-write
omission and reject an invented matrix omission. The written rule already requires that
check; this illustrative conditional case is not a contradictory unconditional pass.

A completely recorded failed physical attempt can establish discrepancy recording. Missing
required attempts or not_run cannot. Neither recording completeness nor nominal compatibility
establishes physical accuracy. The remaining zero/null/absence, exact budgets, source checks
and A-F12 scope requirements are preserved.

## R2 — resolved at proposal level

Precise interface references:

- `#/$defs/SourceMetricRecipe` and `#/$defs/MetricDependencies/properties/source_recipes`;
- existing `MetricRecipe` and `DependencySelector` syntax, unchanged;
- P/R1-R2-corrections.md, “R2: exact purposes and source recipe inheritance” and
  “R2: precise fixture/display expectations”; revised companion evidence section;
- F/metric-dependencies.json, dependencies-review.json, r2-reference-assumptions.json,
  r2-actual/reference-count-evidence.json and associated verification/review records,
  r2-semantic-context.json, r2-contributors.expected.json and r2-semantic-cases.json.

The four overbroad wildcard recipes are replaced by exact bound comparison/channel paths.
Independently enumerated all nonnull ratios on the executed sample fixtures: **30 recipes,
22 counts and 8 duration**. Their channel indices agree with the actual bound channel names,
including signed/absolute adjustment bookkeeping zeros. No count-purpose recipe covers a
duration ratio. The pre-call-refusal fixture has no promised numeric display recipes; the
existing missing-recipe policy applies to it as to other unlisted fields.

Each ratio selects its exact ProducedValue source, its corresponding inventory reference
value and its own declared_deviations. Verified those source pairs against the comparison,
not merely against arbitrary resolvable JSON paths. The ps-to-seconds conversion remains
explicit and does not change contributors or purpose.

A result_field now necessarily traverses a uniquely keyed source recipe. The correction
specifies recursive inheritance, matching purpose, identity-specific model evidence and
scope, required computation inputs, cycle rejection and no value-only fallback. Other
selector kinds terminate at their declared original inputs/evidence; a hash-shaped value is
not an implicit dependency. The primary context model cannot substitute for the reference
model. A reviewed recipe cannot waive a required computation dependency.

Independently checked **20 source recipes, 60 purpose-matched result_field edges and 261
resolvable selectors**. All source recipe model identities match their model_evidence leaves.
Expanding the matrix-ratio dependencies reaches two distinct source models and no unused
timing hardware. Expanding duration reaches both source models and six hardware selectors:
core rows/cols/frequency, matrix and vector rates, and DRAM bandwidth. The bandwidth leaf is
an actual `kind: claim, provenance: stub` input; expansion preserves it.

The sample reference is explicitly a hand-authored synthetic literal with its own assumptions
and model identity, not a frozen oracle execution. Rules for later frozen data require the
original nominal model/query/precision/tp and component/model inputs, including efficiency .55
and source fingerprint. Those future data recipes must satisfy the same completeness rule;
the literal fixture does not claim to have exercised them.

Empty adjustment lists introduce no phantom claim. Nonempty unvalidated deviations remain
stub model assumptions. All four sample ratio types use the conservative full source union,
so a bookkeeping zero cannot promote a timing metric. Source bands are not synthesized into
a ratio confidence interval; absent separately applicable supplied ratio evidence, its band
remains unknown.

The dedicated context binds separate actual/reference **matrix-count-only**, no-band,
synthetic L3 evidence and verification records. The explicitly injected scope-MATCH premises
are synthetic test inputs, not findings about the analytic bundle's null mapping. Under those
premises, the .184 matrix ratio can be estimated while the zero duration ratio remains stub:
there is no duration evidence and a genuine stub hardware leaf survives. Without the injected
MATCH premise the original analytic scope stays stub. Even adding eligible timing evidence
would not erase the retained stub claim. These are justified expected evaluator outcomes,
not executed eligibility/renderer results or actual silicon evidence.

Materialized all seven R2 mutations in memory, rehashed synthetic review/dependency bodies
where directed, validated structure and independently checked their concrete defects:

| Mutation | Observed review/topology/dependency diagnosis |
| --- | --- |
| Missing duration source recipe | MissingSourceMetricRecipe |
| Source recipe selects itself | CyclicMetricRecipe |
| Duplicate source target | AmbiguousSourceMetricRecipe |
| Duration source purpose changed to counts | MetricPurposeMismatch |
| Timing selector removed with old review retained | ReviewSubjectMismatch |
| Timing bandwidth removed despite a rebound synthetic review | IncompleteMetricContributors |
| Reference model selector removed | IncompleteMetricContributors |

These diagnoses check the proposal's expected refusals; no future runtime verifier or renderer
was executed. In particular, a newly hashed or reviewed body cannot cure an omitted required
hardware/model input. The positive dependency requirements are substantiated by the already
declared computation rules, not merely by trusting the review string.

Raw actual/reference magnitudes remain stored and loader-accessible. Internal source recipes
are explicitly not display recipes. Verified that sample raw-magnitude display recipes are
absent; the correction explicitly keeps those values hidden even with opt-in and returns
MissingMetricRecipe for direct numeric rendering. That policy covers labels, numeric warnings,
SVG geometry/axes/tooltips/data attributes/accessibility and other numeric surfaces. It does
not erase data to hide it. Actual all-surface rendering enforcement remains a required test.

## Direct dependencies and unchanged choices

The schema adds exactly six definitions: ArtifactPointer, ExpectedPrecisionRefusal,
PrecisionCheckInput, PrecisionCheckTrace, PrecisionRefusalObservation and SourceMetricRecipe.
Only three existing definitions change: ReferenceInventory, ComparisonArtifact and
MetricDependencies. No parallel private B schema is needed. A's existing comparison.py owns
the refusal carriers; report_context.py owns SourceMetricRecipe. Delivery names the added
standalone schema roots and leaves B's comparison/evidence tests with B.

All **63 catalog payloads** validate against the 132-definition schema. Independently checked
**62 self hashes and eight reviewed-body bindings**. Review-body exclusion rules still avoid
self-reference while final hashes bind the review. Updated comparison/dependency identities
propagate through report context, table and both render specifications. The render fixtures
change only table/context/render hashes; their display flags and formatting policy do not change.

Byte-compared 19 specified policy/historical-evidence files against the parent, including
U0003 ADR, public patch/index, interfaces, accounting, precision matrix, physical conventions,
prepared bundle, export bindings/model input, nominal literals and prior check records. No
unintended policy delta was found. Changed amendment/delivery prose adds R1/R2 obligations
inside the existing scope. Public patch/index are unchanged; no patch was applied and no
new prompt-sync or loader result is implied by retaining their older records. Final integrated
public-document hashes still belong to the coordinator's later integration step.

The complete human-choice list in the prior report's “Public amendments, ownership and
remaining human decisions” section remains in force. For the coordinator, it covers:

1. Exact S replacement gate subjects and null/absent policy, preserving count/duration limits
   and stating the lost physical full-workload accuracy claim.
2. Exact shared versions/carriers, export truth/projection/loss rules and execution-model
   assumptions, including separately proposed efficiency1.0. Real npu-l4 input and artifact
   acceptance remain concrete later steps.
3. The narrow selected-rank/U0019 extension and explicit synthetic assignment, or corresponding
   unequal-hit refusals and revised completion scope.
4. Individual physical D6 conventions and D12 capability limits.
5. Default-hidden STUB with labelled opt-in, or deliberate alternate display policy with
   revised exact bytes. This package retains the recommended hidden default.
6. The 1008-success/four-refusal baseline, separate optional BF16/FP8 addition, ownership and
   conditional estimates; explicit U3 G2(c) subject and U0021 check-scope amendments.

R1/R2 changes do not accept any of these choices. Count budgets remain <=5% absolute spend
and <=0.5% residual; nominal duration remains +/-0.1%; exact zeros, A-F12 and the human
artifact lifecycle remain. Accepted U0021 hosts/publication identity are not reopened.

**Estimate impact: none.** A140–222 + B100–154 + fresh independent reviewers16–24 remains
**256–400 engineering person-hours**. Human active2–4 provisional hours/waits and previously
separate U3/U4 costs are not folded into that estimate. This is not a calendar commitment.

## Verification limits and handoff

Executed here: manifest/delta checks, schema/self-hash/review-body checks, exact input/trace/
source correspondences, bounded in-memory R1 reduction checks, channel-source checks,
recursive R2 dependency inspection, seven mutation diagnoses and outer hash propagation.
These go beyond checking schema acceptance but are still proposal review probes, not product
implementation or a run of the future comparator/evidence evaluator.

Required implementation checks include source/trace tampering and malformed joins, reductions
across complete real inventories, actual declared omissions versus invented omissions,
isolated nominal candidate access traps, complete physical replay/discrepancies, recursive
missing/duplicate/indirect-cycle/purpose/contributor refusals, real evidence applicability,
review/ordering checks, raw-magnitude nonleakage under opt-in, renderer determinism and actual
npu-l4 bridge/generation/adoption. Later fresh independent implementation review remains
required. Their current absence does not block a coherent proposal decision.

No full suite, loader, prompt-sync, nominal candidate, physical engine, oracle generation or
renderer was run. Older validation.json, loader-probe-results.json and prompt-sync-results.txt
remain historical evidence; r1-r2-validation.json was inspected, not relabelled as B's run.
Only this report was written, uncommitted. Earlier B reports and both preserved snapshots remain
unchanged. No public patch, runtime/contract/vendor/hardware edit, artifact adoption, dependency
installation, UARCH_HUMAN, agent, commit/push/tag, main transfer or worktree cleanup occurred.
