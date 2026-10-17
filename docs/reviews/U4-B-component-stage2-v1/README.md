# Component Lane B — consolidated Stage 2 response

Author correction/preparation for reviewer F1–F11. **Applied means corrected in the exact
unapplied proposal, with tests; it does not mean installed, independently accepted or closed.**
No blocking finding is rejected or deferred as an author correction. Javid's semantic and
installation decisions remain pending. [A's companion response](../U4-A-component-stage2-v1/README.md)
and [shared interface](../U4-A-component-stage2-v1/interface.md) complete the joint handoff.

The exact combined patch is
`sha256:81b81c6c2680a17e7d106dedb4a11dc07891b331f3323319fb0192b852bdebe3`;
[23 pre/postimages](../U4-A-component-stage2-v1/combined-postimages.json) include code, three
schema mirrors, normative text, discoverable tests and stable helpers. B's
[12-path delta](b-candidate.json) is [unapplied](b-candidate.unapplied.patch). Apply the combined
patch only in a private reconstruction for verification. Its preparation base and immutable
activation inputs are pinned separately to avoid a selection↔patch hash cycle.

The [106-case selection](execution-selection.json) hash is
`sha256:4b9e73cf9ef11456e216acba58c9496c242169e2a40efcf0aa9e3f36bf0dbbc0`.
It preserves all old 99 rows and 13 fixture files, with explicit old→new identity mapping;
seven new inputs add three valid controls and four unmasked lifetime refusals. Totals are
90 prospective result cases, 12 resource-preflight refusals and four profile refusals.
All engine/build/authority/job identities remain null; native status is `not_run`.

## Finding dispositions

| Finding | Disposition in proposal | Independent B evidence and exact responsibility |
| --- | --- | --- |
| F1 | APPLIED | Required service inventory drives channel/port/matrix laws before occupancy joins. M4b and both missing-port/overlap counterexamples accepted before correction and now refuse. NoC positive-hop occupancy is explicitly overlapping latency bookkeeping, still proposed for human acceptance. |
| F2 | APPLIED | Independently derive complete eligible sequence/dependency/acquisition/credit sets, then require equality. V1/V2 and off-chain omission refuse. A structurally eligible first/last credit forgery under cap=2 passes the carrier and fails B because capacity was never exhausted. D05-one, zero links, D14 and barrier controls pass. |
| F3 | APPLIED, shared with A | B supplies consistent M1/M2/M3 carriers and independently executes C1's genuine two-zero-node cycle. A owns the 46→59 structural guard matrix: 42 unsafe-admission controls and 17 explicit redundancy/structure/totality dispositions. B independently proves C1 still refuses after removal of the whole cycle pass; a message change is not a behavioral kill. |
| F4 | APPLIED | Independently anchored A1/A3b/A3c plus disjoint writer controls reach InvalidDependency with intended detail. Each becomes an unsafe admission with its essential guard removed, then passes its restored refusal/control. Equal footprints prevent capacity masking. |
| F5 | APPLIED | [Guard matrix](guard-matrix.json) covers all 55 historical guards and the corrected 69 main-checker plus 11 transition guards by semantic invariant. [Receipts](restoration.json) show 33 actual unsafe-acceptance invariant experiments, including explicitly grouped redundant defenses; four protected lifetime experiments are separate. Identity tests never count as behavioral kills. |
| F6 | APPLIED | All B behavior tests/helpers install under validation/component; A tests install under contract/tests/mapped and tests/unit. The historical 55 B carrier/lifetime tests also migrate to ordinary discovery. No doc-sibling helper imports, missing-file skips or conditional waivers. /2's historical fingerprint binds archived exact bytes; /3 binds current files. |
| F7 | APPLIED | New selection adds B3-false-writer-disjoint, B3-terminal-partial-A1, B3-use-before-A3b and B3-use-unordered-A3c. Original masked negatives remain unchanged refusal-order controls. Wrong-owner defense is redundant with admitted compute/core/size constraints; it is not claimed as an essential unsafe-admission kill. |
| F8 | APPLIED | Independently bind job owner, release=0, dependency readiness, first/last endpoints and event kind/job/owner/time. /2 legacy job blockers are empty and critical predecessor is null, explicitly unrepresented. Fully resealed field attacks fail. /1 helper bytes remain unchanged. |
| F9 | APPLIED | Executed reversed tied-ready D08 grants: r01 [59000,60000), r00 [60000,61000) previously passed both validators. Correct order is r00 then r01. New FIFO guard kills this forgery although makespan remains 61000. Separate nonoccupying overlap yields two [59000,60000) intervals and also refuses. |
| F10 | APPLIED | Reverse-ID uniform 256³ example independently confirms 14 moved operand offsets, no transient accumulators or added dependencies, and different @2 graph identity. Default @1 equals explicit @1. A's exact proposed text now states topological placement of all operands. |
| F11 | APPLIED preparation; human choice PENDING | Independent /1 relabel admits with unchanged graph/point/profile and changed bundle. Proposed /2 tests cover component and transport scopes, exact policy tuple, and refusal under the old external profile anchor. [P2/P1 decision](../U4-A-component-stage2-v1/profile-decision.md) distinguishes profile promise from separate whole-bundle selection binding. No old anchor is rewritten. |

## Evidence and reconstruction

[Independent workings](independent-workings.md) retain C04 1855000 ps and useful work/traffic,
receiving-clock alignment, rational carry, waiting/occupied separation, overlap, zero-hop,
credit and barrier derivations. [Peer joins](peer-join.md) record exact exchanged inputs and
routine fixes. [Development corrections](development-corrections.json) retain masked attempts,
setup/type/fixture mistakes and their corrected controls; none are counted as discrimination.

[Checks](checks.json) distinguish executed B evidence from A's single final combined run.
[Evidence manifest](evidence-manifest.json) binds original retained logs in
[evidence.tar.gz](evidence.tar.gz). Counts from overlapping selections are not additive.
The [fault runner](fault_controls.py) uses only private mutations, requires DID NOT RAISE
from the behavioral assertion, restores bytes in finally, and reruns affected tests. Grouped
controls remove all named defenses of one invariant; they are not per-line mutation scores.

The [final audit](final-audit.json) independently computes 56 selected support files and an
empty actual support delta. Five runtime import inventories/deltas match A exactly; mapped.py
changes those runtime identities. All 22 native source files, sealed original K2 mapped.py,
and original K2 release/selector hashes remain unchanged. U0002 human generation is not
required by this candidate's support delta; that grants no protected-install permission.

## Remaining human and execution decisions

Javid must decide the exact proposed NoC occupancy convention, /2 causal/field semantics,
P2 profile promise versus the bounded P1 alternative, and protected installation of the whole
reviewed code/schema/text/test package. A later installation must reconcile both U0011 streams
at their exact preimages. Separate future component engine/build/host and authenticated
selection/profile bindings are absent. The proposed case-ID-only immutable D3 resource-refusal
transport remains unimplemented and needs its own exact reviewed authority/mechanism; profile
refusal, stale hash, positive synthetic unit anchors and real resource negatives stay distinct.

H-L1-GEMM-01 and H-L1-DMA-01 remain pending actual human workings at L1 acceptance. The six TPU
proposal files and all 70 rows retain their 2c62a0f bytes. No measurement, purchase, reference
placeholder or extra tool search was performed; reference access does not gate bounded npu-l4
implementation. Native build/job, protected installation, authority placement, artifact adoption,
positive badge, G3a and U4 closure remain outside this task. The same independent reviewer,
not either author, adjudicates this response.

The exact future consumer join is recorded in [first-use-bindings.json](first-use-bindings.json).
Revision /3 retains the immutable historical selection's `observation_contract` by its exact
selection hash; the file repeats that value for clarity and binds its source. It is passed
explicitly to assert_case→consume→real validate_result plus independent check_v2. This adds
no authority, native output or fallback to missing accepted engine/build/host inputs.
