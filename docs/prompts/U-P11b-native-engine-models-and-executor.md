# U-P11b · U6 · Lane A — Native engine models: compute level 1, NoC and DRAM level 0, and the TaskGraph executor

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/mapping/README.md, build-spec §2.4
(the ladder and fidelity_detail), §2.5 (the TaskGraph and EngineResult) and §2.8, ADR U0011
as U-P11a left it, and U-P11a's handoff.

TASK: the models at the levels this sprint builds, and the executor that runs a real
TaskGraph through them, so the native engine produces real rows.

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
2. TaskGraph executor: runs the TaskGraph from mapping/ (ws-rowsplit@1, os-tiled@1 and
   onnxim-compat@1; npu-m256 uses ws-rowsplit@1 until the mesh policies land in U-P13d),
   resolving dependencies by events, attention_fused tiles included. initial_state steady
   primes one iteration inside the same simulation and reports the second (two priming
   iterations when the job asks for the warm-up check).
3. Critical-path attribution: each interval on the critical path is charged to the resource
   that bounded it, and the parts sum to duration_ps.

ACCEPTANCE TESTS (write first):
1. The FULL L0, L0m and L1 suites pass against the native engine through the engine
   protocol, with no suite code changed.
2. Determinism: same job → byte-identical EngineResult across 3 runs, and between debug and
   release builds.
3. `uarch table hw/designs/npu-m256.yaml ... --engine native` builds a full table: the mesh
   class, which the fork cannot represent.
4. The latency-bound stream fixture (U-P8) passes, and lowering max_outstanding lowers a
   distant core's achieved bandwidth.
5. Halving accumulator_bytes on a GEMM whose output tile then no longer fits never shortens
   it, and the extra SRAM traffic appears in ext_counts.
6. attribution_s sums to duration_s on every row.

GUARDRAILS: Only the levels above: NoC "1+ts", DRAM 1 and 2, and compute 2 are U-P13a–c. No
threads. Do not optimise before the determinism and L0–L1 suites pass. Do not tune a model
toward the fork; U-P11c measures agreement.

ADR: append to docs/decisions/U0011-the-native-engine-core.md the models built and every spec
field the native engine lists as unrepresented at these levels.
```
