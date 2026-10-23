# Observed developer runtime and memory

Host measurements from `performance.jsonl`, not simulated chip timing. GiB = 2^30
bytes, MiB = 2^20 bytes. Each row is one sequential attempt. Stage times below are
separate completed-stage wall times; the case column is inclusive and must not be
added to them. Failed incomplete phases are unmeasured. Validation/checking includes
the unchanged independent checker; internal subdivisions are unmeasured. Preparation
includes its validators, and analytic resolution includes its own bundle validation.

| Case / attempt | Status | Case wall s (inclusive) | Mapping s | Preparation s | Native invocation s | Input validation + revalidation s | Output validation + independent check s | Analytic decoding + resolution s | Serialization/check + persistence s | Compression s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| layer-b32-s1 / 1 | failure | 217.39 | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured | unmeasured |
| layer-b32-s1 / 2 | failure | 516.82 | 129.05 | 205.98 | unmeasured | unmeasured | unmeasured | unmeasured | 30.15 | unmeasured |
| layer-b32-s1 / 3 | failure | 246.45 | unmeasured | unmeasured | unmeasured | 214.81 | unmeasured | unmeasured | unmeasured | unmeasured |
| layer-b1-s128 / 4 | complete | 316.63 | 44.95 | 78.59 | 14.37 | 81.03 | 30.17 | 36.99 | 16.77 | 6.59 |
| gather-p16-c2048 / 5 | complete | 24.61 | 1.80 | 2.50 | 1.41 | 2.76 | 4.71 | 1.07 | 2.22 | 0.66 |
| gather-p32-c2048 / 6 | complete | 21.60 | 1.41 | 1.93 | 1.55 | 2.19 | 4.55 | 0.82 | 2.10 | 0.63 |
| launch-minimal / 7 | complete | 8.20 | 0.12 | 0.04 | 0.02 | 0.08 | 0.02 | 0.02 | 0.03 | 0.02 |
| layer-b32-s1 / 8 | complete | 482.59 | reused / unmeasured | reused / unmeasured | 41.40 | 216.44 | 80.61 | 86.68 | 27.26 | 22.53 |

Python peak is the largest final `RUSAGE_SELF` value across that case's short-lived
workers. Native peak is the sole child process's wait rusage, including its launch
footprint. A killed worker's final Python peak is unavailable. Combined RSS is an
**approximate sampled sum**, and may double-count shared pages or miss brief peaks.

| Case / attempt | Python peak GiB | Native peak GiB | Combined peak GiB (approx.) | Available GiB before → after | Swap used MiB before → after | Input MiB raw → gzip | Output MiB raw → gzip |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| layer-b32-s1 / 1 | unmeasured | unmeasured | 9.74 | 11.64 → 11.57 | 0.00 → 0.00 | unmeasured → unmeasured | unmeasured → unmeasured |
| layer-b32-s1 / 2 | unmeasured | unmeasured | 10.51 | 11.61 → 8.67 | 0.00 → 4.54 | unmeasured → unmeasured | unmeasured → unmeasured |
| layer-b32-s1 / 3 | unmeasured | unmeasured | 9.98 | 11.62 → 2.44 | 4.54 → 4.54 | unmeasured → unmeasured | unmeasured → unmeasured |
| layer-b1-s128 / 4 | 6.17 | 4.04 | 6.15 | 11.61 → 11.61 | 4.54 → 4.54 | 40.00 → 3.08 | 168.49 → 18.26 |
| gather-p16-c2048 / 5 | 0.39 | 0.62 | 0.51 | 11.60 → 11.60 | 4.54 → 4.54 | 4.18 → 0.22 | 26.77 → 2.59 |
| gather-p32-c2048 / 6 | 0.35 | 0.58 | 0.35 | 11.61 → 11.61 | 4.54 → 4.54 | 3.41 → 0.20 | 25.52 → 2.38 |
| launch-minimal / 7 | 0.08 | 0.04 | 0.00 | 11.61 → 11.61 | 4.54 → 4.54 | 0.02 → 0.00 | 0.01 → 0.00 |
| layer-b32-s1 / 8 | 9.12 | 11.71 | 11.96 | 20.61 → 20.59 | 0.00 → 0.00 | 184.00 → 10.09 | 445.53 → 51.63 |

