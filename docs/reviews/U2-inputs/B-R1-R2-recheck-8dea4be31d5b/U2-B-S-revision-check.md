# U2 B — focused check of A's revised S proposal

**NOT READY.** Two narrow proposal corrections remain: an observed-result interface and
complete outcome rules for precision-refusal inventory entries (R1), and comparison recipes
that respect metric purpose and declare their contributor treatment (R2). These are interface
issues, not demands for runtime implementation before a human decision. The proposed S gate
change, export split, rank policy and display policy otherwise have concrete choices for Javid.

This is a proposal compatibility report, not sprint U-REVIEW, acceptance of U0003/U0004,
or authorization to implement. S was selected for drafting only. Accepted policies remain
operative until Javid accepts exact amended bytes. No broad H/R reconsideration is requested.

## Inputs and integrity

B worktree: `/home/jjaff/AI-infra-simulation/rk-uarch-u2-b`. Entry status contained only the
untracked preparation and initial compatibility reports. Both remain unchanged:

- `U2-B-preparation.md`: `12c38ea9f9ae6d64ff59b69aab6e5ee4e1e5761414d1a94daba037e0efa58dbf`.
- `U2-B-U0003-compatibility.md`: `a4ef227c7ac563d6b02e4197137e30cef773dd8565aa1b14f00c7904a8099fb8`.

