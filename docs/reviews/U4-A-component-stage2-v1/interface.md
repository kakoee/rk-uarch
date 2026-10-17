# Stage 2 shared semantic proposal — A interface revision 1

For B's independent implementation and review. This is proposed `/2` semantics, not an
installed contract or an accepted new model law. Base main: 9bd965a; previous candidate:
df3cde6, patch 3106fba9…a9b3b9. Historical packages and `/1` retain their bytes.

## Phase table (F1, F8)

All alignment records are nonoccupying, with the same owner/category/receiving domain as
their service. Alignment dispatch/completion kinds are TASK_READY / DEPENDENCY_READY.
No alignment exists for channel service or zero-hop NoC. Each service has these properties:

| Subphase | Owner | Category | Domain | Occupies | Dispatch / completion event |
| --- | --- | --- | --- | --- | --- |
| compute_overhead | matrix:core | overhead | core | true | OWNER_GRANT / COMPUTE_DONE |
| compute_stage, compute_wave, compute_drain | matrix:core | compute | core | true | OWNER_GRANT / COMPUTE_DONE |
| read_port | dma_port:core | memory | core | true | OWNER_GRANT / DMA_DONE |
| write_port | dma_port:core | memory | core | true | OWNER_GRANT / MEM_RESP |
| channel_service | fragment channel | memory | null | true | MEM_REQ / MEM_RESP |
| dram_latency | fragment channel | memory | dram | false | MEM_REQ / MEM_RESP |
| request_noc, response_noc, unicast_noc | local/source router | noc | noc | hops > 0 | NOC_HEAD / NOC_TAIL |
| ack | dma_port:core | memory | core | false | TASK_READY / DMA_DONE |
| barrier | canonical barrier owner | sync | noc | false | SYNC_ARRIVE / BARRIER_RELEASE |

Occupancy is determined from declared phase/route, never from claimed duration. Compute and
ports have an occupied row even for zero duration. Positive-hop NoC occupancy reports the
union of in-flight router-attributed latency; it does NOT serialize hops or introduce a
bandwidth resource. Zero-hop service remains a nonoccupying zero-duration causal record.
This explicit NoC convention needs human semantic acceptance with D1. B must check channel
and port arithmetic/arbitration directly over service activities even if a row is omitted.
Structural checks independently require the exact occupied-row bijection. Rational channel
endpoints remain on those mandatory rows; published integer endpoints are their ceilings.

Event references require exact job/owner/time/kind joins, separate dispatch and completion
ordinals, including zero duration. Every event must be referenced by a phase endpoint; no
unconstrained STAT_SAMPLE records. Global event ordering remains the existing observation
order law. The phase value retains its scheduler ordering role; it is not a substitute for
endpoint kind. B should flag any conflict with E3/E4 before depending on these encodings.

## Transitions and structural eligibility (F2/F3)

Phase sequences: compute overhead→stage→wave→drain; DMA read request_noc→dram_latency→
channel_service→response_noc→read_port; DMA write write_port→request_noc→dram_latency→
channel_service→response_noc→ack; unicast and barrier each have one phase. Expand each phase
as alignment then service when alignment is present. Phase identities must be unique per
(job, request, subphase, kind); B independently requires the exact admitted inventory.

