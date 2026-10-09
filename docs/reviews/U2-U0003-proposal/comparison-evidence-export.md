# Complete companion interfaces — proposal revision 3 (R1/R2 only)

These rules and proposed.schema.json jointly specify the review-only interface. Every object
is closed, versioned and has a self hash excluding only its own hash field. Required nulls
are explicit; all numerics finite and type-strict. Unknown version, duplicate JSON keys or
artifact IDs, missing companion, invalid hash, conflicting identity, unresolved required
selector or ambiguous scope causes a named refusal, never ambient fallback. This supplements
interfaces.md; all added schema roots and ownership are listed in delivery.md.

## Comparison artifacts

`ReferenceInventory` identifies adopted manifest (raw SHA256), reference model and ordered
complete fixtures/refusals. Synthetic fixtures explicitly carry `synthetic_reference`, so
cannot stand in for adoption. Each fixture has component binding, explicit precision, query,
tp, ProjectionScope (global KV/vocabulary, replication/padding) and exactly all five channels.
`ReferenceValue.state` distinguishes positive, zero, null and absent. State/value combinations
are constrained. An absent field in the source is represented explicitly, not dropped.

`ComparisonArtifact` binds reference inventory, reference model/basis, candidate ModelIdentity,
track, every fixture and precision_refusal_observations. Expected component refusals
join by refusal_id through bound input/trace/source records, separately from query A-F12.
See R1-R2-corrections.md for the required bijection, defects and reduction order. Its `ComparisonFixture` binds input/output or bundle/job/result
identities. Nominal requires candidate_input_hash/output_hash and forbids physical job/result;
physical requires bundle/job/result for executed cases and forbids nominal output identity.
Before-call refusal retains available captured input identity or null when none exists;
no fabricated job/result. `ProducedValue` carries raw value, source hash/JSON Pointer and
explicit identity or ps_to_seconds conversion. Verify against the artifact, no hidden unit
conversion. Five unique channels have fixed units: ops, bytes, seconds. Missing/duplicate
channel/fixture or a changed query/component fails `IncompleteComparisonInventory`.

For positive count reference r and actual a: raw_rel=(a-r)/r; signed_adjustment_rel=sum(d_i);
absolute_adjustment_rel=sum(abs(d_i)); residual_rel=raw_rel-signed_adjustment_rel. Each d_i
binds name/reason/fixture/channel/unit. Absolute spend ≤.05 and abs(residual)≤.005;
raw abs≤.005 forbids adjustments. Cancellation never refunds spend. Known zero requires
actual known zero, no adjustments, raw/residual null. Null/absent references forbid all
adjustments and relative errors; actual raw values survive with unassessed. Matching nominal
omissions use modelled_absence, explicitly no numeric validation. Duration raw_rel uses
actual seconds/reference seconds and abs≤.001, with signed/absolute zero and residual=raw.
Unavailable actual on a known reference is unassessed, with a failed nominal obligation.
R1-R2-corrections.md fixes the complete execution/evidence/gate reduction table.

Execution status is separate: executed, pre_call_refusal, execution_failed, not_run. The last
is for an actual unattempted case only; it fails completeness if an attempted comparison is
required. Per-channel outcome and reason survive every case. Fixture/artifact evidence reduce
by execution_failed, failed, refused, unassessed, passed in that severity order;
modelled_absence counts as unassessed. Expected refusals remain `refused` evidence even when
accepted by the gate. Gate is separate: compatibility_pass/fail for nominal;
discrepancy_record_complete only when physical inventory, source bindings and reasons are
complete attempted coverage (can include actual failures), never a physical accuracy pass.
Explicit not_run cannot be complete. Invalid/missing/duplicate/source-mismatched inputs refuse
verification before any reduced evidence outcome; the caller records not_assessed.
All-attempted comparison hashes bind ReportContext and ArtifactBindings. `comparison_state`
is attempted if any exist; no passing-only `FlopParity` carrier. Legacy FlopParity remains in
schema definitions for historical inspection but is not a 0.2 Table field.

Fixtures comparison-inventory/physical.json deliberately show 1184 vs 1000, zero reference,
known writes vs null, vector absent, and an explicit tp16/KV8 A-F12 refusal. They are synthetic
presentation values, not physical execution or frozen oracle data. The refusal has no bundle
because it is an independently specified scope probe; inventory still carries its exact scope.
Actual full inventory generation is planned after acceptance, never inferred from this sample.

## Authoritative export and test projection

