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
