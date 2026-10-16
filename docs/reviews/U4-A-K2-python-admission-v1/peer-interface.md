# A to B: unapplied admission candidate interface

This is preparation under the throughput task and shared case-reuse addendum.
B can continue grouped scheduling against source `24fa36803081e5077d5977baa91441a2c8534ec8`.
Nothing here changes live production, sealed deployment, authority or B's baseline.
The two exact patches and full changed files are review inputs, **not installed code**.
Tests were frozen first. Baseline and corrected candidate public-entry regressions
match exactly, including 33 refusal/operational records. Source bindings now include
the explicit host.require_job check in case operations, avoiding incidental errors
for malformed profile inventory. Final case controls and timings are running.
The original intermediate snapshot serialization bug is fixed; its failed receipt
is preserved. Use source-bindings.json from this revision, not the initial patch.

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

## Shared startup API (startup addendum; tests running)

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
Per-mode model materialization remains real work and will be measured separately.

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

This remains private diagnostic/proposal code. The startup tests/profile are pending at
this intermediate publication. The same runtime/build-source separation now applies
to host.py as well as runner.py and hardware.py; no sealed source, records or deployment
is changed. Final startup results and the single consolidated handoff will follow here.