`ComponentExport` is authoritative extended truth: format/hash, component ID, original spec
hash/design status, derivation hash, full Parameter values and explicit execution-model hash.
ExecutionModelInput is a separate declared model assumption, not a HardwareSpec field or
hardware-derived fact. Require compute/memory appropriate to scalar/split; scalar memory null
means the documented unscaled-memory omission, not unknown hardware bandwidth. Preserve
source/kind/provenance/date/rationale and accepted/proposed input status.

`ExportBinding` binds primary export, original spec/status/derivation, execution model,
projected descriptor canonical content hash AND exact descriptor byte hash, upstream pin,
recipe, losses and supported KV storage. `ComponentPrecision` embeds that binding, exact
component ID, explicit unique compute/KV pairs and precision_hash. Both fields required;
`[{}]`, missing KV, duplicate pairs and invented formats fail structurally. Generic accepted
Precision defaults are untouched. Upstream-only bindings instead carry pinned component
bytes, oracle manifest and original execution-model hash, with no uarch spec/derivation.

Proposed `uarch rk-component SPEC --execution-model FILE` emits extended truth and companion;
`--oracle-compat` additionally emits a separately named test descriptor and binding. This
replaces the direct upstream-library YAML promise explicitly. Descriptor contains id,
kind=compute_resource, role=asic, params with supported `<format>_tflops`/`_tops`, hbm_bw TB/s,
hbm_capacity GB, tdp W, execution_model, fidelity_available and calibration. Design status
remains authoritative in binding and deterministic YAML comment if exported as YAML; upstream
descriptor does not gain a new unsupported field. JSON fixture is valid YAML input.

All upstream SourcedValues have exactly value/unit/provenance/source/date. Strip extensions
for every value, including claims; claims alone do not make an extended carrier loadable.
Preserve a claim grade only when its real citation meets the pinned loader's requirements
and real measured calibration anchors are present. A derived `uarch-derive:` source is not a
valid datasheet URL, estimated derivation path or measurement anchor. Test-only projection
may use stub/null source/date for ineligible claims and stipulations; record original and
projected values and reason for every loss. Never create a URL/anchor or alter original truth.
Execution-model losses must be included too, not just params. Prefer fidelity_available STUB
and empty calibration for this synthetic projection. No real validation follows from loading.

Full pinned loader and private adapter checks were actually run against synthetic descriptors:
18 cases, zero oracle calls; see loader-probe-results.json and reproducible guarded probe.
Missing execution_model, extended fields, invalid measured/spec_derived/estimated citations
and duplicate library ID fail ComponentLoadError. Unknown Precision enum fails ValidationError.
Missing selected peak, no peaks, missing bandwidth or wrong units fail EngineError at
_accelerator; direct Accelerator.peak_op_per_s fails UnsupportedPrecision. Loader acceptance
alone does not select precision. Unsupported KV storage requires proposed bridge
UnsupportedKvStorage before adapter: pinned Precision/adapter accepts BF16 compute/FP8 KV
without chip storage support. Nonpositive/infinite numbers, mismatched peak derivation,
execution-model mismatch or altered companion hashes are proposed bridge refusals, not claims
that upstream already enforces them. Probe cannot discharge that future bridge implementation.

Retained asic/H100 bindings use actual bytes and .55. Synthetic BF16-only fixture uses tiny
reference stub hardware and explicitly proposed efficiency1.0; it is not npu-l4 or a fabricated
npu-l4 artifact. Actual proposed npu-l4 BF16-only export and 1.0 assumption need B-authored
hardware and Javid acceptance before human generation. Counts/durations were never generated.

## Evidence and offline closure

Shared roots: EvidenceRecord, SourceRecord, ReviewRecord, OrderingRecord, VerificationRecord,
FamilyRegistry, MetricDependencies, ReportContext and RenderSpec. EvidenceRecord has stable
ID/hash, real/synthetic classification, rung, purpose (duration/counts/diagnostics/energy),
channel, energy_family, granularity, independent scope cases, source/review/ordering hashes,
verification hashes and independently nullable error_band. Applicability never depends on
whether an error band exists. Null band remains unknown. Bands are observed bounds, not
confidence intervals or values invented from rung. Multiple applicable incompatible bands
are refused as ambiguous unless a reviewed selector identifies exactly one; no averaging.