In this report, **A/** is the preserved repository-relative root
`/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-inputs/A-S-proposal-59d9d3889e86/`;
**P/** is `A/docs/reviews/U2-U0003-proposal/`; **F/** is `P/fixtures/`.
Schema pointers below are into `P/proposed.schema.json`. ADR means
`A/docs/decisions/U0003-one-chip-one-set-of-facts.md`.

Independently verified manifest SHA256
`59d9d3889e8687128bd0da0a2a39cf25c4a44b9da01e0ed4793c27673d5d24f8`
and all **81 entries**, including a second integrity pass after the probes. Read the revised
handoff, dispositions, change inventory, amendment, companion interfaces, delivery, schemas,
selected fixtures, loader evidence and complete public patch/index.

Coordinator instruction SHA256:
`547080372d6a5785409c5bcb16922ac5920e0d45f2000d1e6651c1af1e46a0fc`.
Coordinator intake SHA256:
`bd7e1e029db92bded2af60704b856dc9dfc54aea249096c4d3d297426092c854`.
Javid remains acting human decision-maker for both lanes; no other human approval is inferred.

## Blocking corrections

### R1 — expected precision refusals have no corresponding observed result interface

**C2 remains open.** Exact references:

- `#/$defs/ReferenceInventory/properties/refusals/items`;
- `#/$defs/ComparisonArtifact`, `ComparisonFixture`, `ComparisonChannel`, `ProducedValue`;
- P/comparison-evidence-export.md, “Comparison artifacts”; P/two-track-amendment.md,
  complete-inventory and compatibility-pass paragraphs;
- F/comparison-inventory.json, comparison-physical.json, comparison-cases.expected.json,
  precision-inventory.expected.json.

The inventory's refusal entries contain component binding, explicit precision, boundary and
expected error class. They contain no query or fixture ID. The comparison has only query
fixtures: each requires fixture_id, query, tp, projection_scope and five reference channels.
It has no collection of observed outcomes corresponding to `ReferenceInventory.refusals`,
no defined mapping of those entries into query fixtures, and no structured observed boundary
or error-class field. Channel `reason` strings cannot supply an interoperable substitute for
an unspecified mapping. `limitations` is not an execution result carrier.

This matters for the **four proposed direct-peak precision refusals**, independently of the
A-F12 case. The synthetic tp16/KV8 A-F12 fixture is already a query inventory entry and is
representable. It does not exercise the separate precision-refusal inventory. The sample
`refusals` list is empty, so the package's positive checks do not expose this gap.

**Read-only counterexample:** in memory, appended one real-shaped expected placeholder
BF16/BF16 direct-peak refusal to the synthetic inventory, recomputed its self hash, and
rebound/rehashed the existing comparison. Both objects remain structurally valid. The
comparison still contains only its three original query fixtures; it records nothing about
whether the added refusal check ran, returned the expected error, unexpectedly succeeded,
or failed elsewhere. The normative completeness promise would require a semantic check,
but the proposed shared data does not carry that check's observation. This is not a claim
that JSON Schema must encode every semantic invariant, or that an implemented gate passed.

The reduction prose also leaves two observable states underdefined: an unavailable actual on
a known reference is called “failed/unassessed” without choosing the evidence enum, and
`not_run` has no explicit evidence reduction in the listed precedence. The nominal gate must
fail in both cases when the comparison is required; B should not invent the evidence result.
The prose specifies broad failure behavior but the semantic fixtures do not pin these cases
or distinguish observed expected/unexpected precision refusals.

**Minimal correction:** A should propose one shared observed-refusal representation, or an
explicit common inventory-entry union, with stable correspondence to each expected refusal,
observed execution/boundary/error, available source/input identity and a separate match result.
Define how missing, duplicate, unexpected and incorrectly observed refusal entries affect both
outcomes. Do not fabricate a query, numerical reference, zero result or successful EngineResult
for a component-level refusal. This report proposes requirements, not new field spellings.

Freeze a small outcome table and schema-valid semantic examples covering at least:

| Case | Recommended evidence result | Recommended gate treatment |
| --- | --- | --- |
| Executed known zero versus zero | passed | Exact zero; no adjustment |
| Known reference with unavailable actual | unassessed, with reason | Nominal fail; never numerical compatibility |
| Null/absent reference with known actual | unassessed | Retain actual; exclude from numerical predicate |
| Declared nominal omission matching unknown reference | modelled_absence at channel, unassessed above | Allow only the declared omission; never complete_pass evidence |
| Expected refusal observed at the right boundary/class | refused | May satisfy its inventory obligation |
| Unexpected refusal, wrong boundary/class, or unexpected success of a refusal check | Preserve observed evidence | Nominal fail |
| Execution failure | execution_failed | Nominal fail; preserve error and available identities |
| Required check not run | unassessed, explicitly not_run | Nominal fail; physical completeness not_assessed |
| Missing/duplicate entry or source mismatch | Named inventory/binding refusal | No complete gate result |

For physical discrepancy reporting, explicitly distinguish a completely recorded attempted
failure from a missing required attempt: complete diagnostic recording can include failures,
but never becomes physical accuracy or discharges separate physical execution tests. A's
existing `discrepancy_record_complete` distinction is appropriate. Specify the refusal reduction
alongside it. Keep the stated severity ordering and exact budgets; no tolerance change needed.

### R2 — comparison recipes assign count purpose to duration ratios

**C4 remains open at the recipe boundary.** Exact references:

- F/metric-dependencies.json, the four recipes with
  `/comparisons/*/fixtures/*/channels/*/{raw_rel,signed_adjustment_rel,absolute_adjustment_rel,residual_rel}`;
- `#/$defs/MetricRecipe`, `DependencySelector`, `ComparisonChannel`;
- P/comparison-evidence-export.md, “Evidence and offline closure”, purpose/granularity and
  used-contributor requirements; F/comparison-physical.json's `duration_s` channels.

All four wildcard recipes specify `purpose: counts`. The channel wildcard includes
`duration_s`. A duration discrepancy does not become a count metric because its result is a
ratio. This conflicts with the same proposal's rule that count evidence cannot establish
duration evidence. The fixture's all-stub card masks the distinction; it would matter when
applicable count evidence and inapplicable duration evidence differ.

Each comparison recipe selects the comparison `/fixtures` subtree as `result_field`, plus
only the physical ModelCard `/model_id`. The subtree preserves raw source hashes/pointers,
which is useful. However, the companion rules do not define whether a `result_field` selector
recursively follows the source metric's contributor recipe, or merely verifies its numeric
value. Do not let the renderer choose that meaning privately: the timing source's hardware
claims and the separately identified reference model cannot simply disappear when forming
a displayed comparison ratio. A bound number is not by itself a complete contributor recipe.

