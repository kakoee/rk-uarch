# Exact gaps and prospective decisions

No protected change is applied. These are input/model-stage prerequisites, not permission
to change installed schemas, assumptions, selected support or campaign source.

**G1: explicit accumulator lifetimes.** Installed `validate_resources` derives buffer
readers from compute X/W and transfer sources only; accumulator final consumers must be
empty. Its alias rule requires nonempty final consumers before a later producer. Thus two
successive, dependency-ordered different-size accumulators cannot share physical storage.
A reproducer uses M256/K256/N255 then M256/K256/N256: each alone fits262144B, combined
persistent allocations require523264B. The mapper currently refuses this with named
CapacityExceeded. Identical footprints use one persistent scratch buffer; sixteen maximum
shape ops succeed with four core-local scratch buffers. This is an explicit carrier-driven
limit, not a claim that all possible1–16-op heterogeneous collections map successfully.

Exact before/after: [accumulator-lifetime.proposed.patch](accumulator-lifetime.proposed.patch)
adds compute readers **only for accumulator buffers with explicit producer_id** and requires
that producer to be the current compute or its ancestor. Existing producer=null persistent
scratch stays unchanged. Existing generic final-consumer and ends_before alias checks then
permit transient reuse only after the final compute. Patch pre/post source SHA256s are in
protected-preimages.json. No Pydantic field/schema shape changes are needed. New transient
fixtures/graphs/profiles must have new hashes; do not silently rehash installed fixtures.
After human semantic/protected-source acceptance, the mapper can emit dependency-ordered
transient allocations under a prospectively versioned producer/mapping decision. Current
ws-rowsplit@1 bytes must not silently change. Additional installed policy-version admission
would require a separately exact literal change; this patch does not grant it.

Proposed U0011 addendum text (unapplied): “B accumulator producer=null denotes a persistent
scratch allocation shared only by exclusive matrix-owner jobs with an identical footprint.
An explicit compute producer starts a transient allocation; all compute users are lifetime
consumers, and physical overlap requires the previous final consumers to precede the next
producer. A changed mapping strategy requires a new admitted policy version and producer
identity. No K split, spill, numerical precision or timing law changes.”

**G2: incomplete-input validation.** Installed admission permits a two-byte DMA to populate
a thirty-byte X, a cold compute without its output write, and a barrier with a matrix owner.
The three tests-first failures are retained in completeness-red.log. The new owned consumer
`validate_component_completeness` adds full-range input production, exact cold-output byte
coverage and canonical barrier owner joins **after** installed `admit`/`validate_resources`.
It does not broaden admission. Exact installed before: range≤buffer size, source/predecessor,
destination producer and buffer readers; no equality to complete operand/output or barrier
owner. Exact after: producer.destination=(operand,0,operand.size_bytes); cold output write
source ranges partition[0,Y.size_bytes) once; barrier.owner_id=canonical_owners[barrier:id].
A protected consolidation can move those exact guards after human review; until then Rust B
must implement them independently and fixtures must reach these guards after resealing.
No schema field additions or waiver are necessary. The public native K2 source is untouched.

**G3: observation binding and clock-domain decision, before B output.** Existing carriers
already hold exact service ratios, byte boundaries, request identities, queues, allocations
and critical intervals. No new general observations schema is justified merely by missing
handlers. `ResourceInterval.activity` lacks an explicit request field; freeze the proposed
exact encoding `dram_service:<request_id>` (and `dma_port:<request_id>`) so twelve fragments
inside one DMA job can be joined without position inference. Generic job labels are
insufficient. Freeze `TransferObservation.boundary_id` for issue, channel and destination
commit separately; no implicit double-counting of one packet as independent NoC work.

The component branch of installed `validate_result` currently demands every queue record's
clock_domain be non-null. Channel rational-service and credit-inflight populations are not
clocked queues. Proposed exact replacement of that branch's clock check:
`all(q.clock_domain is not None or q.queue_id.startswith(("channel_service:",
"dma_inflight:")) for q in records)`. Those two names must respectively bind a declared
channel owner or DMA owner and their request populations; other null domains refuse.
No schema shape change: QueueObservation already permits null. Do not label rational service
as DRAM-edge service just to pass. This semantic validation change needs exact human approval
and independent positive/wrong-owner/wrong-population controls before component results.

Causal blocking requires request/subphase identity when several requests of the same job
contend. Before B release, freeze whether the existing activity/boundary conventions plus
ordered event observations establish that join unambiguously; if not, propose explicit
request/phase fields under a new component observation version while preserving K2/v1.
No structural field extension is assumed in the supplied tests. Missing causal proof stays
unverified, never fixed by a plausible partition or expected totals.

**Lifecycle.** The measured selected generator inventory excludes
contract/uarch_contract/mapped.py (and the owned mapped loader); hardware.py is selected.
The two supplied patches alone therefore predict no selected-support change. Recompute the
actual complete postimage closure at acceptance; do not require a generation cycle merely
because a protected file changed, and do not waive a real changed support edge. Any additional
selected change requires the minimal exact delta and normal source/freeze/generation/adoption
lifecycle. This package installs neither patch and performs no generation/adoption. The
published source/artifact pair remains valid. Exact human protected-source/semantic acceptance
is still required independently of whether selected support changes; mapper authorization
does not authorize these amendments or component builds/execution.

[nonclocked-queues.proposed.patch](nonclocked-queues.proposed.patch) supplies the exact G3
validator delta, including the owner/request/population joins omitted from the shorthand
expression above. `channel_service:<channel_id>` allows waiting/service, tied to the
fragment's declared channel; `dma_inflight:<flattened_engine_id>` allows inflight only,
tied to the fragment's DMA engine and canonical owner. Other null-domain records refuse.
Before/after hashes are in queue-proposal-preimages.json; read-only apply check passes.
No schema field change and no old fixed-delay result change. Positive and wrong-owner,
wrong-request, wrong-population controls must accompany real B observations on installation;
this preparation does not fabricate completed component results to declare those tests passed.

**G2 access precondition:** installed validate_prepared_op indexes operand_access by each
required operand without first checking its keys. A hash-valid component missing X access
therefore leaks KeyError. The exact owned before-admission precondition is now
`all(set(op.operand_access)=={"X","W","Y"} for op in bundle.scope.ops)`; failure is
`InvalidCoverage: operand access`. It is applied in both assembly and saved loading before
installed resource validation. No new accepted input or protected change follows. The
installed general PreparedOp helper may later consolidate this check under its own scope;
no full-model schema expansion is included here.
