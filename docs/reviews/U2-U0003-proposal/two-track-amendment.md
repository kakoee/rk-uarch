# S: two-track validation amendment — review only

Javid selected S for drafting, not acceptance. Existing physical workload count and ±0.1%
duration exits remain operative. This document proposes replacing their subject explicitly.
No result in this package is a run of either proposed model. No gate is discharged here.

## Old and proposed exits

| Obligation | Operative old exit | Proposed replacement, conditional on acceptance |
| --- | --- | --- |
| U-P3 task 4 / acceptance 3 | Actual physical graph passes nominal rk-sim count harness: per fixture/channel total absolute adjustments ≤5%, residual ≤0.5%. | A separate **nominal-rk-compatibility/1** candidate passes the same positive-reference budgets over every adopted fixture. Physical counts instead pass independently specified operator/shard/traffic tests and have a complete discrepancy artifact against every nominal reference. A physical discrepancy may fail while the nominal gate passes; it must remain visible. |
| U-P3 task 5 / acceptance 1; execution-plan U2 | Physical U-C0 aggregate duration equals each fixture's own stored upstream duration within ±0.1%. | Nominal candidate duration, using that fixture's declared component execution model, equals stored upstream duration within ±0.1%. Physical U-C0 timing passes independent hand algebra, conservation, replay and determinism tests. This **replaces**, and does not satisfy, physical full-workload ±0.1%. |
| U0002 unknown channels | Zero requires actual zero; null requires actual null. No zero/null adjustment. Vector not provided. | Keep known-zero rule. Null/absent reference produces `unassessed` with actual retained, never passed or zero. Matching candidate omission may be `modelled_absence`, never numerical validation. Comparable-channel nominal gate can pass while evidence outcome is unassessed. This is an explicit null-policy amendment. |
| A-F12 | Replicated KV/padded vocabulary projection refused before candidate execution. | Unchanged for both comparison tracks. Record all five channels as refused and keep fixture inventory entry, scope and reason. Physically legal execution tests are separate. Other differences cannot be relabelled A-F12. |
| U-P5 / G2(c), inherited U3 | Fork decode matrix counts compared with nominal rk-sim fixtures, residual ≤0.5%, “no single deviation above 5%”. | Fork counts compared with independent resolved-operator expectations for the same captured bundle: B={1,8,32}, context/seq={512,4096}, tp={1,8}, applicable declared precisions. Exact integer matrix counts and preserved rank shapes, no adjustment. Missing/unrepresented matrix work fails. Nominal compatibility and physical-versus-nominal discrepancy retained separately; neither substitutes for fork correctness. Other G2 criteria unchanged. This stricter same-work test is a new gate subject needing explicit acceptance. |
| U0021 listed check scope | Full U2 checks under accepted fresh GitHub WSL2 clone plus hosted Ubuntu CI at same published commit. | Same hosts and publication identity; check list explicitly replaces physical nominal-parity exits with both new tracks and discrepancy completeness. No host or publication reauthorization implied or requested here. |

Compatibility acceptance checks exactly the complete adopted inventory, not only cases where
values happen to match. Inventory carries four count channels plus duration for each fixture,
including missing vector and null decode writes, all component bindings, precisions, queries,
tp and refusal cases. Every component precision refusal also has a separately joined observed
input/trace/boundary/class and match result; A-F12 query refusals cannot substitute for it. Initial snapshot: 864 records; proposed refresh: 1008 successes and four
explicit precision refusals. Actual npu-l4 expectations still require the human artifact
lifecycle. A synthetic descriptor does not supply them. Optional BF16/FP8 adds 144 only after
an explicit supported storage declaration and a separately reviewed matrix addition.