**Minimal correction:** split recipes by count versus duration channel using explicitly
specified paths/selection rules, or deliberately classify comparison ratios as diagnostics
and define the corresponding diagnostic evidence policy. Either alternative must specify
source-metric/reference dependencies and preserve their limitations; neither may borrow count
validation for a duration comparison. Exact index paths can express the finite sample without
adding a new selector language. If a reusable channel selector is preferred, A must propose
it in the shared carrier before B uses it.

Add a discriminating semantic fixture with count-only eligible evidence and uncovered duration,
plus a timing source containing a real stub hardware claim. Demonstrate that the duration
comparison cannot acquire a stronger badge through the comparison recipe. No runtime
implementation is requested for this correction. Raw actual/reference magnitudes currently
have no sample recipes; explicitly keep them hidden/refused under the existing rule or supply
reviewed recipes before promising their opt-in display. Their complete stored values must
remain accessible to the verified loader in either case.

## C1–C5 dispositions beyond those corrections

| Finding | Revision disposition | Evidence and remaining status |
| --- | --- | --- |
| C1: physical/nominal accounting and efficiency | Ready for an explicit human policy decision | P/two-track-amendment.md old/new exits and isolated nominal model; ADR D8; `ModelIdentity`, `NominalInput`, `NominalOutput`, `AssumptionSet`. The physical graph is no longer promised to match the incompatible nominal count/duration reference. Numeric budgets remain unchanged but their subject changes. |
| C2: complete comparisons | R1 blocks closure; main numerical transport is improved | Five channels, positive/zero/null/absent reference states, raw actual source pointers, named units/conversions and separate evidence/gate outcomes are concrete. F/comparison-physical.json preserves positive mismatch, zero mismatch, known writes versus null, absent vector and A-F12 refusal. |
| C3: export and precision | Proposal interface ready for human decision | `ComponentExport`, `ExportBinding`, `ProjectionLoss`, `ExecutionModelInput`, `UpstreamComponentBinding`, `ExplicitPrecision`, `ComponentPrecision`; P/comparison-evidence-export.md export section. Actual bridge and npu-l4 artifacts remain planned. |
| C4: evidence closure | Substantially addressed; R2 blocks recipe closure | `EvidenceRecord`, `EvidenceScopeCase`, `EvidencePrecision`, source/review/order/verification records, `FamilyRegistry`, `ReportContext/2`, metric recipes and exact companions now exist. Applicability no longer depends on a nonnull error band. |
| C5: STUB display | Ready for human choice, conditional on complete contributors | `RenderSpec`, F/render-default.json, render-opt-in.json, evidence-display-cases.expected.json; companion display section and U-P4 hunks. Default hide and explicit opt-in are concrete. R2 must not be bypassed to make a numeric comparison visible. |

The nominal candidate is explicitly test-only at `contract/tests/nominal_candidate.py`.
The callable receives nominal model/query/tp/precision/component/model inputs, no fixture ID
or expected counts/duration; B's comparison runner holds the reference side outside its
isolation boundary. It cannot import rk, vendor readers, the physical producer or OpSpecs,
and is not a CLI engine. Binding/source hashes are identities, not lookup permission. File,
network, import and lookup/delegation mutants are required future tests, not completed evidence.

Count rules remain total absolute adjustment <=0.05 and absolute residual <=0.005 per positive
fixture/channel; raw-inside-tolerance, zero, null and absent references forbid adjustments.
Duration retains abs(raw_rel)<=0.001 without count adjustments. Known zero remains exact.
The old count conflicts and raw-peak/.55 diagnostic are retained rather than retuned.
Pinned source inspection confirms nominal weights use active_params; total_params is a
capacity concern. Hand checks reproduce the proposed tiny literals (592 ops/296 ns decode,
1488 ops/744 ns prefill for the synthetic descriptor). They are not oracle generation or
executed nominal compatibility. Retained scalar .55 and unscaled memory are explicit inputs;
new efficiency 1.0 remains a proposed unvalidated assumption.

