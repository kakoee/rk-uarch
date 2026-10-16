# Shared A/B addendum — startup cost and the recurring developer loop

Javid has explicitly requested optimizing genuine host resolution/setup as well as
case execution, because validation will recur during development. Add this to the
existing tasks; do not create another worker or restart completed work. Deliver one
consolidated handoff per lane, with the three reuse scopes distinguished: startup
common data, a case's repetitions, and internal work within one call.

B reported 556.93 seconds for genuine resolution/setup and 63.20 versus 10.56 seconds
for eight saved-output checks with one/eight workers. These numbers are B-reported
until its exact receipt is published and reconciled. Do not attribute all startup
time to one function without a breakdown. The coordinator's separate measured
16-check batches remain 124.37/20.67/16.55 seconds at 1/8/16 workers, Python-only.

## A: optimize startup using a real authority-producing API

Profile the resolver/setup phases separately: selector/approval, common file hashing,
profiles/registry, corpus/job admission, mode-specific receipts/binaries and preparation
of case state. Establish how often each phase executes for both modes and workers.
The current resolver loads the complete job inventory separately for each mode.

Implement a private candidate API that validates the shared immutable installation
and corpus once per campaign/setup session, and produces correctly bound debug and
release capabilities through the real production authority path. Reuse the common
validated material without re-admitting the entire corpus for every mode or worker.
Retain separate validation of each executable, mode configuration and build receipt.
Do not create a release capability by editing a debug dataclass or copying its token.
Keep strict public resolution behavior and test it independently of the shared path.

This explicitly extends the previous case-scoped proposal with a bounded startup
session. It does not authorize a durable/global cache across campaigns or treating
prior CI success as permission. Own exact bytes, authority identity and immutable
internal state; define lifetime, invalidation and cleanup. Returned case contexts
must not expose a mutable shared graph that can change another worker's authority.
No memoization based only on path, mtime, user-supplied hash or Python object identity.

Changes to the selector, approval, HostRecord, trust/profile/registry, source/support,
corpus membership, any job, executable or build receipt must still be detected at
its existing trust boundary. Binding checks and executable verification remain in
force for actual launches. Test cross-mode substitution, stale sessions, mutation,
missing/extra cases and unchanged positive controls. Preserve refusal semantics;
never mark an unvalidated corpus member admitted merely because the other members
or another mode passed.

Evaluate parallel pure validation during initial resolution only if the profile
justifies it and immutable reuse is insufficient. Coordinate resource ownership
with B so nested pools do not oversubscribe CPUs/memory. Unrelated cleanup or a
second engine/authority implementation is outside scope. Protected changes remain
unapplied patches with lifecycle effects disclosed, as in A's existing task.

## B: consume shared setup once and expose honest test profiles

Continue case-group scheduling independently. Integrate A's exact startup/session
API in the private join once published. The parent/setup phase establishes genuine
authority; worker initialization must not each repeat the complete host resolution.
Document whether state is inherited, reconstructed or transferred and why authority,
immutability and resource bounds are preserved. Keep one-worker and multiworker
controls and do not use unreviewed serialization to manufacture capabilities.

Report startup wall time separately from case-processing wall time and total time.
Measure baseline and candidate on the same bounded selection and environment. A
speedup of case processing alone is not a speedup of the whole campaign. Include
peak-memory/resource observations appropriate to the worker-count choice. Python-only
saved-result diagnostics remain distinct from fresh native or full-campaign evidence.

Prepare explicit recurring-use selections/commands alongside the full campaign:
- Fast development: relevant unit/boundary tests and a small declared representative
  smoke selection, avoiding full-corpus host startup merely to run unrelated units.
- Broader regression: declare exact case/mode/repetition coverage for changed runtime
  or boundary behavior; reuse existing test selection mechanisms where possible.
- Complete first-use/qualification evidence: retain the current exact 798 slots and
  replay/refusal obligations. A quick profile must never write a complete-campaign
  receipt or silently satisfy that gate.

Propose when to run each selection and what changes require broader coverage. Do not
change existing required gates, hosted CI workflows, U0024 deferrals or repetition
policy by implication. Native remote CI remains deferred; local developer commands
and preparation are sufficient for this task. Avoid an elaborate new test framework.

## Finish as the same combined optimization milestone

Keep the stopped run, current sealed deployment and historical receipts unchanged.
Publish candidate source/helper patches, bounded discriminating checks, actual timing
breakdowns and the exact installation/binding implications together. Resolve routine
A/B joins directly through published work; return only substantive unresolved issues.
No full campaign restart, root installation, native rebuild, artifact adoption or
qualification claim is released by this addendum. The coordinator will reconcile one
combined candidate rather than schedule separate campaigns for each optimization.
