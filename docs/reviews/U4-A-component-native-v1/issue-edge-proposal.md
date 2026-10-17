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
