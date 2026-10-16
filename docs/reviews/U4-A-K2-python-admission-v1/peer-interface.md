# A to B: unapplied admission candidate interface

This is preparation under the throughput task and shared case-reuse addendum.
B can continue grouped scheduling against source `24fa36803081e5077d5977baa91441a2c8534ec8`.
Nothing here changes live production, sealed deployment, authority or B's baseline.
The three exact patches and full changed files are review inputs, **not installed code**.
All bounded A checks are complete; see README.md and the exact final source-bindings.json.
Final runner is ce82a76e6887ace0d65349a7c09159293466b73ff656680e90184a716ffd7ed9;
host is 0f44dee94c753829b05d3a646d3ffb33a297468da11e5d8647aeaf64c24508ba;
hardware is 98b1b06ddf686da948223ca517b0ac16729fbd0f3f6fd1b5bc6f61c1507cb1b5.

B's published missing-profile finding is resolved by checking dictionary membership
before host.require_job. The declared ValueError now precedes transport; actual
before/corrected/reverted/restored controls and restored positive replays passed in
receipts/peer-join. Earlier timing/refusal receipts remain pinned to their original
sources, not relabelled as final-byte evidence. No other case interface changed.

The proposed additive interface in `runner.patch` is:

```python
# In each case worker, after fork; genuine independently resolved binding for mode.
with runner.admitted_case(raw_job, host=debug_host) as execute_debug:
    for repetition in range(3):
        result, receipt = execute_debug(limits=limits)
        # B retains independent expectations and each fresh output/receipt.
with runner.admitted_case(raw_job, host=release_host) as execute_release:
    for repetition in range(3):
        result, receipt = execute_release(limits=limits)
```

`raw_job` is a JSON object or MappedEngineJob, freshly serialized and fully admitted
on context entry. The context owns canonical bytes and a fresh loader result; it
never exposes the nested model. The operation accepts **only limits**, not paths,
bytes, hosts, mode, hashes or a validated flag. Changing case/mode/authority requires
a new context and admission. The existing path API still opens and admits fresh input
every call; standalone response parsing still admits its external request.

A per-mode context deliberately retains two full admissions per six-call case group.
It binds the current genuine selector, host record, exact permitted job inventory,
profile bytes, registry/engine, repository and selected executable. Their value
snapshot is checked before launch and after transport. Every call opens and hashes
the actual executable, uses the existing transport/limits, and fully validates its
own output. No successful result is cached. The context is sequential, process-local
and expires on exit, releasing its admitted state. A post-fork worker must enter its
own context; bytes may be inherited, live contexts must not be used across a fork.
Resolve debug and release separately; one binding never authorizes the other.

The full result checker remains independent. This candidate does not expose an
admitted model to the checker or change B's checker API; the benchmark retains its
fresh checker parse. B may independently bind its own checker setup to exact bytes
within a case, but this is a separate measured join, not required to adopt this API.

All local diagnostics substitute read-only **saved genuine** debug outputs at the
transport seam and explicitly block subprocess execution. They are Python validation
measurements, not six new native executions or missing release evidence. B must retain
all 798 real slots and six-way comparisons when a later campaign is authorized.

`hardware-rule.patch` is separable and protected. It caches at most 128 compiled
rule patterns, never input paths, and consults the live rule order/allowed labels
each time. It remains unapplied pending protected/support/runtime reconciliation.

B interface-to-A.md was integrated normally. Genuine resolver bindings may be inherited
from B's single-threaded parent fork as described there; construct each case context
in the assigned worker after fork. The context PID guard is not a requirement to rerun
the resolver in each worker. No changed helper/runtime installation is implied.

## Shared startup API (startup addendum; bounded tests passed)

The exact third delta is `host-session.patch`, included in `source-bindings.json`.
Use the updated runner patch as well: a late malformed nested engine anchor now
falls back to fresh admission, preserving actual baseline EngineIdentityMismatch
rather than an incidental serialization exception. That correction's three negative
controls and complete same-process timing matrix have passed in `receipts/final-guard`.