A nominal compatibility pass requires every expected comparable channel within its original
threshold, every known-zero exact, every declared omission matching the model specification,
no unavailable candidate on a positive reference, no unexpected refusal/execution failure,
and exact complete inventory. Expected A-F12 and unsupported-precision refusals must match
before calls. Unknown references are reported as unassessed and excluded from the numeric
predicate explicitly; the evidence outcome cannot be `complete_pass` if any remain.
Duration has no count-adjustment allowance. All signed/absolute/residual quantities are stored
in fractions, not percent. The comparison interface and R1-R2-corrections.md define complete formulas, observation
correspondence and separate evidence/gate reductions. Unavailable actual on known reference
is unassessed and fails the nominal obligation; required not_run cannot establish physical
discrepancy completeness. Count evidence never validates a duration comparison ratio.

## Two models, two identities, no hidden production model

`physical-resolved/1` is A's proposed production analytic model over resolved OpSpecs;
engine remains `analytic`. Its implementation digest, model identity, `resolved-ops/1`,
AssumptionSet and engine version bind every job/result. Table/report must print “physical
resolved-operator prediction” and its actual validation rung. Counts include gather, vector,
KV writes and all declared accesses. Actual execution cannot read nominal expectations or
apply comparison adjustments. Aggregate and per_op are two modes of this same physical model.

`nominal-rk-compatibility/1` is A's **test-only** candidate at
`contract/tests/nominal_candidate.py`, with tests in
`contract/tests/test_u2_nominal_candidate.py`. It is not a selectable CLI engine and must not
be imported by src/. B's `contract/tests/u2_comparison.py` calls its typed pure function in a
separate guarded process with only serialized NominalInput. The candidate may not import
rk-sim, vendor readers, parity fixtures, expected values, the physical producer or OpSpecs.
Tests trap file/network access and prohibited imports during execution. Import/static review
and independent literal expectations detect a lookup or delegation to the oracle. The caller
loads reference inventory only outside that boundary. Candidate inputs cannot carry expected
counts/duration or a fixture ID. Candidate output identities bind inputs and its own source
hash; binding hashes are verified outside the candidate, not used as lookup keys.

Inputs: nominal ModelSpec (unchanged accepted rounded params), explicit compute/KV formats,
query, tp, component binding, selected sourced peak, sourced bandwidth and explicit sourced
ExecutionModelInput. Source rules from the pinned implementation are a specification to
reimplement, not permission to invoke it or feed its frozen counts into a roofline diagnostic.
Let P be active parameters, D width, L layers, B decode batch, T total context, n prefill
prompts, S prompt length, w compute storage bytes, v KV bytes, h=D/n_heads:

- decode matrix = 2PB + 4LDT; prefill matrix = 2P(nS) + 2LD(nS²).
- nominal weight bytes = Pw. KV coefficient k=2L×kv_heads×h×v.
- decode reads=Pw+kT, writes=null; prefill reads=Pw, writes=knS; vector=null/not supplied.
- rank counts use the existing uniform /tp projection only after A-F12. Nominal duration is
  max(global matrix/(declared peak×compute efficiency), modelled global bytes/(bandwidth×memory
  efficiency))/tp. Scalar efficiency declares compute factor and implicit memory factor 1;
  split efficiency must declare both. Use decimal conversions, no display rounding.

Retained 0.55 compute efficiency is preserved verbatim and remains a model contributor.
Proposed new npu-l4 test efficiency 1.0 is an explicit unvalidated assumption requiring
acceptance; it is not derived from hardware, fitted, a fallback or a physical engine input.
No collective/spill/DVFS/vector timing appears in nominal compatibility scope. Named model
and source hashes differ even if particular values agree. Source inspection fingerprints and
safe loader checks are recorded; no new expected oracle duration was calculated here.

