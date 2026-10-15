# U4 Lane A: fixed-delay saved-input loader and K2 preparation

Author clone: `/home/jjaff/AI-infra-simulation/rk-uarch-u4-a`, independent main.
Started clean, fetched and fast-forwarded `1c42aed` to published `4f3be8f`; required
`d9d51ca67ba8f1862ae71224020504cb7e8f5bcb` is an ancestor. Peer history is preserved.
This package is ordinary A-owned implementation/preparation. No protected installation,
component mapper, native launch, public host authority, K2 activation or U4 exit.

Implemented: [loader](../../../src/rkuarch/workload/mapped.py) and
[tests](../../../tests/unit/test_u4_a_mapped_loader.py). Exact signatures and fixture joins
for B are in [K2-proposal.md](K2-proposal.md). Inputs are the exact installed full
MappedEngineJob; host registry/profile hashes and expected engine are separate mandatory
keyword arguments. Return is the exact installed carrier, not another workload IR.
Export validates before writing, uses canonical UTF-8, refuses overwrite, and never
rehashes or remaps. Relocated imports do not run producers. There is no native subprocess.

## Tests-first and controls

`tests-first.log` captures missing-module collection failure before implementation.
Initial test scaffolding incorrectly assumed nonempty installed clock_setup and a
structural_leaves dict. Corrected tests construct clock mutations explicitly and mutate
an actual nested hardware dictionary. Those four initial failures were scaffolding
errors, not product passes. No installed fixture was changed. The final focused run
is in `focused.log`: **108 passed** (43 new loader tests, 65 installed admission tests).

Tests include export/import/relocation; duplicate keys/non-finite/trailing JSON; unknown
fields, strict integer coercion, old protocols, stale and rehashed broken joins; wrong
engine/profile/registry/seed/clock/scope; malformed dependencies and closure; mutation
before export; refusal before creating output; and full caller rehash with unchanged host
anchor. The attack has a positive consistency control under a separate synthetic anchor,
then fails against the original host anchor. All unit anchors are synthetic scaffolding,
not human-approved profiles or native evidence. A later test adds three isolated Python
process replays with producer/native imports blocked and explicit current clone origins;
these are Python loader processes, not native execution.

## Actual dependencies and selected-policy currentness

[audit.py](audit.py) records actual local module origins, import/load opens, conservative
AST imports including function-local/conditional imports and package initializers, test
data reads and the installed selected-generation support inventory in
[dependency-audit.json](dependency-audit.json). Observed runtime and static local loader
closures each contain **26 files**. The selected generation-support closure currently
contains **56 files**; that is an observation, never a quota. It remains strictly current
against the installed adopted vendor pair. New loader has no reverse import from nominal
roots, no initializer edits and no implicit authority/data discovery. No artifact lifecycle
transition is needed for this measured change.

Production file read is only the explicitly supplied saved job. Test audit reads
`contract/fixtures/mapped/kernel-job.json`; additional unit refusal controls explicitly
read component-job/resident/transport. Existing contract admission tests retain their
published reads. No accepted host authority file is installed or read; the embedding host
must eventually resolve the independently accepted record. That future resolver's actual
Git/profile/registry/executable/build reads require a new B audit. Authority argument hashes
are not a claim that this library can authenticate who supplied them.

## Concrete preparation and decisions

- [K2-proposal.md](K2-proposal.md): writer/process/parser and direct-Rust responsibilities,
  one-job EOF framing, status/error/stdout behavior, canonical serialization, exact proposed
  hash dependency and numeric feature, acyclic build identity and binary-origin verification.
- [observations-and-tests.md](observations-and-tests.md): execution-derived observation and
  causal-path algorithm, hand O/F/Z/I/T/Q/clock/overflow examples, numerical and observation
  fault discriminators and exact public test obligations.
- [public_boundary_tests.py.txt](public_boundary_tests.py.txt): unapplied runnable test design
  using **real future execution** for positives and result mutations; not a fake result
  generator and not collected in the present suite. Fixture/API release is still required.
- [event-kinds.proposed.patch](event-kinds.proposed.patch): necessary protected enum/schema
  addition for actual K1 dependency/owner-grant dispatches, read-only apply check passes.
  Exact pre/post hashes are recorded. It is not applied. Release-time clock semantics and
  event vocabulary require further reconciliation; the minimal two-kind patch does not
  resolve those decisions automatically.
- [dependency-candidates.json](dependency-candidates.json): read-only official crate metadata
  for exact proposed pins/licences/checksums. No install, lock/feature change or substitute
  hash. Prospective resolved closure/image approval and canonical float parity stay open.

B/coordinator should consume published `f213317ec61622c91e74c9f42e95578e80432588`; see
[published-coordination.md](published-coordination.md) for exact API and fixture joins.
Consume these APIs and candidate
joins, then return published finite fixture/profile/registry candidates and dependency
findings. No untracked peer file is an input. This package does not claim B agreement.
Qualifying first use still needs actual profile/registry acceptance, semantic reconciliation,
bounded K2 implementation/build release, exact built-engine receipt and final host binding.
A K1 library commit must never occupy that tested-K2-binary field.

## Evidence scope

Executed Python/static/currentness checks are recorded in validation receipts. Inherited
native evidence is only the installed K1 publication: final tested `fb7ba4a`, 28 tests per
mode, replay `4490d63cd5b49bac327ded1661df7802356f541e003391666963965809f2a62a`;
controls at `63ca8be`, inventory installed at `1351d29`, recorded at `d9d51ca`.
No native rerun was required or performed. Historical proposal paragraphs are not current
release records. No remote CI was requested, run or polled. U0024 deferral remains in force;
independent review, public K2 qualification, performance and final closure remain separate.

Executed final evidence: 1938 passed, 29 skipped, 10 deselected in 861.03s (0:14:21); fresh committed export
179 passed, including all 43 final loader tests. See [validation.json](validation.json)
for exact collection scope, origins, currentness and preservation checks. Both CI-form
mypy commands ran with PYTHONPATH/MYPYPATH unset; lint/import contracts and all three
schema checks passed. The 29 analytic skips are retained limitations, not native passes.
