# R1/R2 narrow correction — proposal only

Input B report: 20863fb6c5e90753f4c637db672d9c330f95b683048ff4ae10293c25661218a3.
Parent is the preserved 81-entry S package, manifest
59d9d3889e8687128bd0da0a2a39cf25c4a44b9da01e0ed4793c27673d5d24f8.
S, numerical thresholds, nominal inputs, 1008/four matrix, physical conventions, rank policy,
display choice and estimates are unchanged. These are corrections inside already estimated
comparison/evidence work. No model, semantic comparator or renderer is implemented here.

| Finding | Disposition | Exact schema and rules | Discriminators |
| --- | --- | --- | --- |
| R1 | Addressed as a proposed interface; pending B recheck | `$defs/ExpectedPrecisionRefusal`, `PrecisionCheckInput`, `PrecisionCheckTrace`, `PrecisionRefusalObservation`; `ReferenceInventory.refusal_inventory_source/refusals`; `ComparisonArtifact.precision_refusal_observations`. Stable ID join, source correspondence, complete reductions below. | Four nonempty expected/observed pairs in comparison-inventory/physical.json; r1-input/trace/observation-0..3.json; r1-recorded-probe-*; r1-outcomes.expected.json, r1-semantic-cases.json, r1-channels.json. |
| R2 | Addressed as a proposed interface; pending B recheck | `$defs/MetricDependencies.source_recipes` and `SourceMetricRecipe`; existing MetricRecipe/DependencySelector syntax unchanged. Exact channel-index paths, purpose preservation, recursive source-recipe inheritance below. | metric-dependencies.json; r2-reference-assumptions.json; r2-*-count-evidence/verification/review.json; r2-semantic-context.json; r2-contributors.expected.json; exact r2-semantic-cases.json mutations. |

## R1: stable component-level correspondence

`ReferenceInventory.refusal_inventory_source` is an ArtifactPointer to the complete approved
matrix refusal list (content hash plus JSON Pointer). Each `ExpectedPrecisionRefusal` has a
unique nonblank refusal_id, exact component_binding_hash, explicit precision, requested
boundary/error_class, check_input_hash and source_entry_index. Source index identifies exactly
one frozen source entry; compare component role, precision, boundary and class through the
bound PrecisionCheckInput. Coverage must be bijective over that source list. No extra entry,
duplicate ID/source index, inferred format pair or mismatched source is allowed. The retained
four matrix obligations are unchanged. IDs remain stable through observation updates; changing
expectation content changes inventory hash, not the caller-assigned ID's meaning silently.

`PrecisionCheckInput` binds component role and original binding, precision, requested callable,
exact callable source SHA256/upstream commit and input-origin classification/limitation.
It contains no query, tp, numeric expected value or fabricated successful EngineResult.
A check invoking another boundary cannot be mistaken for direct-peak UnsupportedPrecision.
The direct peak probe does not run the table bridge or chip KV-storage validation; those
remain separate boundaries. This preserves the four existing direct-peak obligations.

`PrecisionCheckTrace` binds observed execution, reached boundary, error class/message and
check input. It identifies synthetic observations versus captured probe events. Optional
capture_source points to an existing immutable raw observation artifact. `PrecisionRefusalObservation`
binds that trace and available input, repeats the observed facts for reduction, carries its
own hash and expected refusal_id, match_result, evidence_outcome and reason. Trace facts and
observation must agree. Recompute match/evidence; do not trust an author-provided enum.
For not_run, trace/boundary/error are null; retain available input hash or null if unavailable.
A reached successful boundary has null error_class; execution_failure carries its actual
error class and last reached boundary (null if none). Required fields never get invented data.

Expected entries require exactly one observation. A null refusal_id records an additional
unexpected refusal with its own input/trace, preserving the event without inventing an
expectation. Only execution=refused, match_result=unexpected_refusal is legal for a null ID.
A nonnull unknown ID is an invalid join, not that escape hatch. Duplicate unexpected events
(same trace hash) also refuse. A-F12 remains query-level execution=pre_call_refusal with the
actual projection scope; it never occupies a component-level precision observation slot.

