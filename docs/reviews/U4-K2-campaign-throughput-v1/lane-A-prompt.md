# U4 A — remove redundant Python admission work without weakening the boundary

Continue the existing U4 A session in its independent clone. Pull published main,
preserving peer history. Javid stopped the sequential first-use campaign and asked
for a faster approach. B is already implementing a parallel campaign harness.
This task is the complementary production-validation optimization, not another
harness implementation or native-engine algorithm change.

Read this package's README, diagnostic.py, diagnostic.json and profile.txt, the
installed runner/loader/carriers, and the original frozen first-use package at
f2b270aa55204a6bf43ff8d3b7fdeb902db30c0f. The accepted engine source remains
24fa36803081e5077d5977baa91441a2c8534ec8. The interrupted run has 88 checked calls
and 89 transports; it is incomplete. Preserve all historical and partial evidence.

## Outcome and work boundary

Deliver a complete, measured, tested candidate that eliminates avoidable repeated
request parsing/admission within one call. Also evaluate the measured hardware-unit
rule hotspot. Work through routine corrections independently and return one
consolidated handoff, not separate requests for each small correction.

Build and test the candidate in a private export. Publish the exact source/test
delta and its evidence as an unapplied proposal under an owned review directory.
Keep live production, protected contract files, schemas, source/support snapshots,
root deployment, authority and frozen B inputs unchanged while B works. This
proposal boundary prevents two optimizations from silently changing each other's
baseline; it is not a request for another architecture or dependency decision.
No new dependencies, native builds/runs, artifact generation/adoption, root
installation, full campaign restart, remote work or qualification are authorized
by this task. Python-only validation of saved genuine outputs is in scope.

## 1. Remove repeated admission within a public invocation

The profile and source show request admission in run_fixed_delay/encode_request,
then another encode_request admission and another load in parse_response. The
harness reparses the same job for the independent checker as well. Distinguish
these repeated operations from the deliberate three fresh-process repetitions.

Trace the exact call graph and identify the genuinely independent trust boundaries.
An appropriate design may use a private operation returning canonical request bytes
and the admitted job, then a private response-validation operation that consumes
that exact per-call state. Keep public encode_request and standalone parse_response
fully validating externally supplied input. Preserve public signatures and output
bytes unless a concrete unavoidable change is separately identified.

Reuse only privately owned per-call validated state bound to the exact bytes and
independently resolved host context. Do not add a global cache of caller models or
trust a path, object identity, caller-provided hash, model_copy, or Pydantic instance
as proof of admission. Frozen models contain mutable nested objects. No public
'validated=True' flag, externally constructible bypass, synthetic AcceptedHostBinding,
resolver bypass, or skipping result validation is acceptable. Different host anchors,
engine identity and permitted-job inventories must remain effective on every public
entry. Keep executable identity checks, transport/framing, limits and result semantics.

Standalone parsing must still reject malformed or mismatched requests even if no
runner was called first. All public refusal/operational outcomes and canonical bytes
must match the baseline. Do not remove the independent result checker to improve a
benchmark. Identify any safe checker-interface reuse for B as an optional exact join;
B owns its harness and can continue without adopting it.

## 2. Evaluate the stable hardware-rule overhead

The profile records about 3.38 million regex fullmatch calls and 2,014 hardware
coherence validations for one profiled sample. hardware_unit_rule currently rebuilds
rule expressions for each lookup. Evaluate precomputed rule matching or a similarly
bounded equivalent optimization. Preserve ordered matching, valid/invalid paths,
allowed units, exception behavior, schema metadata, and every hardware check.
Account for whether the rule mapping can change; do not silently introduce stale
cache semantics or unbounded caches for attacker-controlled paths.

contract/uarch_contract/hardware.py and other contract paths are protected: provide
an exact unapplied patch and tests, never install it live. Keep this optimization
separable from runner-only work so the coordinator can assess its benefit against
its support/adoption impact. Do not rewrite carriers or broader validation semantics
just to make the benchmark faster.

## 3. Tests and measurements that justify the change

Write discriminating regressions before the candidate change. Cover normal and
standalone public entries; altered nested data between calls; changed raw/canonical
bytes; different host/profile/registry/engine anchors; wrong permitted job;
malformed/noncanonical streams; foreign or stale results; and restored controls.
Prove the new internal reuse does not admit input the baseline refuses. Existing
result/refusal tests remain meaningful and must not be weakened.

Use actual saved requests/results from /tmp/u4-k2-approved-campaign read-only for
Python-only before/after checks, recording exact hashes and case membership. Native
execution remains blocked in diagnostics. These checks do not qualify an unexecuted
candidate engine or invent successful result evidence. Run against explicit private
source/import paths, not the live editable installation. Tests must not mutate the
live checkout or other workers' files.

Compare baseline and candidate on the same bounded workload, one process, with the
same pinned interpreter/packages; report unprofiled timings separately from cProfile.
Measure runner reuse and rule matching separately and together. Verify resulting
bytes and independent expectations, and include representative refusals. Record
startup/resolver work separately if it remains expensive. Avoid broad suite reruns
until actual integration warrants them; run affected regressions, lint/types,
import/schema checks and currentness/closure audits appropriate to the patch.

## 4. Identity and peer reconciliation

Audit the concrete changed paths against the selected generator-support closure,
loader/runtime closure, BuildInputs/model inputs and frozen deployment inventories.
Do not assume Python-only edits preserve all accepted hashes or require a Rust
rebuild; show the actual edges. State which parts would require a human protected
installation, source/adoption lifecycle, runtime rebind or no lifecycle action.
The current sealed deployment must remain usable unchanged until reconciliation.

Coordinate the narrow interface proposal directly with B using shared published
notes/normal Git, without changing B's files or making B wait on this candidate.
B should retain the current source pin until the coordinator combines accepted
results. No repeated full native construction or fault campaign is needed merely
because this Python candidate exists.

Publish the bounded proposal normally on main with hooks and peer integration.
Return one handoff: exact baseline/candidate/patch hashes; separately applicable
runner and protected-rule deltas; tests-first and baseline/candidate/revert/restore
results; actual timing comparison; precise identity/lifecycle impact; and any real
remaining join. No CI polling or K2/U4 closure claim.