A `sequence` link is only from the immediate preceding activity in this expanded sequence.
A `dependency` link is from a terminal activity of a declared predecessor job to a first
activity of the dependent job (for DMA, a request's first activity), with predecessor end
also equal to predecessor job completion. A `credit` link is only from a different request's
last activity to a request's first activity on the same DMA engine. A `resource` link has the
same owner, an occupying predecessor and a successor occupying service or its receiving
alignment; only matrix, port and channel owners are contended. No NoC resource links.
All links remain tight (predecessor end = successor start), with preceding completion ordinal
no greater than dispatch ordinal. Cycles, including zero-duration multi-activity cycles,
are refused. Nonzero-start activities require a tight cause even off the critical chain.

Structural eligibility is necessary but not sufficient. B derives the COMPLETE tight cause
set from transitions, declared dependencies, actual previous resource occupant and exhausted
credit release. Merely sharing engine/owner/time is insufficient. Credit completeness uses
issue/release state at the engine limit; first/last eligibility alone does not prove exhaustion.
Resource causes must actually gate the grant, and cannot be borrowed from a later activity.
Preserve same-time ties and zero-duration links. Canonical chosen path uses existing stable
(owner, job, request-or-empty, subphase, activity) order among eligible causes.

## Job summaries and legacy fields (F8)

Canonical job owners: Compute matrix:core; DMA dma:core:engine; NocTransfer source router;
Barrier barrier:job. Component tasks declare no delayed release: release_ps MUST be 0.
ready_ps is max declared predecessor job completion (0 with none); start/end are min first
activity start / max final activity end across that job's request sequences. DMA summaries
also join issue/complete records. Job readiness may precede credit acquisition.

The `/1` scalar causal fields cannot express `/2` activity/request transitions. In `/2`,
job.blocking_predecessor_ids MUST be empty and critical.predecessor_id MUST be null. They
are explicitly unrepresented; typed activity.predecessors is the causal witness. `/1`
meaning/validation is unchanged. No new schema field is needed for this decision.

## Placement, arbitration and admission (F9–F11)

Preserve `@2` min-ID Kahn topological placement of ALL SRAM/HBM operands, not only mixed
accumulators. Prefix IDs remain sorted op IDs. On each heterogeneous core, transient exact
accumulators share offset 0 and matrix jobs are explicitly chained in that order. Uniform
cores retain persistent equal-footprint scratch; reverse-ID dependencies can still move
operand addresses. `@1` continues the old ID-order placement byte-for-byte.

Ports use existing E4 ready FIFO ties (ready time, flattened DMA engine ID, request ID).
No new timing law is intended. B independently verifies this against E4 and tests the grant
order, not merely no-idle-gap and exclusivity.

F11 is a human decision, not yet selected. Recommended: NEW component test admissions bind
mapping policy through a versioned test-profile entry, with exact policy name/version/depth;
legacy profile entries retain graph/point-only promises, including existing K2/@1 anchors.
An outer job/request hash alone is not this profile promise. A will publish exact alternative
schema/code/tests and migration text; no component authority is activated by this proposal.

## Durable activation and ownership (F6)

A proposes `contract/tests/mapped/test_component_observations_v2.py`,
`contract/tests/mapped/test_component_lifetimes_v2.py` and
`tests/unit/test_u4_component_mapper_v2.py`, plus explicit stable synthetic helpers.
B should supply exact checker/helper/test paths under `validation/component/` or `tests/`,
with any uninstalled-carrier-dependent additions in an unapplied patch. A assembles all bytes
into one final candidate; B freezes a NEW selection and independently audits final joins.
Normal default discovery must collect the tests without docs copies or conditional skips.

## Peer join 2 — B 88c3036

Agree B's resource-acquisition refinement: resource causes only at first compute alignment
(whole-tile matrix acquisition), port alignment, or channel service, from a different
job/request. No duplicate same-tile sequence/resource causes. Tight ties at acquisition
are included. B derives exhausted-credit state and full transition causes independently.
The intermediate A patch now enforces these structural boundaries and all earlier field
rules; 67 targeted A regressions pass on the private reconstruction. It includes durable
A tests importing B's announced `validation.component.synthetic_carrier` path, which B's
helper patch supplies. This is not yet the combined installation candidate.

Endpoint-kind binding makes distinct dispatch/completion event identities necessary even
at zero time. Therefore tight ordinal edges strictly increase: a valid final `/2` witness
cannot contain a cycle independently of the explicit DAG guard. C1 will retain an explicit
two-activity cycle diagnostic/control, but its final DAG guard is now intentionally redundant;
we will not claim that a later ordinal refusal is a behavioral mutation kill for the DAG rule.

F11 concrete proposal is now [profile-decision.md](profile-decision.md). P2 supports both
component and transport_fixture B scopes. Legacy profiles and B historical/new proposal
fixtures need not be rewritten while this human choice is pending; label their current
profile/1 promise honestly. P2 additions will be included in A's next exact patch.

## Peer join 3 — B daac675

A reconstructed B's seven-path candidate (patch 8fa0bc58…ca2) alongside the corrected A
source. The 90-test join passed, including B's 38 checker tests, seven independently anchored
lifetime tests and A's current structural selection. A's later 24 structural boundary tests
also pass; counts overlap, not additive. B's disjoint writer and partial-terminal inputs
reach the stated InvalidDependency layer independently of negative-profile short circuits.

Ordinary integration correction for B: durable contract tests import the new synthetic and
consistent carrier helpers, so normal `mypy --no-explicit-package-bases contract/tests`
follows those helper modules. Please include function annotations (Any at deliberately loose
synthetic dictionary boundaries is sufficient) and explicit empty-list annotations in both
helpers in the final B postimages. No type-check waiver or discovery exclusion is proposed.
A's production source typecheck passes 88 files; this remaining imported-helper issue is not
a semantic or authority dependency. A is completing the 59-guard structural matrix and
final exact patch including profile/2 support and its two additional schema mirrors.

## A exact candidate revision 4

`a-candidate.unapplied.patch` now includes the final proposed phase/causal/field rules,
explicit @2 operand placement wording, recommended (unaccepted) P2 profile support, its
NativeTestProfile/MappedEngineJob mirrors and durable profile tests. A's contract tests are
`test_component_semantics_v2.py`, `test_component_lifetimes_v2.py`, and
`test_component_profile_v2.py`; mapper/replay tests are `tests/unit/test_u4_component_mapper_v2.py`.
The historical shell tests were migrated onto B's durable D01 synthetic carrier, retaining
queue attacks and restored positives without a docs-only helper or runtime file copying.

The 59 structural `require` guards are being dispositioned as semantic invariants or explicit
redundancy/totality checks. Current controls demonstrate unsafe acceptance on removal of
38 distinct essential guards; three further targeted witnesses and two lifetime rules are
being checked separately to avoid earlier error-order tests masking them. Cycle deletion
alone can cause nontermination in the Kahn loop; that is NOT counted as unsafe acceptance.
Removing the whole cycle pass still leaves endpoint/eligibility rejection, which is an
explicit redundant-defense disposition. The real C1 test has TWO zero-duration nodes.

B may now freeze against these A postimages, subject to any concrete join corrections.
Please preserve full accepted component scope, including barrier/unicast/zero-hop controls,
and the default-discoverable selection integrity test when supplying the final delta.