SourceRecord binds kind, exact reference identity/version/raw blob digest, independence from
candidate and limitation. ReviewRecord binds reviewer, independence, decision, exact subject
hashes and rationale. For objects containing review_hash, reviewed subject is canonical body
excluding its self hash and review_hash; this avoids cycles while binding every other field.
For raw sources, subject is the complete source hash. Registry/recipes/evidence/verification
each need their own matching review subject. Changing a body invalidates its review even if
someone recomputes the enclosing self hash. Review acceptance is evidence data, not authority
for this proposal; synthetic reviewer strings never claim Javid signed anything.

L0/L0m/L1/L2 VerificationRecords bind scope, model, purpose, source/review and actual outcome.
L3 requires same-class silicon measurement (device-side time for duration), accepted independent review,
passed relevant verification and OrderingRecord proving committed prediction predates results
(ancestor check and pinned tree). L4 requires target silicon measurement with independently
reviewed source and scope; a simulated or hand-derived source cannot be relabelled silicon or exceed L2. L3 duration also
requires workload FLOP/byte fidelity checks and explicit matched/compiler-chosen class;
diagnostic promotion needs device counters where supplied. Raw source artifacts bind those
checks and their measurement protocol. No mapping class is inferred from a policy name. These requirements
apply even with error_band=null. Ordering source must actually establish order; a boolean
assertion alone cannot. Synthetic records only exercise evaluator fixtures in explicit test
mode and cannot raise any real model card. Test fixtures use synthetic commit IDs deliberately.
Nominal compatibility evidence is counts/duration compatibility at most L0–L2, never L3
independent physical timing evidence. Model identity cannot be substituted between tracks.
Energy remains null/unverified; no energy computation. If a later figure uses energy, every
used family mac/sram/noc_hop/dram/static must have applicable L2 verification tied to that
model/spec/purpose; counts/duration evidence cannot verify energy.

EvidenceScopeCase is a conjunction, a list is a union of complete cases: never cross-product
fields from two cases. Family comes from reviewed exact spec-hash FamilyRegistry in bound
report context, not engine or ambient hardware-name lookup. A missing family match is UNKNOWN;
missing registry artifact is ArtifactMissing. Duplicate spec mappings are AmbiguousArtifact.
ReportScope carries op class, role-specific precision and nullable U1 bins/load/mapping;
format names match exactly. Compute/KV/each operand are separate roles; BLOCKFP8 is not fp8.
No new bin boundaries. Evidence can omit irrelevant dimensions only when a reviewed metric
recipe explicitly excludes them; null in a required dimension is UNKNOWN, never wildcard.
Not all duration evidence must know an irrelevant NoC load for U-C0 with no NoC time.

Purpose/granularity must match: whole-iteration duration evidence never covers an operator
point; a GEMM count fixture never covers whole-model duration. Operator-scoped row claims
require every contributing operator covered, with mismatched/unknown IDs retained. Applicable
whole-iteration evidence can cover only whole-iteration metrics with exact bundle identity.
State, KV block, frequency, model identity, spec and bundle/mapping correspondence are matched
whenever relevant. `matched` requires a checked correspondence artifact, never policy-name
equality. Unknown evidence cannot be widened by a renderer or flattened to a card's best rung.

MetricDependencies is a reviewed, versioned list of exact output path patterns, purpose,
granularity, applicable dimensions and hash-bound selectors. A selector resolves a JSON
Pointer into an identified artifact. result_field selectors recursively inherit the unique
source_recipes entry for that artifact/pointer, not just its numeric value. Other subtree
selectors enumerate all used original sourced leaves. Exact source-recursion, purpose,
coverage and cycle/ambiguity rules are normative in R1-R2-corrections.md. Expand before combining; preserve every real claim and condition. No remote lookup,
no magic unknown JSON fields. Recipes include counts/workload conventions, matrix and vector
rates, core count/frequency, memory bandwidth, timing overlap and traffic assumptions. Counts
and OI do not consume unused peak values; timing/throughput do. Numeric input display uses
input purpose; it is not duration validation. Comparison raw values bind their actual source
and reference; ratio recipes retain count or duration purpose by channel and inherit both
source models/inputs and any adjustment assumptions. Adjustments do not change physical work.
Raw actual/reference values have no sample display recipes: hidden even with opt-in, while
remaining stored and accessible to the verified loader.
The fixture recipes are for the declared sample table fields; any unlisted numeric field,
including newly added warning magnitudes, must get a reviewed recipe or be hidden/refused.
No unresolved selector is a contributor. An empty hardware-claim summary is null, not a stub
claim. Model assumptions/evidence still contribute: all stipulations plus eligible L3 may be
estimated, while a genuine stub claim keeps stub. Completely empty contributor set is stub
and cannot render an opt-in prediction. Proposed design ceiling remains estimated.

