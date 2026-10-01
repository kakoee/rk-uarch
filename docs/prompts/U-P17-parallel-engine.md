# U-P17 · U9 · Lane A — The parallel engine: exact conservative synchronisation, then a labelled lax mode

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, build-spec §2.8 (ownership and partitioning) and
§2.9 (parallel execution), ADR U0011, U0012 (the performance baselines), U0013. From rk-sim
READ-ONLY: docs/vision/elements_of_parallel_DES.md §§6–15 and 30–38 (partitioning, mailboxes,
epochs, determinism) and docs/vision/rack-to-kernel-24-month-execution-plan.md (E6 and the funded plan's G1).
SST's documentation on conservative synchronisation with link-latency lookahead.

TASK: parallelism INSIDE one simulation, built so that the exact mode is byte-identical to the
single-threaded engine. Only then comes a lax mode, and it is labelled as approximate everywhere it
appears.

1. Partitioning: logical processes are rectangular sub-meshes (row bands first; blocks behind
   a flag). Every owner id belongs to exactly one partition, so the ownership discipline from
   U-P11 becomes the partition boundary, and the owner assertion now also fails a
   cross-partition mutation. Memory controllers, and the shared SRAM when present, may be
   their own partition.
2. EXACT MODE: windowed conservative synchronisation. Lookahead L = the minimum latency of any
   cross-partition link, which is router pipeline plus link, and SEVERAL CYCLES on any real
   design. It is not 1, and this is where the vision note's lookahead-collapse premise gets
   corrected in code. Each window [T, T+L): partitions execute independently; cross-partition
   events go into single-producer/single-consumer mailboxes; at the barrier, mailboxes are
   drained and merged in the global total order (t_ps, phase, target, seq). seq for a
   cross-partition event is derived deterministically, NOT from a shared atomic counter
   whose value depends on thread interleaving.
3. Threads: a fixed pool pinned to cores, static partition affinity, no work stealing in this
   prompt. No mutex on the hot path; the only synchronisation is the window barrier.
4. LAX MODE (a flag, off by default): a synchronisation quantum Q > L. Events that cross a
   partition boundary within a window are delivered at the next window boundary (temporal
   decoupling, as in a TLM-2.0 quantum keeper). EngineResult then reports sync: approx(Q),
   and the composite rule (U-P13) DROPS THE COMPOSITE TO C1 unless the model card cites a
   measured error-vs-Q curve that covers this Q (U-P18 produces it).
5. The U-P12 metrics become live: cross-thread messages per simulated cycle and sync
   operations per million simulated cycles, recorded for npu-m256 and the 32×32 variant at
   1, 2, 4, 8 and N threads.

ACCEPTANCE TESTS (write first):
1. EXACT MODE IS BYTE-IDENTICAL to single-threaded for every golden request, at 1, 2, 4 and
   8 threads, under the sanitizer build too (TSan added to the nightly for this binary).
2. A mailbox fuzz test with randomised thread sleeps produces identical output across 50
   runs.
3. The lookahead is computed from the spec, not configured. A test changes a router latency
   and asserts L changes with it.
4. Lax mode at Q = L is byte-identical to exact mode. At Q > L, EngineResult says
   approx(Q) and the composite is C1 without a covering curve.
5. Scaling is recorded, not asserted: the speedup curve at 1..N threads, next to the vision
   note's expectation, whatever it turns out to be.

GUARDRAILS: No optimistic synchronisation and no rollback: the design says so, and adding
it is a new ADR, not a detail. No SIMD, GPU or MPI in this prompt. Never let lax mode be the
default. Never let a result computed in lax mode carry exact mode's composite.

ADR: docs/decisions/U0017-the-parallel-engine.md, with the measured scaling and the
lookahead values for each golden design.
```