Planned nominal tests use independent tiny literals, not the frozen-count diagnostic:
D=4,L=2,P=100,n_heads=2,kv_heads=1,bf16/bf16,tp1,peak=1000 op/s,bw=100 byte/s,
compute efficiency=.5,memory=1. Decode B2,T6: matrix592, reads296,writes=null,duration2.96s.
Prefill n2,S3: matrix1488, reads200,writes96,duration2.976s. tp2 halves counts and duration
(when vocabulary/KV projection is legal). A split memory efficiency .5 changes decode to
5.92s. Perturb P, T, n, S, precision, tp, bandwidth and compute factor separately. Mutants
that read expected values, omit .55, use triangular/full-square physical attention, ignore
memory writes or apply tp twice must fail. These are hand expectations, not executed tests.

## Physical evidence required after acceptance

Run literal GEMM/attention/norm/activation/gather/KV expectations and independent whole tiny
decoder counts for all supported operators; include decoder multiplicity, MoE single expert
expansion, head/tail once and declared omissions. Compare every locally produced dimension
and dependency with literals, then execute both captured local and independently authored
bundles with producer/import trap enabled. Do not test a producer against its own output.

Hand timing cases include 48-op/52-byte GEMM; serial matrix/vector time 2ps versus overlapping
1ps; memory/compute tie rule; aggregate max of sums versus sum of per-op maxima (10ps versus
18ps); fractional ps and seconds conversion; attribution conservation and per_op≥aggregate.
Conventions and discriminating cases are in fixtures/conventions.expected.json. All real
sidecars and inventory queries are captured and executed to produce physical discrepancies;
fixtures requiring A-F12 refusal remain present even though the comparison adapter is not
called. Additional independent physical tests cover those legal replicated/padded graphs.
No physical expected count is regenerated by preparation under test.

D7 replaces the invalid all-token-on-every-rank claim: hits are a supplied integer vector of
length tp, each in [0,M], sum M. tp2/M1 [1,0] conserves; [1,1] does not. Representative mode
requires equal hits and equal physical extents for all equivalent ranks at every point.
Selected-rank mode allows a balanced tensor split with explicitly unequal gather hits and
`equivalent_ranks` exactly those matching selected hits/extents across all points. This is a
narrow proposed U0019 scope extension, not already authorized import support. Imported
counts are authoritative; never re-shard. High-level queries without token IDs use declared
`synthetic_balanced_assignment`: distribute M in rank order, floor(M/tp) plus one for first
M%tp ranks, selected rank0. E.g. tp8/M1 [1,0,0,0,0,0,0,0], equivalent=[0]. Report synthetic
workload assumption. Require explicit selected-rank policy, no silent convenience default.
If this extension is rejected, unequal-hit queries are refused; do not claim full physical
inventory execution feasible under representative-only scope.

D6/D12 are separate acceptance decisions: all-token head, full-square attention default
versus declared triangular causal, abstract vector algorithms/rates, serialized matrix/vector,
once per explicit operand DRAM traffic, valid-token paged reads, append writes, partial
weight/KV capacity checks with total residency null. Scalable DRAM at nonbase core ratio,
frequency rounding to zero Hz, and nonzero block-scale bytes without geometry are capability
refusals. Legal generic contract shapes remain legal. No energy model or full workload
silicon timing evidence is introduced. Passing these tests supports correctness of declared
algebra and replay, at most L0–L2; it is not independent physical duration validation.

## Alternatives retained for rationale

H retains the existing physical gates; the 8B count conflict and duration diagnostic prevent
a credible completion estimate. R seeks an independent compatible physical reference; none
with complete scope is established and its acquisition/validation cost is unbounded here.
S is the selected drafting direction and has explicit added costs in delivery.md. None of
these alternatives authorizes oracle edits, hidden graph corrections, altered nominal inputs
or tolerance increases. Exact package acceptance remains outstanding.

The schema-valid nominal-decode/prefill-input and output.expected fixtures also bind the
complete synthetic export descriptor (2e9 op/s, 1e9 byte/s, explicit efficiency1.0): expected
592 ops/296 bytes/296ns decode and 1488 ops/296 bytes/744ns prefill. They are independent
expected values, not an executed compatibility pass. The separate 1000op/s/.5 examples above
exercise another declared model factor without claiming to use that descriptor.