ReportContext/2 binds request/model/assumptions, registry, recipes, evidence ID→hash,
verification hashes, comparison hashes, used energy families and limitations. Table binds
context and attempted comparisons; full card evidence IDs resolve exactly through this
context. A's verified artifact loader recursively validates source/review/order/raw blobs,
versions, hashes, paths, requested identity and complete selectors before B evaluates badges.
Hash-addressed JSON files and raw blobs are offline companions; include no absolute paths or
live timestamps. Missing, tampered, ambiguous and unresolved inputs refuse before rendering.
No engine, producer or physical recomputation is permitted in a report.

## Display decision and exact demo contract

Recommendation C5: default hide magnitudes of STUB computed metrics. Explicit
`uarch report TABLE --show-unvalidated-predictions` may display a finite, actually computed
prediction only with complete resolved contributors and visible label
**STUB — unvalidated model prediction** beside every metric/series. It cannot promote a badge.
Null is absent/not modelled, never zero. Missing/unresolved contributors never qualify.
Synthetic presentation fixtures require separate test-only allow_synthetic_presentation and
label “synthetic fixture — not executed”; product report refuses that mode for real evidence.
Alternative needing Javid's deliberate decision: visible-by-default STUB predictions with the
same labels and closure; easier exploration, greater risk that a number is read as validated.

Permissions cover text, tables, HTML/Markdown, SVG points/lines/geometry/domains/axes,
tooltips, data attributes, titles/ARIA/accessibility and numeric warnings. Hidden values cannot
influence an axis extent or survive in raw attributes/comments. Count metadata is a separate
classified input, never an excuse to expose a forbidden magnitude. Null has no plotted point.
Per-op roofline on aggregate rows says “isolated per-op roofline estimates; durations do not
add to aggregate latency.” The literal plot fixture is 18ps sum versus 10ps aggregate.
RenderSpec binds renderer_version, exact table/context, both explicit flags, locale and number
format; render_hash is output identity. Changing display changes report identity only; no
clock or hash-excluded generation comment. HTML and Markdown repeated bytes must be identical.

Proposed U-P4/demo wording: “The default table→report demo shows conditional inputs, unknown
error, C0 fidelity, not-modelled diagnostics and hidden STUB magnitudes with reasons. An
explicit --show-unvalidated-predictions demo additionally shows finite predictions, complete
contributors and STUB — unvalidated model prediction labels. Both retain every physical
comparison failure/unassessed/refusal and identify nominal compatibility separately.”

## Exact evidence vocabulary and model-card projection

New evidence uses separate typed intensity_regime/array_fill/noc_load_regime/dram_load_regime,
not ambiguous combined strings. U1 bins stay intensity low<.5, middle [.5,2], high>2; load
low<.30, middle [.30,.70], high>.70; fill underfilled when M<rows OR N<cols, full otherwise.
For legacy named-regime display only, canonical strings are
`intensity=low;array_fill=full` and `noc=low;dram=middle` (fixed field order, exact enum names).
No legacy arbitrary string or missing role is inferred into eligible evidence: an explicit
reviewed migration record must supply the typed scope or the import is refused. That is a
capability refusal, not a widening of accepted bins. Non-GEMM fill stays null and is excluded
only by an explicit reviewed class/purpose recipe; unknown required load is never MATCH.
Mapping class remains required for model promotion; analytic null means uncovered. The
positive no-band fixture uses a separately declared synthetic compiler-chosen scope and does
not certify the analytic fixture's null correspondence.

The legacy full/embedded ModelCard summary is cross-checked against the new report context;
evidence IDs must resolve, verification slots must match any claimed executed record, and
unknown slots remain null. If typed role-specific/compound scope cannot be represented exactly
by the legacy band carrier, keep that summary band null and display eligible per-metric bands
only from the complete evidence artifact. Do not flatten cases or invent a broad ModelCard
scope. No-band eligible model evidence can promote within its exact scope without a band.
Fixtures' synthetic verification data never replaces an unexecuted model-card slot. Reports
for real data reject synthetic evidence; the fixture RenderSpec test flag is explicit.

The R1/R2 correction is normative for precision observations and comparison contributor
recipes. Its schema pointers, exact outcome tables and semantic fixture IDs are in
[R1-R2-corrections.md](R1-R2-corrections.md). No unrelated interface decision changed.