Identity and coverage validation precede reductions. After parse/version and hash checks,
validate expected-ID/source-index uniqueness, source-list bijection, observation uniqueness,
unknown nonnull observation IDs, then missing observations, then input/trace correspondence.
This order pins the primary error when defects overlap; no reduction runs after any defect:

| Defect | Named refusal | Verified evidence / gate |
| --- | --- | --- |
| Missing expected observation | RefusalObservationMissing | No verified evidence reduction; gate not_assessed |
| Duplicate observation for ID, or duplicate auxiliary trace | DuplicateRefusalObservation | Same |
| Unknown nonnull observation ID | UnknownExpectedRefusal | Same |
| Extra/unknown/missing source expectation, wrong source index | RefusalInventoryMismatch | Same |
| Duplicate expected ID or source index | DuplicateExpectedRefusal | Same |
| Input/binding/precision/callable/source/trace facts mismatch | RefusalSourceMismatch | Same |
| Missing required query/duplicate fixture/channel | IncompleteComparisonInventory | Same |
| Hash corruption/missing source artifact | ArtifactHashMismatch / ArtifactMissing | Same |

These are verifier failures, not numerical comparison failures. Preserve raw incoming bytes
for inspection, but do not return a verified ComparisonArtifact with an invented reduced
outcome. The caller records the named refusal and not_assessed; an already serialized claimed
outcome is untrusted. This avoids adding a false “complete” enum for malformed evidence.

## R1: complete evidence reductions

Apply execution overrides before numerical comparison. For execution_failed, every query
channel outcome is execution_failed; retain any available actual and the error reason. For
not_run, every channel is unassessed and not_produced, with raw/residual null and zero/no
adjustments. For a recorded pre_call_refusal every channel is refused. Any override contradicting
a declared channel/fixture outcome is ComparisonOutcomeMismatch. An unexpected query refusal
retains refused evidence but fails its nominal obligation. Only the actual A-F12 scope guard
can satisfy the expected query-refusal obligation.

For an executed channel:

| Reference / actual | Channel evidence | Nominal obligation |
| --- | --- | --- |
| Positive / known finite | passed or failed using unchanged count/duration bounds | Numeric bounds must pass |
| Known zero / known zero | passed; raw/residual null, no adjustments | Satisfied exactly |
| Known zero / known positive | failed; raw/residual null, no adjustments | Failed |
| Positive or zero / unavailable actual | **unassessed**, reason required | Failed; no “failed/unassessed” ambiguity |
| Null or absent / known actual | unassessed; preserve actual, raw/residual null, no adjustments | Unknown reference excluded from numerical predicate |
| Null or absent / unavailable actual matching declared nominal omission | modelled_absence | Allowed declared omission; never numerical validation |
| Null or absent / other unavailable actual | unassessed | Failed: missing a model-required output cannot hide behind an unknown reference |

All count adjustment bounds and no-adjustment rules remain as before. Duration remains
abs(raw_rel)<=.001, with no adjustment. A model-required channel cannot be fabricated as zero
or omission. Invalid adjustment policy is ComparisonPolicyViolation (unverified/not_assessed),
not a numeric pass. A valid but over-residual actual is ordinary failed evidence.

For a component precision check:

| Observed execution and correspondence | match_result | Observation evidence | Nominal obligation |
| --- | --- | --- | --- |
| Refused, expected boundary/class/input | matched | refused | Satisfied |
| Refused at wrong boundary | wrong_boundary | refused | Failed |
| Refused at right boundary, wrong class | wrong_error_class | refused | Failed |
| Refused with null ID, fully recorded extra check | unexpected_refusal | refused | Failed |
| Succeeded although refusal expected | unexpected_success | passed | Failed; passed only describes observed execution |
| Check execution failed | execution_failed | execution_failed | Failed |
| Required check not run | not_run | unassessed | Failed |

Boundary mismatch takes precedence over class mismatch if both differ. Source mismatch is a
verifier refusal before either classification. A wrong boundary/class is still an observed
refusal; do not relabel its evidence as numerical failure to simplify the gate.

