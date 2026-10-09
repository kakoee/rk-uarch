# U2 shared-baseline acceptance package v1

**Decision status: PENDING JAVID.** B reports READY FOR HUMAN DECISION; R1/R2 are resolved
at proposal level. This document recommends acceptance of the identified package, not a
sprint-exit verdict. No implementation is authorized until Javid accepts it.

Decision identifier: **U2-U0003-acceptance-v1**.
Decision-maker: Javid (@jjaffari), acting for both U2 lanes; no Reza approval is asserted.

## Exact material being accepted

Baseline: `1e9e794a84c5173812c23a1cf2fc04b85e6f6831` (main and peeled u01-end).

Proposal root:
[U2-inputs/A-R1-R2-proposal-8def4c6d2c27/](U2-inputs/A-R1-R2-proposal-8def4c6d2c27/).
All 116 payloads are bound by its repository-relative
`docs/reviews/U2-U0003-proposal/SHA256SUMS`, SHA256:
`8def4c6d2c275010719525bc7f39b463675284791122def8c38001889c0ea4d6`.

Final B compatibility report:
[U2-inputs/B-R1-R2-recheck-8dea4be31d5b/U2-B-R1-R2-recheck.md](U2-inputs/B-R1-R2-recheck-8dea4be31d5b/U2-B-R1-R2-recheck.md),
SHA256 `8dea4be31d5baf548fa26fbede7fcf81768ee73355f10f80f5b29a30c4675178`.
Its qualifications and future test obligations are retained, including rejection of invented
matrix omissions and treating injected synthetic scope-MATCH as a test premise only.

Within the proposal root, the normative package includes the U0003 ADR, schema, interfaces,
two-track-amendment.md, comparison-evidence-export.md, R1-R2-corrections.md, fixtures,
delivery.md and the exact proposed public amendment patch/index. Historical probe records
and independent expected fixtures retain their original evidence classifications.
This brief summarizes those bytes; it neither silently changes them nor makes historical
drafting-only statements claim a later human approval.

Key identities for auditing:

| Item | SHA256 |
| --- | --- |
| U0003 ADR | 375662c76695ac0d0f5cbd81a97cfb8bc91c8e0023b2b6b4e1dbaf30e11b5fcc |
| proposed.schema.json | e903f46bc7dc43a26b9824be25a927ae9fb6c3fe035e34d229ee0bfaca21dc64 |
| R1-R2-corrections.md | 8c03dcbc415b6d92185b61639177049b04bb0d9daabce494fb9ead0749fba324 |
| public-amendments.patch | d1239a37b79c05581e1336f8ae1306aeadcd2b95380e57e9e7d84056f61ab017 |
| public-amendments-index.json | 7bdc058fd332510054213b639c4a9b5d551551b0171caba94b6d28eb98eed303 |
| delivery.md | 6015c8afb98502c6f5860fc10c8901b6d79e1ea894c26d96fa025f0fd6402a8d |

## Six explicit decisions — recommended package

Acceptance of v1 means accepting all six recommendations below, including their named
assumptions and limits. An exception should name its item/D-number; affected bytes must be
reconciled and reidentified before dependent implementation.

### 1. Replace the physical-to-nominal gates with S (D8 and null-policy amendment)

Use production `physical-resolved/1` for resolved-operator analytic results. Require
independent operator/whole-tiny-decoder counts, traffic, shard and timing algebra; authoritative
prepared replay with producers disabled; deterministic aggregate/per-op/table/report output;
and complete physical-versus-nominal discrepancy records for every adopted inventory entry,
including refusals and failed comparisons.

Use a separate, isolated test-only `nominal-rk-compatibility/1` candidate for numerical
compatibility with the pinned nominal oracle. It receives declared model/query/precision/tp,
hardware and execution-model inputs; it cannot read expected fixtures, call rk-sim, use a
fixture ID lookup, import the physical producer, or become a selectable production engine.

