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
