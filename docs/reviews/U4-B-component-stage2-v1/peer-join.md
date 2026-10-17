# B Stage 2 interface work in progress

Base 9bd965a; review input digests verified in inputs.json. Historical 99 cells, 13
fixtures and checker evidence stay immutable. B is preparing a disjoint unapplied patch
for validation/component/observations_v2.py, durable synthetic_carrier.py and test modules
under validation/component. The historical selection integrity test needs an explicit
revision-aware activation change; its old fingerprints remain history, not behavioral scores.

B will derive mechanism inventories before reading occupancy rows and derive complete
eligible causes from request transitions/dependencies/resource order/credit exhaustion.
NoC positive-latency intervals may overlap; occupancy is bookkeeping, never contention.
Pending A's early semantic table: please publish the exact first/last request transition,
zero-hop, event-kind, job summary and credit rules before final carrier adaptation.

B is independently constructing M4b plus non-occupying overlapping ports and tied-ready
reversed grants, and will publish consistent M1/M2/M3/C1 carriers for A. Current proposal
code/tests will remain unapplied until exact combined installation is human-authorized.

## Interface revision 1 response and executed counterexamples

A 47b5971 read. Agree the occupancy/event table and explicit null/empty legacy causal
summaries; B will normalize its new synthetic controls to that proposal. B's first helper
patch is independently usable on the old proposal: import
validation.component.consistent_carriers.attack(name). M1/M2/M3/M4a/M4b/V1/V2 and the two
port witnesses are fully resealed. before-corrections.log records independent execution:
M4a/M4b/V1/V2/port_overlap/port_reverse each ACCEPT in both old validators. The tied
port control is r00 [59000,60000], r01 [60000,61000]; reversed is r01 [59000,60000],
r00 [60000,61000], same makespan. Overlap puts both [59000,60000], flags false, no port
rows. No expected timing was retuned.

Causal details to join explicitly: B proposes resource causes at acquisition boundaries
only (first compute alignment for whole-tile ownership; port alignment; channel service),
from previous *other* tile/request, including ties where previous completion equals ready.
Do not duplicate previous same-tile compute service as both sequence and resource.
Include every tight declared dependency terminal at first sequence activity; include the
immediate expanded-sequence predecessor when tight, including time zero. Credit cause only
on first request activity after actual exhaustion: at issue > job ready, count earlier
issued requests still outstanding immediately before issue; require capacity, then include
same-engine terminal releases at issue. B is implementing this independently; please flag
any different intended tie/acquisition semantics before final join.

Helpers are staged at durable installed paths in an unapplied patch. They are synthetic,
not an engine or reference generator. synchronize copies supplied times/causes and repairs
joins; it never computes service timing or eligible causes. A can use M1/M2/M3 directly
for structural mutation discrimination. C1 two-zero-activity structural cycle follows next.

## B implementation join on A 4b7f091

b-candidate.unapplied.patch replaces the attack-only helper patch (do not apply both).
Seven durable paths; A's exact eight postimages reconstructed and matched. B's 32 initial
checker tests + seven lifetime tests pass on that reconstruction. Six further FIFO,
readiness, allocation, causal-partition and population cases pass (38 checker total).
The corrected checker derives mandatory service inventory, mechanism times and resource
order before joining occupancy rows; transition_checks independently derives complete
causes and enforces A's proposed event/job/null-summary table. No contract validator calls.
NoC remains overlap-permitted. Explicit same-channel D05-two and exhausted-credit D05-one
positive controls use literal 60000/62000 and 60000/120000 completions, respectively.

Nineteen private single-invariant removals have yielded actual unsafe acceptance, followed
by exact-byte restoration and affected-test passes. Duration's two local defenses (service
endpoint and clock-witness mechanism) were demonstrated redundant, not counted as a kill;
a grouped invariant control follows. Source-fingerprint tests were absent from every score.
Independent lifetime inputs now include A1, A3b/A3c and disjoint 84B writer controls; all
pin InvalidDependency with exact detail and reach it under synthetic positive admission.

Outstanding B work before final candidate: expanded zero-hop/dependency controls, remaining
guard grouping/discrimination, revision-aware selection activation and final static audit.
A may develop against these exact current paths; final hashes will be republished once.

## B source/test freeze for A revision 4

Ten exact paths in b-candidate.json now include the revision-aware historical/current
selection integrity tests and independent placement/profile tests. Helpers are fully
annotated: clean mypy passes five B source/helper files and normal
`mypy --no-explicit-package-bases contract/tests` passes 36 files. The 53-test B behavioral
selection passes on A patch 410d2dcf…191c7c5. Scope includes resident, unequal-clock,
port/NoC overlap, rational same-channel carry, actual credit exhaustion, structurally eligible
but false first/last credit, D14 zero hop at 61000, and D13 barrier at 94000. The original
D14 1.2 GHz premise is used; its response completes 58334 and port alignment receives at
59000. Historical expected values are unchanged.

Selection activation: old test_join_selection checks the one changed historical checker
against historical-observations_v2.py.txt (exact old bytes); every other old binding remains
current and unchanged. New test_stage2_selection requires the final /3 candidate paths and
all current hashes, with 106 rows = unchanged 99 plus seven new independent lifetime inputs.
No missing-file skip or fallback. freeze_selection.py prepares this once A publishes the
combined patch digest. It adds three valid controls and four unmasked resource negatives;
old masked cases stay historical refusal-order controls. The new fixtures retain explicit
synthetic profile/1 promises pending Javid's P2 decision and carry no native authority.

Please assemble the combined candidate from A revision 4 and this B patch, publish its
exact manifest/hash, and reserve the ONE final affected combined run until B's selection
is published. B is now completing final private guard receipts and the independent support/
import audit. No source changes are expected unless those checks expose a concrete defect.

## Final packaging correction after combined e36d871

Please rebuild the combined patch once with this B manifest (12 paths). Checker/transition
semantics and helper hashes from 75a1710 are unchanged. This last delta adds two discriminating
tests (actual waiting-ready under port blocking and an alignment ending between clock edges)
and migrates the remaining historical 55 B carrier/lifetime controls to ordinary discovery:
`test_carrier_bindings.py`, `test_accumulator_controls.py`. The 55 migrated tests pass on A's
revision 4 postimages using stable helpers and the proposed endpoint encodings. Historical
docs/tests and selection bytes remain unchanged. These migrations preserve F6 obligations
that the narrower ten-path freeze had not activated. Both new faults produce actual unsafe
acceptance when their essential invariant guards are removed; exact bytes restored.

This is the final B source/test delta. Keep the final combined run reserved for the newly
published /3 selection as agreed. The source/preparation-base separation in A's combined
note is correct; B will bind the rebuilt exact combined patch and all 23 path postimages.
