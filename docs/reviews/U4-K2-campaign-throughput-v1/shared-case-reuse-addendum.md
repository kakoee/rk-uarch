# Shared A/B addendum — case-level reuse across fresh executions

Send this same addendum to both existing sessions. Continue current work; do not
restart it or repeat completed checks on unchanged bytes. This extends A's original
per-call reuse proposal and clarifies B's scheduling unit. All other task restrictions,
including private candidate work, protected-path handling and no full campaign restart,
remain in force.

## Joint outcome

Parallelize across the 133 independent cases. A worker handles a case's three debug
and three release executions, each in a fresh native process. Share safely admitted
immutable input/setup state within that case. Preserve all 798 actual execution slots,
per-result validation, independent expectations and six-way byte comparison. Reusing
a previous result is not a repetition test and is not permitted.

Grouping calls alone does not remove production validation overhead. A supplies the
explicit case-reuse interface; B consumes it only after exact candidate reconciliation.
Until then B can implement grouped scheduling against the existing public runner and
record that validation reuse remains pending. Neither lane needs to wait to continue
its independent work.

## A owns the reusable admission interface

Extend the private, tested proposal to permit a bounded case-scoped context as well
as per-call reuse. Specify the constructor, execution/validation operations, lifetime,
mode handling and cleanup. Choose the smallest interface; names are not prescribed.

Create state only through real admission against independently resolved host authority.
Own the exact canonical request bytes and validated data privately. Do not expose
mutable nested models as an authority shortcut. Bind reuse to the exact request,
profile/registry, expected engine, permitted-job inventory, host record and relevant
executable mode. Debug and release require their own valid executable/host bindings;
sharing a common request must not imply that a debug binding authorizes release.
Keep exact executable checks and per-call limits on every fresh process launch.

Make snapshot semantics explicit: execution may use the captured admitted bytes,
not silently reopen a mutable path and treat different bytes as previously admitted.
An API presented with new bytes or another authority must re-admit or refuse. Existing
path-based public entry points retain their current validation behavior. Standalone
response parsing remains strict for independently supplied requests. Every output,
including later repetitions, still undergoes complete response and semantic checking.

Scope state to this case group/worker, with a clear release point. No persistent/global
cache, serialized approval token, caller-supplied validated flag, manufactured host
capability or unbounded cross-job cache. Document what can be inherited by forked
workers and what must be established locally. Do not assert a frozen Pydantic model
is deeply immutable. If a smaller per-mode context is needed for correctness, use it
and report the remaining duplicate work rather than merging distinct authorities.

Add discriminating controls for changed bytes, nested mutation, another host/profile/
registry/engine, wrong executable mode, cross-case use and expired state as applicable.
A corrupt second or final result must fail even after an earlier result passed.
Preserve baseline refusal meanings and canonical output. Show separately the benefit
of per-call reuse, case-scoped reuse and hardware-rule optimization using the same
bounded saved evidence. Python-only measurements are not fresh native repetitions;
do not invent missing mode/execution evidence.

## B owns scheduling and evidence collection

Schedule whole case groups across the effective available worker processes, with
resource limits and dynamic scheduling as appropriate. Preserve identities of all
six slots even though completion order differs. Canonically assemble final records
in the existing mode/repetition/case order. Use per-case immutable setup through A's
reviewed interface once available; do not reach into private state to bypass it.

Maintain fresh-process isolation, production transport and validation, independent
checks, concurrency-safe blob/receipt writes, exact membership and refusal outcomes,
time/output caps and cleanup of only the run's processes. An incomplete group cannot
be counted as complete. A failure in a later repetition must propagate, with previous
receipts preserved. Keep the one-worker path as the comparison control and measure
actual parallel throughput; do not assume core count equals speedup.

Develop the scheduler against current production while A works. Once A publishes its
exact candidate/API, reconcile them directly in a private export, retaining a serial
control and bounded mutation/failure checks. Keep old evidence and published bindings
unchanged; provide the concrete combined runtime/helper identity and placement delta.

## Delivery

Each lane returns its existing consolidated handoff with this addition included.
Publish ordinary preparation work with normal Git integration. A's production and
protected deltas remain unapplied candidates until reconciliation; B's existing
runtime stays pinned. Reuse prior unaffected checks, run the new interface/scheduler
join checks, and report actual versus inherited evidence. Return real unresolved
semantic or installation boundaries together, not one small approval request per
routine change. No campaign restart, root installation, native rebuild, artifact
adoption, remote qualification or sprint closure follows from this addendum.