C4's other closures are coherent at proposal level: purpose/granularity, role-specific precision,
independent compound cases rather than a Cartesian union, exact-spec family registry outside
engine identity, required-dimension UNKNOWN, unchanged bins and no BLOCKFP8 alias. No-band
L3 applicability requires source/review/order/verification just as banded evidence does.
All-stipulated inputs have a null claim summary; a real stub claim still lowers the metric.
Completely empty contributors cannot render an opt-in prediction. L0–L2 cannot promote a
real model; synthetic L3 fixtures are evaluator fixtures only. Their invented commit/tree
identities are not ordering proof for real predictions. Energy remains unmodelled/unverified.

Reviewed-body hashing correctly excludes only self hash and review_hash for an object that
contains a review, then its final self hash binds that review. Independently checked the four
review-body bindings. The raw source digest in evidence-source.json resolves to the exact bytes
of F/decoder-op-counts.expected.json; it is not a missing blob. All 113 sample selectors resolve.
A's reported closure audit should still not be described as an executed production evidence
validator: semantic eligibility, correspondence and ordering checks remain future work.

The display proposal covers text, HTML/Markdown, SVG geometry/domains/axes, data attributes,
accessibility, tooltips and warning magnitudes. Hidden values cannot set axis extents. Nulls
have no plotted point and never become zero. Finite executed predictions with complete
contributors may opt in with the adjacent STUB label; synthetic presentation is separately
flagged and cannot masquerade as execution. Render identity binds table/context, renderer
version, options, locale and number format. No timestamp exception remains.

## Export, retained matrix and physical scope

C3 separates authoritative extended truth from a lossy five-field test descriptor, with exact
canonical content and raw descriptor-byte hashes. Original spec/status, derivation, execution
model, original/projected SourcedValues and reasons stay bound. Stipulations remain in primary
truth; test projection may lower provenance without inventing a citation or calibration.
The fixture uses stub claims, so it does not prove the future stipulated projection validator;
the proposed carrier and loss reason can express that case. A stipulated-clock/mixed-stub test
remains required implementation acceptance work.

Read A's full-loader probe source and its 18-case output; independently matched all three
recorded pinned-source fingerprints. Those checks cover full loading and private precision
selection, with zero recorded oracle evaluations. Missing execution model/extended values/
ineligible citations fail ComponentLoadError; missing selected peaks through `_accelerator`
fail EngineError, while direct `Accelerator.peak_op_per_s` fails UnsupportedPrecision. Unknown
format fails Precision validation. BF16 compute/FP8 KV succeeds through the upstream adapter:
chip KV support therefore remains a proposed bridge check, not existing upstream enforcement.
Hash, positive/finite value, derivation/model consistency and supported-storage bridge checks
are not implemented by loader success. This review did not rerun the write-producing probe.

Both retained component byte digests match their actual files in the frozen vendor snapshot.
Upstream-only bindings carry no invented uarch spec/derivation. Explicit compute and KV fields
are required and duplicate pairs are structurally rejected without changing generic Precision.
The matrix remains **864 retained successes + 144 npu-l4 BF16/BF16 = 1008 successes**, with the
two retained placeholder missing-peak refusals and two proposed npu-l4 missing-peak refusals.
The four expected paths are direct peak UnsupportedPrecision; R1 concerns recording their
actual observations. Optional npu-l4 BF16/FP8 adds 144 only after explicit storage declaration
and a separately reviewed decision. The synthetic BF16 descriptor is not npu-l4.

No retained count/duration/null value change is authorized by S. New comparison interpretation
(null/absent unassessed), metadata/bindings and whole artifact revision are explicit proposals;
any unexpectedly changed old value during later generation must be reported and reviewed,
not silently accepted as part of the 1008 expansion. Actual hardware authoring, frozen-tool/input
review, Javid's two generation runs and whole-revision adoption remain outstanding B-F16 work.

For D7, `RankScope` and `PreparedPoint.embedding_hits/hit_source` replace the invalid
all-token-every-rank assertion. Length tp, integer bounds and sum M are stated semantic
invariants; embedding_local_tokens equals the selected hit. Representative work requires
identical physical extents and hits; equivalent_ranks is the intersection of equal-work ranks
across **all** points, not equality at a convenient single point. Imports are authoritative.
Balanced physical extents, explicit vocabulary padding and KV replication remain mandatory;
A-F12 still refuses comparison projection before calls without prohibiting legal physical runs.