Retain per-fixture/channel count limits: total absolute adjustment <=5%, residual <=0.5%;
no cancellation/splitting refunds, no unnecessary or zero/null adjustments. Duration retains
+/-0.1% with no adjustment. Known-zero references require actual zero. Unknown/null/absent
references retain actual values and unassessed evidence; only genuine declared nominal
omissions are permitted. Compatibility may pass without complete_pass evidence.
R1's explicit precision observations, verifier refusals and separate evidence/gate reductions
are normative. A-F12 stays a pre-candidate scope guard for both comparison tracks.

**Consequence:** this replaces the requirement that the physical graph itself match the
nominal count/duration oracle. It does not satisfy that old requirement. U2 gains tested
correctness of its declared physical algebra, not independently established full-workload
physical duration accuracy. Physical discrepancies cannot disappear behind nominal success.
L0–L2 evidence still leaves the physical model at stub.

### 2. Accept shared interfaces, packaging and export assumptions (D1–D5, D10, R1/R2)

| Decision | Recommended choice and consequence |
| --- | --- |
| D1 versions | uarch-contract/0.2, uarch-prepared/1, uarch-engine/1, resolved-ops/1, uarch-report-context/2. Keep 0.1 evidence explicitly inspectable; refuse it for new execution/report verification. Unknown future prepared/protocol versions fail closed. |
| D2 authority/export | HardwareSpec and the primary ComponentExport retain complete truth/status/derivation. A distinct hash-bound five-field test projection records losses, original/projected bytes and explicit execution model; it cannot confer provenance on omitted information. |
| D2 efficiency | Preserve retained component compute efficiency .55. Accept 1.0 for the proposed new npu-l4 nominal test model as an explicit unvalidated assumption, not hardware derivation or physical-engine input. Actual hardware input and generated artifact adoption remain later concrete decisions. |
| D3 report packaging | Embed per-op counts/coordinates/scope/result identities in tables; resolve hash-bound companion bundle/spec/card/derivation/evidence artifacts offline. Missing/wrong companions refuse verified report production. Generated HTML/Markdown are standalone. Do not broaden the narrow hardware-cycle echo exception. |
| D4 transport/time | One JSON subprocess boundary with a reusable pure core; nonnegative finite binary64 duration_ps, no analytic integer-ps ceiling. Convert once to seconds in table code. Independent algebra/conservation tests cover fractional ps. |
| D5 state | Declare stateless_roofline. Carry cold/steady state in identities and coverage even if predictions agree; do not invent priming experiments. Experimental errors remain null with zero samples. |
| D10 determinism | No wall-clock timestamps anywhere in canonical reports, including comments. Deterministic build/version identities may appear. |
| R1/R2 shared carriers | Accept the corrected refusal-observation interfaces, complete reduction rules, distinct count/timing recipes and recursive source contributor inheritance. Missing/cyclic/ambiguous/wrong-purpose/incomplete contributors refuse; raw magnitudes without display recipes stay stored but hidden, including opt-in. |

A owns the shared carriers; B consumes the same types and supplies independent tests.
Acceptance approves the proposed interface semantics, not a claim that structural JSON Schema
alone enforces them or that synthetic fixtures have executed future runtime behavior.

### 3. Accept the narrow selected-rank extension (D7/U0019 addendum)

Require a supplied integer gather-hit vector of length tp whose entries sum to token count M.
Representative mode requires equal physical extents and hits across every equivalent rank at
every query point. Add selected-rank support only for otherwise balanced tensor splits with
unequal embedding hits; equivalent_ranks names only genuinely matching ranks.

For high-level queries without token IDs, allow explicitly requested
`synthetic_balanced_assignment`: floor(M/tp) hits each, remainder assigned to low ranks,
selected rank0. Label this as a synthetic workload assumption, never silently enable it.
Imported prepared counts and mappings remain authoritative.