Normalize channel modelled_absence to unassessed above the channel level. Reduce each fixture's
channels, then all fixture outcomes plus precision observation evidence, using the unchanged
severity order: **execution_failed > failed > refused > unassessed > passed**. At artifact level
only, all passed maps to complete_pass. Therefore matched expected refusals make an otherwise
passed artifact refused, and a matching omission makes it unassessed unless a higher-severity
outcome is present. Required not_run reduces to unassessed, never disappears. The sample's
matrix failures dominate four matched refusal observations: artifact evidence remains failed.

## R1: gate reduction is separate

For structurally and semantically verified inventory/observations:

- Nominal compatibility_pass iff every required channel obligation, every expected precision
  refusal and every expected A-F12 obligation is satisfied, there is no unexpected observation,
  no execution failure and no not_run. Otherwise compatibility_fail. Expected refusals and
  declared omission can coexist with compatibility_pass without complete_pass evidence.
- Physical discrepancy_record_complete iff every required query and component check has a
  completely recorded attempt, with valid identities and explicit reasons/outcomes. Executed
  failures, unexpected success/refusal, unavailable produced values and execution errors can
  be completely recorded. An explicit not_run, missing attempt or invalid source cannot.
  Not_run gives not_assessed, not discrepancy_record_complete. This certifies recording only;
  it never satisfies physical correctness/accuracy or the separate engine-execution tests.

Synthetic presentation outcomes test these reductions only. All four new observations in the
sample are hand-authored. The npu-l4 roles use the existing BF16 synthetic descriptor as a
surrogate, not an actual npu-l4 binding/adoption. The separate recorded-probe example faithfully
translates one existing direct-FP16 refusal, with reconstructed input classification and a
pointer to the prior captured record. It is outside the four-entry inventory and demonstrates
an unexpected auxiliary event, not a new executed four-refusal check. No loader was rerun.

## R2: exact purposes and source recipe inheritance

Replace only the four overbroad comparison wildcard recipes. The finite fixture uses exact
paths `/comparisons/0/fixtures/<i>/channels/<j>/<ratio>`; j=0..3 are count channels and j=4 is
duration_s. Cross-check j against the bound channel name before lookup; changed ordering
requires new reviewed recipes and hashes. No new JSON Pointer/filter/selector language.
Every numeric comparison ratio, including signed/absolute adjustment zero, uses its channel's
purpose. Missing/null ratios remain absent; they need no display recipe. A count-only evidence
record cannot validate a duration ratio, even when the ratio is zero.

`MetricDependencies.source_recipes` is a list of SourceMetricRecipe records: source artifact
hash, source model_identity_hash and an ordinary MetricRecipe with an exact source JSON
Pointer as metric_path. These are dependency recipes, not permission to render their targets.
The entire source recipe list is covered by the existing reviewed-body hash and dependencies
hash. No ambient registry of recipes and no new selection syntax is introduced.

A result_field selector **always recursively inherits** the uniquely matched source recipe
for (artifact_hash, exact json_pointer). Its value/hash binding alone never contributes
provenance. Check source model identity against that recipe's model_evidence selector and
carry its independent scope/purpose requirements. For a model_evidence leaf naming a source
ModelIdentity, require H(identity)=SourceMetricRecipe.model_identity_hash, then resolve all
applicable evidence through this bound ReportContext.evidence_index, filtered by that source
model, purpose, granularity and full scope. The context primary model does not stand in for
the reference model. A resolved but inapplicable/missing evidence match contributes stub; a
missing referenced artifact refuses closure. No ambient card/ledger fallback.
Other selector kinds terminate in verified
original sourced leaves, prepared input assumptions or the identified model's evidence.
Do not recursively follow a leaf merely because it contains a hash. Hash-shaped data is not
an implicit dependency declaration.

For each ratio, union these dependency sets without weakening any one of them:

