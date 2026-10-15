# U-P11b · U4a/U4b · Lane A — Native engine models: compute level 1, NoC and DRAM level 0, and the TaskGraph executor

_From build-spec §8. One prompt, one fresh session._

```text
TEMPORARY U0024 EXCEPTION: read docs/decisions/U0024-temporary-local-verification-and-deferred-native-ci.md.
During its multi-sprint deferral, passing current local checks and independent review may
support interim development under the normal task/contract prerequisites. Record remote
qualification pending; no local result becomes a hosted CI/nightly/performance pass.
Full G5, U9 entry, simulator-performance claims and final project closure keep their gates.

CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/mapping/README.md, build-spec §2.4
(the ladder and fidelity_detail), §2.5 (the TaskGraph and EngineResult) and §2.8, ADR U0011
as U-P11a left it, and U-P11a's handoff.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Execute locally produced or imported validated TaskGraphs through the same path.
Mapping policy identifiers are provenance, not instructions for the native engine to invoke
Python mapping. Engine arbitration follows declared policies; it never changes tile shapes,
placement, fusion or buffer assignment to fit a job. Reject unsupported supplied decisions.

TASK: execute only the authorized phase. B (U4a) implements the accepted small component
slice; R (U4b) extends the same engine to the actual U5 reference suite. Product tables are
U-P7 T in U7. Unsupported work refuses, never disappears from a claimed complete layer.

B prerequisites/exit: K2 and approved component inputs; implement the admitted subset of
items 1–3, independent literal/fault checks and applicable acceptance below. Full decoder,
extra hardware/precision, steady state or spill remain refused until explicitly admitted.
Record every deferred acceptance case with R or later consumer; do not claim G3a from B.

R prerequisites/exit: reviewed TPU sourcing, reference representability/measurement scope,
exact required suite and protected contract decisions. Add native reference admission and
all required operators/precisions, including RoPE/casts/coefficient traffic and fused/paged
KV work where used. Validate no omitted work, reference fields/unknowns, decoder execution,
steady/priming behavior and benchmark-granularity correspondence. Int8 is admitted only when
required/supported, never inferred from BF16. Required missing scope blocks G3a. Implement
reference changes here, before U-P9's prediction-only freeze session. No silicon results or
tuning in this task. B and R both require applicable public-boundary tests before acceptance.

1. Models (build-spec §2.4):
   - compute level 1: tile-job intervals, meaning pipeline fill and drain for the job's
     declared dataflow, tile quantisation and padding, double-buffer overlap of DMA and
     compute, operand staging at operand_bytes_per_cycle, an output tile bounded by
     accumulator_bytes (partial sums beyond it go to SRAM where the policy placed them), and
     job_overhead_cycles on every tile job. A tensor job is O(1–10) events, not O(cycles);
   - NoC level 0: hop latency, infinite bandwidth;
   - DRAM level 0: fixed latency plus a bandwidth cap per channel, derated for refresh from
     the spec's timing;
   - at every level, each DMA engine honours dma.max_outstanding and request_bytes, so a
     distant core's bandwidth is latency-bound; barriers cost sync.barrier_latency_cycles.
   EngineResult reports fidelity_detail honestly: {compute: 1, noc: 0, dram: 0}. The
   composite for that is C1 at best, and the table must say so.
2. TaskGraph executor: runs only explicitly admitted mapping/ output (no automatic
   os-tiled or second-hardware requirement); U6 mesh admission is separately verified,
   resolving dependencies by events, attention_fused tiles included. initial_state steady
   primes one iteration inside the same simulation and reports the second (two priming
   iterations when the job asks for the warm-up check).
3. Critical-path attribution: each interval on the critical path is charged to the resource
   that bounded it, and the parts sum to duration_ps.

ACCEPTANCE TESTS (write first):
1. All required applicable L0, L0m and L1 cases pass at the public native boundary.
   Preserve U0006 unsupported/not_run reductions; do not rewrite expectations to match
   the engine. Tests distinguish executed work from expected input totals.
2. Determinism: same job → byte-identical EngineResult across 3 runs, and between debug and
   release builds.
3. B passes its declared component cases. R passes G3a's actual benchmark suite and reference
   admission, not a full table. U6 uses representative mesh points; G3b full tables are U7.
4. The latency-bound stream fixture (U-P8) passes, and lowering max_outstanding lowers a
   distant core's achieved bandwidth.
5. Halving accumulator_bytes on a GEMM whose output tile then no longer fits never shortens
   it, and the extra SRAM traffic appears in ext_counts.
6. attribution_s sums to duration_s; independent critical-path fixtures and discriminating
   faults check assignment, serialization and permitted overlap before G4 uses it. A large
   attribution share is not proof of the cause of silicon error.

ADDITIONAL ACCEPTANCE — prepared inputs:
- Replay a saved mapped job with local workload/mapping producers unavailable and compare
  its complete EngineResult with the original. Invalid placement is refused before events
  run. No hidden reconstruction from ModelSpec or tp is allowed.

GUARDRAILS: Only the levels above: NoC "1+ts", DRAM 1 and 2, and compute 2 are U-P13a–c. No
threads. Do not optimise before determinism and applicable L0–L1 pass. Do not tune to
reference results. U-P11c/U-P12 qualify the expanded native scope in U6.

ADR: append to docs/decisions/U0011-the-native-engine-core.md the models built and every spec
field the native engine lists as unrepresented at these levels.
```
