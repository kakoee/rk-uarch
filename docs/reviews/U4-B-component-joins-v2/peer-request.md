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