1. Actual metric's complete recipe: physical counts consume graph/workload/count assumptions;
   actual timing also consumes all used matrix/vector peaks, core count/frequency, bandwidth,
   traffic/overlap assumptions and physical model evidence. Propagate original claims and
   conditions; derived projections cannot hide a stub source. ps_to_seconds changes neither
   contributors nor purpose and may occur only through the bound ProducedValue conversion.
2. Separately identified reference metric's recipe: original component/model inputs and
   reference model assumptions/evidence under its own identity and purpose. For the sample,
   these are explicitly stipulated synthetic reference literals and the separately bound
   reference AssumptionSet; they are not an adopted oracle recipe. For later frozen data the
   recipe must bind the declared nominal inputs/precision/tp, original component peak/bandwidth
   and execution efficiency (including .55), source fingerprint and reference model. It may
   not select just the reference value or borrow the actual model's evidence.
3. Declared adjustments and their validation/limitations. Empty declarations add no phantom
   stub claim. Nonempty named declarations without validating evidence remain unvalidated
   model assumptions and contribute stub. Signed/absolute zero remains a known bookkeeping
   zero; it is not duration validation. Raw/residual may not gain a stronger badge by dropping
   a dependency; the sample uses the conservative full union for all four ratios.

A comparison's badge is no better than any inherited actual/reference/adjustment contributor,
with scope, model and purpose evaluated independently for each source. A failed numeric
comparison can still have well-supported inputs; numerical verdict and provenance badge are
distinct. Conversely zero timing error cannot remove a stub hardware input or uncovered timing
model. No ratio computation promotes evidence or changes the model's validation rung.
Source error bands are not combined into a comparison confidence interval or copied to the
ratio: its band remains unknown absent separately applicable supplied ratio evidence.

Reject MissingSourceMetricRecipe, AmbiguousSourceMetricRecipe (including duplicate target
records), CyclicMetricRecipe (direct/indirect recursion), MetricPurposeMismatch,
IncompleteMetricContributors (omitted required source computation dependency), or
ReviewSubjectMismatch. No fallback to value-only provenance, broad wildcard precedence,
count evidence, a favorable source or empty contributors. Required dependency coverage follows
the already declared physical/nominal computation contracts; a signed recipe cannot authorize
omitting a required input. Shared DAG nodes may be memoized and identical original leaves
merged by artifact+pointer, but retain all source scopes and conditions; cycles never qualify.

## R2: precise fixture/display expectations

The dedicated synthetic evaluator context gives actual and reference models eligible L3
**matrix-count-only** evidence with no error band, complete matching synthetic prerequisites,
and explicit compiler-chosen scope. It does not alter the real analytic fixture's unknown
mapping or its default stub card. There is no eligible duration evidence. The actual timing
source uses a genuine `kind: claim, provenance: stub` bandwidth leaf from the existing hardware.

- Matrix raw ratio1184/1000-1=.184: inherited count model evidence eligible, no timing hardware
  used, no adjustments => estimated in this synthetic evaluator scenario, band unknown.
- Duration raw ratio0: duration evidence uncovered on both models and true stub bandwidth
  retained => stub, band unknown. Default hidden; the existing explicit synthetic display
  mode may show it with synthetic/unvalidated labels and complete contributors only.
- Even eligible synthetic duration evidence on both models cannot lift that real stub claim.
- Removing or mismatching source recipes, dropping timing hardware/reference model inputs,
  or cyclic/ambiguous inheritance refuses with the named errors above; no value rendered.

Raw actual/reference magnitudes remain stored and available to the verified loader. They
have **no display recipes in this sample**, even though internal source recipes exist.
They stay hidden on all surfaces, including opt-in; a direct numeric render request returns
MissingMetricRecipe. This includes labels, SVG axes/geometry/tooltips/data/accessibility and
numeric warning strings. Stored values and source identities are never erased to hide them.
The same rule applies to any unlisted metric or incomplete contributor closure.

All expected semantic verdicts above are test specifications. Checks in this turn validate
schema shape, exact fixture correspondence, recipe coverage/pointers, hash/review propagation
and independent expected arithmetic/reduction tables. They do not run the future comparator,
renderer, evidence-eligibility evaluator, nominal candidate or physical engine.
