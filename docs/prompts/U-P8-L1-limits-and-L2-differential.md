# U-P8 · U4 · Lane B — L1 analytical limits and L2 differential references

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, build-spec §2.7, third_party/README.md,
ADR U0005 (which fork sub-models are BookSim 2 or Ramulator 2). Documentation for BookSim 2 (BSD-2, Stanford), Ramulator 2 (MIT, CMU SAFARI), SCALE-Sim v3
(MIT). Optionally Gemmini (BSD-3, UC Berkeley) and Verilator (LGPL-3.0/Artistic-2.0).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Pin the prepared workload/mapping identity and represented scope for each reference
comparison. A difference caused by another mapping is not an engine discrepancy. References
that cannot consume equivalent resolved inputs must be reported as unmatched rather than
being compared solely by model name, tp or a policy label.

TASK: two rungs. L1: the model reduces to closed forms wherever those are exact. L2: it
implements the same abstraction as independent, published models. Both run through the
engine protocol against every engine in the matrix.

1. validation/L1_limits/:
   - uncontended point-to-point transfer = hops × router_latency + serialisation (bytes /
     link width), per NoC;
   - saturated DRAM streaming = peak bandwidth × (1 − t_rfc/t_refi) ± 5% at levels 0–1,
     the derating taken from the spec's timing; at level 2, at most that figure, with the
     efficiency recorded as data against Ramulator 2 in L2;
   - a latency-bound stream (one requester, dma.max_outstanding requests of request_bytes
     over a known round trip) achieves min(peak, max_outstanding × request_bytes / round
     trip) ± 5%;
   - a single GEMM with operands resident in SRAM follows the pipeline formula for the
     declared array and dataflow (fill + ceil-tiled steady state + drain);
   - A C2 RESULT IS NEVER BELOW ITS OWN U-C0 ROOFLINE. Assert it for every row of every
     table. A cycle-level result faster than the roofline of the same spec is a bug, not a
     finding;
   - at vanishing load, C2 converges to U-C0 plus the fixed latencies.
   AT LEAST TWO L1 FIXTURES ARE COMPUTED BY HAND, ON PAPER, BY A HUMAN, with the working
   committed as a scan or Markdown under validation/L1_limits/hand/. An unfilled hand
   fixture SKIPS with its id and is listed in the report. It never passes. rk-sim calls
   these the defence against plausible garbage; the same reason applies here.
2. validation/L2_differential/ (the nightly job):
   - NoC: the engine's NoC vs STANDALONE BookSim2 (built in the engine image) on
     uniform-random, transpose and hotspot traffic, over an injection-rate sweep. If the
     engine's NoC IS BookSim 2 (ADR U0005 says which fork sub-models are), the comparison is
     refused as not independent and the report says so; the bound then waits for the native
     NoC (U-P13a). ENFORCED:
     latency within 10% below 70% of BookSim's saturation throughput. Above that, record,
     don't assert;
   - DRAM: vs Ramulator 2 standalone on streaming, random and strided traces;
   - tile compute: vs SCALE-Sim v3 cycle counts for GEMM shapes on the matching array and
     dataflow, one run per dataflow the spec declares;
   - optional: one systolic tile vs Gemmini RTL under Verilator (a cycle-exact reference for
     THAT design);
   - Tenstorrent tt-npe (Apache-2.0) as a second NoC reference for mesh specs, once
     U-P13a lands the native mesh NoC;
   - energy references are DEFERRED until after U8: energy stays "unverified", and
     energy_verification stays None, until every coefficient family has a reference;
   - optional, a mapping reference: Timeloop's best mapping for representative GEMMs on the
     same array, recorded next to each named policy's efficiency. It never changes a policy:
     mapping search stays out of scope.
   Check each new tool's licence against third_party/LICENSES.md's allow-list before using
   it. If one fails, record that and skip it.
   Each comparison records its deviations as DATA (JSON, hashed), and attributes each
   deviation, where it can, to a named mechanism (e.g. "BookSim models VC allocation; the
   reservation NoC does not").
3. The L2 report computes ONE NUMBER THE FOUNDERS SHOULD WATCH: the fraction of deviations
   larger than 5% that carry a named mechanism. Below one half, the rungs above L2 will not
   mean what you want them to mean. Report it on the first page.

ACCEPTANCE TESTS:
1. All L1 pass for U-C0 and the fork; the roofline-floor assertion runs over every row of the
   npu-l4 table.
2. The two hand fixtures exist, pass, and have committed working.
3. The L2 nightly job runs end to end and publishes its report; the NoC bound is enforced.
4. A mutant (NoC with router latency read as 1 instead of the spec value) is caught by L1
   and shows up in L2.
5. The derated DRAM check and the latency-bound stream check run for every engine they apply
   to; a mutant DMA that ignores max_outstanding fails the latency-bound check.
6. At least one hand fixture covers the latency-bound stream.
7. The harness refuses to compare a sub-model with itself (a fork NoC that is BookSim 2,
   against BookSim 2), naming both.

GUARDRAILS: Do not tune engine parameters to close an L2 gap. Record it and attribute it.
Agreement between two simulators is L2 and NOTHING MORE. It never appears in a model card as
validation. BookSim, Ramulator, SCALE-Sim and Timeloop run as standalone references
here; they are not new dependencies of rkuarch.

ADR: docs/decisions/U0008-the-L2-reference-set-and-its-limits.md.
```