Synthetic assignment is sufficiently specified as an assumption: floor(M/tp), remainder in
rank order, rank0 selected, explicit opt-in and disclosure. tp2/M1 gives [1,0], not [1,1];
tp8/M1 gives one hit on rank0, while tp8/M32 gives four per rank. This makes unequal-hit
inventory points representable without universal gather equivalence. If Javid rejects the
selected-rank extension, those points must be refused and full physical inventory execution
cannot be claimed complete under representative-only support.

What is established about nonselected ranks is limited: the supplied hit vector and the
accepted uniform non-embedding extent rule specify their modelled work. No separate rank
execution or real token placement has been observed. `equivalent_ranks` is conditional on
those supplied assumptions; it is not silicon evidence, inter-rank timing or a proof of an
unseen heterogeneous graph. Arbitrary other nonuniform extents, PP/EP/CP and collectives remain
outside this extension. Semantic conservation/equivalence tests, including a changed second
query point, are planned; the tp1 sample bundle alone does not execute those tests.

D6/D12 have useful independent discriminators in F/conventions.expected.json:

| Choice | Concrete distinction to retain |
| --- | --- |
| Attention/head | n2/L3: full-square 288 matrix ops versus causal 192; all-token head 384 versus last-token 128 |
| KV pages | T1/T17: valid reads 8/136 bytes, allocated pages 128/256 bytes; append 8 bytes; context includes the append |
| Vector/traffic | Versioned abstract algorithms and core/rate/frequency contributors; serialized 2 ps versus overlap 1 ps; GEMM operand traffic 52 bytes |
| Residency/plot | Known weight+KV subtotal 356 bytes is not total peak; total remains null. Per-op isolated durations sum to 18 ps versus aggregate 10 ps |
| Frequency/format | Fixed DRAM at ratio .6 and scalable at 1 allowed; scalable DRAM at .6, core rounding below 1 Hz and nonzero block-scale bytes without geometry refuse |

Format `bytes` is a fixed numeric width checked against the exact format vocabulary, not a
missing SourcedValue claim; I do not raise a hardware-width provenance blocker. Per-operand
precision, half-byte rounding, explicit rate inputs and point frequency must still be checked
by the future implementation. Omitted conversion work, NoC timing, total activation residency,
energy and full physical silicon timing remain explicit limitations, not zero-valued models.

## Public amendments, ownership and remaining human decisions

The public patch explicitly changes U-P3/build-spec/engine/workload statements, U2 exit,
U-P4 display and U3 G2(c). Proposed G2(c) is exact integer same-work fork correctness with
independent resolved-operator expectations, not nominal compatibility under a renamed gate.
Its changed subject and separate U3 cost require Javid's decision. U0001/U0002/U0019 addenda
are new acceptance requests; they do not manufacture historical U1 approval. U0021 adds check
scope only; fresh GitHub WSL2 clone plus hosted Ubuntu CI at the same published commit remains
settled. No new host permission is needed here.

Read-only `git apply --check` passed against integration. Nothing was applied. The public
index's plan/how-it-works hashes are A-base hashes, not final integrated identities; retain
coordinator amendments and record final hashes after integration. The existing coordinator
ownership edits must not be replaced by A's whole base documents.

B confirms the proposed **100–154 person-hours**, conditional on correcting R1/R2 without
scope expansion: prior consolidated 90–138 plus S comparison/report integration 10–16.
R1/R2 belong to already budgeted shared comparison/evidence work; no new increment is claimed
for these narrow corrections. A's 140–222 and fresh independent reviewers' 16–24 are separate:
**256–400 engineering hours**, not elapsed schedule or a delivery commitment. Human active
2–4 provisional hours and unbounded waits are separate. U3 A6–10/B4–6 and U4 A20–32/B8–14
remain separate future planning amounts.

The exact delivery partition is acceptable as a proposed implementation boundary:

- A authors shared `contract/uarch_contract/{comparison,evidence,report_context,registry,exports,assumptions}.py`
  plus listed generated schema mirrors, under human contract acceptance. R1/R2 changes must
  enter that one reviewed boundary. A owns engines/protocol.py and schema mirrors without a
  duplicate contract protocol definition.