Example: tp2/M1 uses [1,0], not [1,1]; rank0 is not representative of rank1.
**Consequence:** if rejected, unequal-hit points must be refused and the promised full
physical-inventory execution scope must be revised. Acceptance extends U0019 prospectively;
it does not rewrite U1's approval history.

### 4. Accept the individual physical conventions and capability limits (D6/D12)

| Assumption/limit | Recommended behavior |
| --- | --- |
| Head and attention | Standalone prefill uses all-token lm_head; full-square attention is default, triangular causal only when explicitly declared. Preserve the corresponding declared dimensions/counts. |
| Embedding and padding | Gather counts rank-local selected tokens; it is not dense V x D multiplication. Charge physically executed padding only; do not charge allocation padding as valid work. |
| Vector and compute | Use the declared abstract vector operation algorithms/rates; serialize matrix and vector compute in the specified roofline model. These are modelling assumptions. |
| Operand traffic | Charge each explicit DRAM operand read/write once per declared operation; do not infer inter-op retention. |
| KV traffic | Page-granular addressing, valid-token reads and append-only writes. Example with block16: T17 allocates two pages but reads 17 tokens, not 32. |
| Residency | Check known weight/KV capacity components; total peak residency remains null where the model lacks complete live-state coverage. |
| Aggregate/per-op | Aggregate max-of-sums and isolated per-op maxima have different meanings; isolated durations need not sum to aggregate latency. Label plots accordingly. |
| Frequency | Refuse non-base frequency when DRAM scales but no accepted bandwidth curve exists. Fixed-DRAM positive core ratios remain supported subject to positive resolved frequency; refuse zero-Hz rounding. |
| Quantization metadata | Refuse nonzero block-scale bytes without supported geometry. Generic contract shapes remain legal even where U2 engine support refuses them. |

These choices are conditional physical predictions, not hardware evidence or a detailed
schedule/state/energy model. Independent literal tests must exercise each discriminating case.

### 5. Accept conservative evidence and display (D11)

Bind evidence/source/review/order/verification/registry and metric dependencies in ReportContext/2.
Model evidence remains a contributor. Keep purpose, granularity, precision roles and source
scope distinct; count evidence cannot validate duration. Empty claims give a null claim
summary, while an actual stub claim remains a stub contributor. Proposed designs cap at
estimated; missing evidence stays unknown and no deterministic confidence band is invented.

Hide STUB magnitudes by default. Explicit `--show-unvalidated-predictions` permits only
finite executed predictions with complete contributors and adjacent STUB labels on every
numeric surface. Stored raw magnitudes without display recipes remain hidden even then.
Synthetic evaluator fixtures are not actual silicon evidence or evidence of real scope match.
An alternate visible-by-default policy would require revised, reviewed bytes.

### 6. Accept matrix/ownership/planning and prospective scope amendments (D9, delivery)

Proposed refresh: preserve all 864 retained successes and add 144 npu-l4 BF16/BF16 cases,
for 1008 successes. Keep four direct-peak UnsupportedPrecision obligations:
placeholder BF16/BF16 and FP8/FP8; npu-l4 FP16/FP16 and FP8/FP8.
Do not include optional npu-l4 BF16/FP8 +144 without a later explicit storage declaration
and separately reviewed matrix decision. Direct-peak checks do not replace bridge KV checks.

Accept the exact path/callable partition in delivery.md: A shared contract/derive/workload/
analytic/table/CLI/test candidate; B hardware/provenance/report/matrix/comparison tooling;
coordinator shared public hunks. No private duplicate schema, hardware spec or nominal engine.
B's U0004 proposal and its human acceptance remain required before dependent policy is treated
as settled. No fork/native/detailed mapper/U3+ implementation is added to U2.