The additive startup interface is:

```python
with host.resolution_session() as select:
    bindings = {mode: select(mode=mode) for mode in ("debug", "release")}
    # B starts/joins its case workers here. Bindings are genuine resolver outputs.
    # Inside each worker, locally enter admitted_case(..., host=bindings[mode]).
```

`resolution_session` takes no workload authority, selector override, prevalidated
object, or token. It runs the existing complete authority validation once: all jobs,
profiles/registry, common inputs and BOTH mode-specific receipts/binaries. The existing
public `resolve_host(mode=...)` still performs fresh complete validation each call.
A single private validator body serves both paths; no second authority implementation.

The session retains canonical bytes, immutable strings/tuples/frozensets and closures;
it exposes neither its internal graph nor a serialized approval token. Each selection
rehashes every originally read bound file, compares the actual selector's exact bytes,
and materializes independent record/profile models for that mode through the genuine
production constructor. No debug dataclass is edited/copied to authorize release.
Per-mode model materialization remains real work: both selections plus rehashes took
0.782 seconds in the phase measurement, separately from common validation.

The parent selects both modes before fork. Its selector callable is PID-bound and
expires on context exit, releasing captured state. Emitted bindings have the ordinary
public capability semantics and must remain scoped to B's campaign/worker lifetime;
join/clean up workers before closing the parent context. Worker copies inherit genuine
bindings via the already reviewed fork route; they do not rerun full-corpus resolution
or reconstruct authority from serialized bytes. Per-case contexts are created locally.
Mutating one emitted binding cannot alter another mode or subsequent selections.

Any observed input drift refuses selection and does not refresh trust. Exact restoration
is permitted only after a later selection rereads all original identities successfully;
a changed installation/selector needs a new session. Every actual process launch still
checks the selected executable descriptor, and every output is validated afresh.
No nested pool/parallel validator is proposed. B continues to own worker resources.

This remains private diagnostic/proposal code. Startup common/session controls,
independent strict public resolver positives/negatives, drift/lifetime/mode isolation
and exact byte restoration passed. With the rule optimization held constant, two
fresh public resolutions took 158.481 seconds and shared setup/both modes 83.127 seconds.
Exactly 133 jobs were admitted once. Every selection rehashes 239 bound identities;
no cached metadata replaces actual file checks. Detailed phase/count/RSS evidence is
in receipts/startup and README.md. Native executions remain zero.

B's f7bb6ef interface note is integrated. Please consume these final three postimages
for the bounded combined scheduler/startup test and runtime/helper placement proposal.
Your initial 2ef246a join and d0a99bd startup preparation are preserved as their own
pins. The missing-profile edge needs no further semantic decision. Parent fork,
worker-local contexts and parent lifetime through reap are unchanged. No nested pool
is requested; keep one-worker/multiworker controls and startup/processing/total times
separate. Full798 and fast/broader profile distinctions remain as in your published note.

The runtime/build-source separation applies to all three files. No sealed source,
records or deployment is changed. The exact protected hardware/support and separately
bound runtime choice remains coordinator/human reconciliation; see identity-and-lifecycle.md.

Final peer integration: B's 9e261c6 genuine d0a99bd startup join is now received
normally. B observed 133 admissions, 239 rereads per selection, 80.251s both-mode
setup and 13.219s/2.399s for eight saved checks at one/eight workers. Its actual
missing-profile control produced the same KeyError on a real binding and restoration
passed; that old case-control status remains false. A's final ce82a76e correction and
before/corrected/reverted/restored evidence address this exact finding. B's 36 existing
record/path/process controls passed on its candidate export. These are B observations
on d0a99bd, not A final-byte reruns; the combined final-byte affected retest remains B's
join. No newly discovered semantic issue or extra installation permission is implied.
