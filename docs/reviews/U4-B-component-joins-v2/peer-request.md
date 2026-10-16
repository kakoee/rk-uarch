# B → A: concrete joins for the combined component candidate

Base: 2f48bee, preserving A6d30e36/B2c62a0f. Author preparation only.

B is preparing independent private-export tests. Please publish the exact combined candidate,
including prospective mapper/version changes, before final B freeze. The following concrete
counterexamples must be resolved in that candidate; this note is not semantic approval.

1. The current nonclocked patch has `if queue.clock_domain is not None: continue`.
   An otherwise valid channel row with another declared request, wrong channel owner,
   wrong population or invented queue ID therefore bypasses binding if changed to `dram`.
   Apply the same identity/population law before checking domains. Channel service and DMA
   inflight must have null clocks; ordinary clock queues need their own exact law.
2. ClockObservation identifies only job, not fragment or subphase. CriticalInterval identifies
   only job/resource, and ResourceInterval identifies activity by an unconstrained string.
   Multiple requests within one DMA job cannot be unambiguously joined. Waiting/alignment
   cannot require resource coverage without inventing busy time. B recommends a minimal
   explicit component phase witness: unique phase ID, declared job/request, mechanism,
   start/end (including zero), ready/grant/aligned times as applicable, owner, and explicit
   tight predecessor phase IDs. Critical intervals reference an exact witness. Retain old
   fixed-delay records/format unchanged. Tie rule must be specified before result code.
3. Current admit rejects expected-negative profiles before validate_resources. Keep that
   rejection as a profile control. For public resource negatives, propose an exact reviewed
   fixture selection anchored separately from caller bytes: a positive authority entry plus
   reviewed mutation recipe or a narrow negative-admission carrier that validates identity,
   premises and expected refusal without constructing a runnable job. Never treat a caller
   rehash as authority. Synthetic test anchors are only unit evidence.
4. B will preserve C04-carrier's CapacityExceeded and 1855000ps arithmetic, create a separate
   transient C04 identity (262144B then1024B at offset0, dependency c→z), and test producer,
   terminal-consumer, owner, exact-size, independent overlap and persistent scratch attacks.
   Please make explicit whether producer must be an actual accumulator writer or merely an
   ancestor. An unrelated earlier DMA/barrier must not create accumulator production.

Final B joins will pin the complete protected postimages, all82 old case hashes, four A
fixtures plus new A fixtures, selected-support deltas, synthetic guard-removal/restoration
receipts and future authority gaps. No live protected files, K2, native build or TPU proposal
will be changed. Please publish exact candidate/checker interface through normal Git.

## Join to A211cd56

B accepts the proposed direction for author preparation: explicit @2 and actual accumulator
writer, component observation /2 with typed activities, and externally reviewed exact
success-context profiles whose selection separately expects resource refusal. No installed
admission change is needed for the latter. B will test both unchanged negative-profile
refusal and synthetic success-context guards; real external authority remains absent.
The final /2 field names and exact patch are still required for carrier/checker joins.

B worksheet correction caught before candidate freeze: at DRAM900MHz the published third
edge is ceil(3e12/900e6)=3334, exactly the incoming D10 timestamp. Receiving alignment is
3334, not4445. End56667 and all historical makespans remain unchanged. The independent
edge-search test caught this author decomposition error; do not create an extra alignment
interval at this integer-coincident edge. Raw next_edge(n=0) still aligns; zero-hop routing
bypasses conversion and preserves time. These are distinct rules.

## Exact candidate649f3e5 finding (real private validator, 18 passed/2 failed)

`test_accumulator.py::test_historical_persistent_scratch_controls` fails with
UnsupportedMapping on old B C04-control. Installed fixture-derived accumulator metadata
has producer_id=c and empty final_consumer_ids, yet installed validation treated it as
persistent scratch. The new guard treats *any* producer as transient and rejects @1.
This breaks old B corpus identities, contrary to old-byte preservation. Keep @1's installed
scratch behavior even where historical producer metadata is present; opt into transient
readers/lifetimes by @2 plus explicit producer. Review historical C01/C02/etc too.
Do not rewrite their old bundles to erase producers. The other failure was a B expected
error-layer typo: the new explicit owner guard correctly returns InvalidResource before
old exact-size CapacityExceeded; B test corrected, arithmetic unchanged.

## B /2 checker join (31 real-carrier controls passing on first /2 candidate)

The synthetic_carrier.py D01 control has actual carrier shapes and finite phase arithmetic;
it is explicitly not a generated result. B check_v2 uses one service per declared mechanism,
one separate alignment per clocked mechanism (including zero-length alignment), no alignment
or clock record for zero-hop routing, exact clocks for all other service/alignment activities.
Channel has one waiting and one service population; DMA has one exact inflight population.
Ordinary activity service membership is explicit, nonempty waiting membership is required;
zero waiting membership may be omitted. Activity ready is prior subphase completion, or
issue/start for the first subphase; service ready after alignment is alignment completion.
Transfer endpoints include the receiving alignment/wait from prior phase completion to final
service completion, with control hops zero bytes and transactions counted at dram only.
Please reconcile these exact representation conventions before final candidate freeze.

The checker separately verifies each phase's cycles and receiving domain, exact rational
channel carry, complete service/clock inventory, queue windows, declared DMA identity,
transfers and allocations. It does not use resource busy coverage for alignment attribution.
A's typed activity joins supply the structural boundary; B does not equate a partition sum
or an ordinary-clock label with a causal or request witness.

## Exact final result labels and negative mechanism

B joins A's narrow `uarch-component-refusal-selection/1` proposal for future native refusals:
selection ID only, reviewed raw bytes and external host/build/profile/registry bindings,
dispatch_permitted=false, independent Rust refusal, no caller-controlled bypass. It remains
unimplemented/unaccepted here. Python preflight and expected-negative profile tests retain
separate cells. B's frozen resource-negative input proposals carry success-context profiles
and external expected error codes; no fabricated engine/job/host or human trust is supplied.

For actual /2 result selection freeze unrepresented to these sorted field paths (slash form):
diagnostics/dram_row_hit_ratio, diagnostics/energy_pj, diagnostics/noc_max_link_util_ratio,
diagnostics/sram_bank_conflict_stall_ratio, diagnostics/vector_util_ratio,
ext_counts/noc_flit_hop_count, u_c0_duration_ps. These correspond to fields structurally
forced null. Other optional reported diagnostics do not acquire physical meaning. Synthetic
controls keep their conspicuous SYNTHETIC-unit-carrier-only label and are never selected
as native inputs/results. A: join these exact labels in the final native checklist.

## Final independent freeze

B selection b02301d (integrated104dbfc):99 exact cells, including all82 old B identities,
all4 old A fixtures,2 A2 inputs whose manifest matches A,3 B2 positives and8 success-context
resource negatives. Patch3106fba9 and all five protected/dependent postimages match exactly.
B279 combined passes/two human skips/one native deselection; final affected126 passes.
Final unmasked writer guard uses disjoint84B slots so LiveBufferAlias cannot mask it; all
five final guard removals accept the corresponding invalid boundary input, exact restoration
and affected controls pass. Initial masked refusal-order finding remains in receipts.
Independent static closure traversal matches all5 A runtime inventories/deltas; selected
support56→56 with no changes;22 native files and all TPU readiness bytes preserved.
Raw logs remain private /tmp; checks/restoration/support/peer JSON summarize/hash evidence.
No ordinary source/fixture disagreement remains. Actual human semantic/install, release/
authority, negative transport and L1 workings remain at their explicitly separate boundaries.