Accept 256–400 engineering person-hours as a conditional planning range:
A140–222 + B100–154 + fresh independent review16–24. R1/R2 adds no estimate increment.
Human active2–4h is provisional; elapsed waits are unbounded separately. These are neither
incurred hours nor a calendar commitment. Re-estimate after concrete hardware/source inventory.

Accept the prospective U3 G2(c) subject change: fork decode matrix work compared with
independent exact integer expectations for the same captured bundle, no count adjustments,
across B={1,8,32}, context/seq={512,4096}, tp={1,8} and applicable declared precisions.
Keep nominal compatibility/discrepancies separate and other G2 criteria unchanged.
Indicative U3 extra A6–10/B4–6h and previously separate U4 A20–32/B8–14h are future scope.

Accept only U0021's listed-check scope addendum for the two tracks. Its already accepted
fresh GitHub WSL2 clone plus hosted Ubuntu CI on the identical published commit stays intact.
No WSL2 simulator-performance approval or U3/later hardware waiver is added. U0020 stays
historical and unchanged.

## Evidence supporting readiness and limits

B independently verified the 116-entry current package and 81-entry parent, schema/self-hash/
review bindings, observed precision-source correspondence, R1 reductions and seven R2
dependency mutations. Its report records 63 typed payloads, 62 self hashes, eight reviewed
bodies, 13 materialized R1 pairs, five channel cases, 20 source recipes, 60 matching-purpose
edges, 261 selectors and 30 ratio recipes (22 count, eight timing).

Coordinator verified B's supplied digest, all three preserved proposal manifests/payloads
(36/81/116), existing coordinator manifest, worktree HEAD/status and tracked whitespace.
The exact public patch passed git apply --check against integration; it has not been applied.
The coordinator reviewed B's findings; these are not a claimed independent rerun of every B
probe. Main is clean and all U2 HEADs still equal the stated U1 baseline.

Actual engine/candidate/renderer execution, real npu-l4 generation/adoption, complete U2 exit
checks and later independent implementation reviews remain outstanding. Proposal readiness
does not certify physics, runtime correctness, performance or sprint completion.

## What an approval authorizes next

1. Record Javid's exact decision and identified bytes, maintaining the preserved proposal and
   historical approvals. Prepare the reviewed shared baseline for A/B, apply only the accepted
   public hunks in integration, retain existing coordinator edits and record combined hashes.
2. Prepare precise A/B implementation handoffs against that common authority, with independent
   acceptance expectations/tests first. Any new shared-interface/policy deviation returns for
   explicit disposition. No dependent work proceeds on a partial or ambiguous acceptance.
3. Prepare reviewable local checkpoint file lists and commit messages. Commit is a separate
   step from approval of this proposal; push is separate from commit. No development-branch
   publication or mandatory PR is introduced.
4. Follow the human artifact lifecycle later: freeze reviewed tooling/inputs, Javid generates
   twice, compare the entire revision, obtain separate explicit adoption. No UARCH_HUMAN bypass.
5. Complete both fresh independent Stage1 -> author Stage2 -> original reviewer Stage3 loops,
   all applicable exits, approved main integration/publication and same-published-commit
   U0021 validation. Tag on main at approved closure; preserve workers through verified
   publication. U2 closure is not U3's G2.

This approval does not itself commit/push/tag, adopt generated artifacts, approve actual
hardware inputs or close U2. All current records and preserved copies are uncommitted local
files; hashes do not provide Git history or off-machine backup.

## Suggested decision reply

“I approve U2-U0003-acceptance-v1, all six recommendations and their explicit D1–D12,
R1/R2 and public scope amendments, for proposal manifest
8def4c6d2c275010719525bc7f39b463675284791122def8c38001889c0ea4d6.
Proceed with recording acceptance, the common baseline and implementation handoffs.
Keep commit, push, artifact adoption and sprint closure separate.”

Alternatively, name the numbered item/D-decision to change. Until a reply arrives, status
remains PENDING JAVID; no silence or elapsed time constitutes approval.