- A owns `src/rkuarch/table/artifacts.py::load_verified_report_inputs`, recursive hash/source/
  review/selector closure, preparation/engine/table identity, `contract/tests/nominal_candidate.py`
  and `contract/tests/u2_prepared_adapter.py`. B gets verified companions; it does not derive
  hardware peaks, rebuild graphs or execute physics in the report.
- B owns `src/rkuarch/provenance/{badge,model_card,applicability}.py`,
  `src/rkuarch/report/{render,badged}.py` and the HTML/Markdown templates, plus the exact
  `test_u2_b_*` and `tests/fixtures/u2_b/` evidence/display paths listed in P/delivery.md.
- B owns `contract/tests/u2_comparison.py`, nominal-compatibility/inventory/physical-discrepancy
  report tests, precision matrix/parity tests, and reviewed changes to parity.py/vendor_support.py.
  B owns `scripts/vendor_rk.py`, the component-precision inventory, four `hw/` specs and
  sourcing inventory. Vendor artifact generation/adoption remains human-only.
- Coordinator integrates shared docs/Makefile/CI hunks under Javid's authority. B proposes CI;
  no competing private carrier, parallel hardware authoring or whole-directory overlay.

After R1/R2 are returned in a rehashed proposal, the remaining explicit human choices are:

1. Accept S's exact replacement U2 gate subjects and the proposed null/absent policy, with
   unchanged numerical thresholds and the lost physical full-workload accuracy claim stated.
2. Accept exact shared versions/carriers, export command/projection/loss rules, execution-model
   assumption treatment and synthetic efficiency1.0 proposal; actual npu-l4 input acceptance
   and artifact adoption remain later concrete steps.
3. Accept the narrow U0019 selected-rank extension and opt-in synthetic assignment, or accept
   the resulting unequal-hit capability refusals and revise completion scope accordingly.
4. Decide the individual D6 physical conventions and D12 capability limits; no implicit
   physical correction or hardware tuning follows from selecting S.
5. Prefer default hidden STUB plus explicit labelled prediction opt-in. Visible-by-default
   remains a policy alternative but would require revised exact RenderSpec/demo/public hunks;
   it cannot be accepted as though these bytes implement both defaults.
6. Accept 1008/four baseline, ownership and conditional estimates; decide optional BF16/FP8
   separately. Accept U3 G2(c)'s changed subject and U0021's check-scope addendum explicitly.

These choices are not themselves new blockers. R1/R2 prevent calling this exact package
coherent and complete for that decision; corrected schemas/fixtures/prose, not runtime code,
are the next requested handoff.

## Checks and limits

Actually executed read-only/in-memory checks:

- 81 manifest entries and manifest digest; unchanged prior B report hashes.
- Draft 2020-12 schema validity, 126 definitions, all 38 catalog typed fixtures; 37 self hashes
  and four reviewed-body bindings. No proposal generation script was executed.
- 113 resolved dependency selectors, ten known actual-source values including ps-to-seconds,
  and exact sample fixture/query/component/precision/projection/channel inventory correspondence.
- Nine structural negatives: five explicit precision mutations and four reference-state/value
  contradictions. These are structural checks, not future semantic-validator results.
- R1 in-memory refusal-inventory counterexample; R2 inspection of all four comparison recipes.
- Tiny nominal literals, selected-rank arithmetic, retained component bytes and three loader
  source fingerprints. No upstream counts/durations were evaluated.
- Public patch applicability via `git apply --check`, without application.

A's 18 loader checks and four prompt-sync tests are inspected recorded evidence, not rerun
results from B. Runtime candidate isolation, bridge validation, evidence eligibility, display
nonleakage, independent physical execution/replay, full adopted comparison inventory and fresh
implementation reviews remain planned. Their absence is not a proposal blocker.

Only this new report is written. No A package, accepted policy, runtime, public contract,
hardware or vendor artifact was edited; no public amendment was applied, artifact generated,
UARCH_HUMAN set, dependency installed, agent spawned, commit made or publication performed.
