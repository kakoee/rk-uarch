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
