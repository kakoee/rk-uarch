# U-P8 · U4 · Lane B — L1 analytical limits and L2 differential references

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, build-spec §2.7, third_party/README.md.
Documentation for BookSim 2 (BSD-2, Stanford), Ramulator 2 (MIT, CMU SAFARI), SCALE-Sim v3
(MIT). Optionally Gemmini (BSD-3, UC Berkeley) and Verilator (LGPL-3.0/Artistic-2.0).

TASK: two rungs. L1: the model reduces to closed forms wherever those are exact. L2: it
implements the same abstraction as independent, published models. Both run through the
engine protocol against every engine in the matrix.

1. validation/L1_limits/:
   - uncontended point-to-point transfer = hops × router_latency + serialisation (bytes /
     link width), per NoC;
   - saturated DRAM streaming = configured bandwidth ± 5%;
   - a single GEMM with operands resident in SRAM follows the pipeline formula for the
     declared array (fill + ceil-tiled steady state + drain);
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
     uniform-random, transpose and hotspot traffic, over an injection-rate sweep. ENFORCED:
     latency within 10% below 70% of BookSim's saturation throughput. Above that, record,
     don't assert;
   - DRAM: vs Ramulator 2 standalone on streaming, random and strided traces;
   - tile compute: vs SCALE-Sim v3 cycle counts for GEMM shapes on the matching array;
   - optional: one systolic tile vs Gemmini RTL under Verilator (a cycle-exact reference for
     THAT design);
   - Tenstorrent tt-npe (Apache-2.0) as a second NoC reference for mesh specs, once
     U-P13 lands a mesh engine.
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

GUARDRAILS: Do not tune engine parameters to close an L2 gap. Record it and attribute it.
Agreement between two simulators is L2 and NOTHING MORE. It never appears in a model card as
validation. BookSim, Ramulator and SCALE-Sim run as standalone references here; they are not
new dependencies of rkuarch.

ADR: docs/decisions/U0008-the-L2-reference-set-and-its-limits.md.
```