Before the bounded retry, B32 had only its **192,935,120-byte** prepared input
(about 184 MiB), with no completed native output or compressed B32 artifact. Its successful mapping/preparation and isolated
input-validation workers reached exact Python peaks of 8.66, 8.94 and 9.12 GiB respectively;
the whole failed-attempt peak remains unmeasured because a later worker was interrupted.
Immediate after-case memory can precede full kernel reclamation. Subsequent idle readings
returned to about 11.6 GiB available; no unrelated process was killed.

The 1 s supervisor polling interval adds up to about one second per short-lived worker.
It dominates the 8.20 s inclusive minimal-launch case, whose native invocation was only
0.02 s. Use the separate stage times for small-case comparisons. A near-zero sampled
combined RSS for that case means sub-second workers were missed by sampling, not zero
memory consumption. Exact Python/native peaks and byte sizes remain in the JSONL records.

The observed prefill bottleneck is Python mapping, preparation and repeated validation:
44.95 + 78.59 + 81.03 s, versus 14.37 s native invocation and 6.59 s compression. This
single-host observation is not a general engine-performance claim. B32 exceeded the original
headroom even after the Python graph was released; the larger WSL budget allowed the
unchanged native invocation to finish. Potential later follow-ups
are to profile native parsing/execution memory, reduce duplicated validated representations
while preserving checks, and reduce supervisor wait overhead on tiny cases. These are
options for a separately scoped decision, **not automatic work or new acceptance gates**.

## Bounded B32 retry after the user restart

Attempt 8 is the one authorized retry on the restarted WSL instance: 23.47 GiB total
RAM, 20.61 GiB available immediately before the case, and 12 GiB unused swap. No effective
cgroup/rlimit cap was observed; unavailable root-cgroup files are explicitly null in the
[preflight](b32-retry-preflight.json). Source, executable and saved-input identities were
verified before use. The utility and native executable were unchanged from the preceding
four successful recovery cases. The external sampler is separately identified in B32's
provenance. Mapping/preparation were reused, not rerun or relabelled as new work.

The case completed in **482.59 s**; the enclosing diagnostic launcher took **483.38 s**.
These are inclusive alternatives, not additive durations. The separate saved-input copy
was 0.37 s; its time is outside the serialization/check column. Python peak was **9.12 GiB**
(input validation); native lifetime peak was **11.71 GiB**. The external sampler's combined
peak was **11.96 GiB**, including the recovery supervisor, worker and native process tree.
This approximate sum can double-count shared pages and miss peaks; earlier rows use the
worker-tree sampler, so their scope differs slightly. Sampled native RSS and HWM both
observed 11.71 GiB; the exact lifetime native value comes separately from wait rusage.
The minimum sampled available RAM was **8.68 GiB**, comfortably above the live 2 GiB guard;
swap use stayed zero. Native and CLI exit status were both zero, with no supervisor stop.

B32 input validation/revalidation (216.44 s), output validation/checking (80.61 s), and
analytic decoding/resolution (86.68 s) outweighed native invocation (41.40 s). Output
serialization/comparison and persistence took 27.26 s; compression took 22.53 s.
The 192,935,120-byte input compressed to 10,581,579 bytes; the 467,173,575-byte output
compressed to 54,141,287 bytes. Complete exact phases, worker peaks and sizes are in
[b32-retry-summary.json](b32-retry-summary.json), with incremental samples in
[b32-retry-diagnostics.jsonl](b32-retry-diagnostics.jsonl) and [performance.jsonl](performance.jsonl).
Native parsing/admission, simulation and output construction remain **unmeasured internally**;
external RSS cannot attribute memory to those phases. A separately scoped native memory
profile could distinguish them. Reducing repeated Python representations/validation cost
while preserving every check is another potential follow-up. Neither is started here.
