# Unapplied proposal: DMA issue-edge observation

The admitted component slice is incomplete for this edge. No protected file or historical selection is changed by this proposal, and no execution authority is granted.

## Observed counterexample

`native/crates/uarch-engine/testdata/synthetic-issue-core-gap.json` is a new private synthetic profile/2 input, case `SYNTHETIC-issue-core-gap`, job hash `sha256:0e62965b0a905d86e3ffbfadd459cf44bd281476a658b546c63eec0bd52b3250`. A zero-hop unicast at0 precedes a32-cycle barrier on the1.2GHz NoC. The barrier completes at26667ps; its dependent read must issue at27000ps on the1GHz core.

Installed Python job/resource/completeness admission and native admission accept the input. Native execution returns `IncompleteObservations: activity requires actual tight earlier cause`. This is an observed post-execution result-construction refusal, not an early resource refusal or a successful /2 result. The candidate receipts bind the exact test/source. The original D09 input remains unchanged.

E4 requires that core-edge delay. The installed /2 inventory starts reads at request_noc and writes at write_port, at issue time. It contains no activity covering26667–27000ps. Linking the barrier directly to the request at27000 would be untight; changing issue/readiness or inventing a busy interval would violate the installed laws.

## Proposed direction, not installed

Add an explicit nonoccupied core-domain `dma_issue` alignment and zero-duration issue service in a prospectively versioned observation contract. Owner: the flattened DMA engine. Category: memory. Alignment records the actual next_edge(core, eligible_ps,0) call after dependency/credit eligibility; service records actual credit acquisition and issue at that edge. It consumes no payload-port bandwidth and adds no finite issue-rate cap. All eligible requests still issue in canonical engine/request order, retaining credits through commit/ack.

The alignment readiness is job readiness; its actual start follows true dependency/credit eligibility and carries all tight causes. Its service and the existing first transfer phase have immediate sequence links. Inflight/credit-acquire/issue begin at issue service, not earlier alignment. Transfer boundary entry stays at the first transfer phase readiness. Job start includes the first issue alignment. Inventory, endpoint kinds, clocks, finite queues, cause eligibility and critical ties must change together.

A concrete endpoint proposal is TASK_READY/DEPENDENCY_READY for alignment and TASK_READY/DMA_ISSUE for service. Exact naming/version/endpoints require human review and installation; do not silently extend /2 or relabel historical receipts. New source/model/contract and later authority must bind the chosen version. No hardware parameter or workload IR is added.

## Acceptance still required

Freeze read/write controls after non-core-edge barrier/unicast completion, with exact alignment intervals, issue edges, traffic and attribution. Add available/exhausted-credit ties, multiple engines, zero alignment and all-ready unlimited issue. Removing alignment, issuing before eligibility, adding a finite issue cap or omitting tight causes must fail. Restore exact bytes and replay debug/release. B must independently review inventory and cause derivation.

Keep this admitted counterexample/refusal as historical evidence. Exact protected semantic/schema/checker installation is needed before claiming this edge complete. Root placement, actual selector/profile authority and public campaign remain separately unauthorized.

## B review refinement: pending issue reservations (unapplied)

B's published `U4-B-component-native-audit-v1/peer-join.md` independently confirms Python admission of the gap input and requests precise pending-alignment credit semantics. The following is an explicit proposed state transition, not a new installed law or an executed implementation.

For each DMA engine track acquired credits and pending issue reservations separately. At dependency eligibility, select requests by the installed ready-time/request-ID order and reserve only while acquired plus reserved is less than the engine limit. Reserve one future issue slot per selected request before scheduling its core alignment. A reservation prevents a second request from claiming the same capacity; it does not increment observed inflight population, publish credit_acquire_ps, occupy a DMA payload port, or invent busy time.

At the scheduled core edge, atomically convert that request's reservation into an acquired credit and emit DMA_ISSUE. The inflight interval and credit_acquire_ps begin at that actual issue edge. Commit/ack releases an acquired credit. Phase-0 completion releases occur before phase-2 issue/grant selection at the same time. Remaining eligible requests receive reservations in canonical order; all available credits may issue at the edge, with no additional finite issue-rate cap. Engines retain independent credit pools. A timing-overflow refusal must leave no successful partial output or leaked reservation.

The proposed dma_issue alignment records the interval from actual eligibility/reservation to the actual core edge, with dependency or releasing-credit causes only when tight. Pending reservations belong to waiting/issue-alignment state, never the existing inflight population. A new observation version must define that population and its endpoints explicitly. Job-start/allocation semantics must also be reviewed against the new alignment phase rather than silently inherited from /2.

The discriminating cap1 case is two simultaneously ready requests at a non-core edge: exactly one pending reservation, zero inflight before the edge, one acquisition at the edge, and no second reservation until the first request releases. Pair it with cap2, independent engines, a release exactly at the issue edge, dependency readiness before/after that release, read/write paths, and zero alignment. B must review these proposed rules and their literal controls before any protected semantic/schema/checker installation.
