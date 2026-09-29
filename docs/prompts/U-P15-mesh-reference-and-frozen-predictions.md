# U-P15 · U8 · Lane A — The mesh reference model, and predictions frozen before anyone measures

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, validation/L3_silicon/README.md, hw/references/blackhole-p100a.yaml,
ADR U0009, U0010, U0013. Tenstorrent's public documentation: the Blackhole product page, and
tt-isa-documentation/BlackholeA0/NoC/README.md (two opposite-direction 2-D torus NoCs,
64-byte flits, about 9 cycles router-to-router, about 5 cycles NIU↔router), the TT-Metalium
device program profiler page, and tt-npe (Apache-2.0).

TASK: the same discipline as U-P9, for the class the native engine exists for: a mesh of many
small cores. Predictions are committed before any measurement exists, and this prompt never
sees one.

1. Complete hw/references/blackhole-p100a.yaml as a REFERENCE: claims only, every number with
   a URL, unknowns as stub claims. Model what the docs describe: two NoCs in opposite
   directions on a torus, the per-hop latencies, flit width, SRAM per core, the GDDR6
   channels and bandwidth, the numeric formats including BLOCKFP8 with its scale bytes. List
   every stub the engine reads in predictions/UNKNOWNS.md.
2. Agree validation/L3_silicon/blackhole/SUITE.md with Lane B FIRST, signed by both, with
   at least 24 benchmarks across at least 4 classes:
   - NoC: point-to-point latency vs hop count on each NoC; k-to-1 contention at k ∈ {2,4,8};
     row multicast;
   - DRAM: streaming read and write per channel, and all channels at once;
   - core compute: single-core matmul at ≥ 4 shapes in at least two formats;
   - multi-core: summa-2d@1-style matmul across 1, 4, 16, 64 cores; one decoder-layer
     operator set at a decode shape.
   Each benchmark states its GRANULARITY IN PROFILER ZONES: which zone start/end on which
   RISC-V core. The profiler timestamps in cycles since reset and holds 125 zones per core
   buffer. Inter-core clocks are "closely synced but may have minor skews", so a
   cross-core latency benchmark states how skew is bounded or cancelled.
3. Predictions from the native engine (all fidelity levels it has: detail 0/0/0, the level-1
   fast path, and composite C2) AND from U-C0, written to
   validation/L3_silicon/blackhole/predictions/<id>.json with full provenance. Also run
   tt-npe on the NoC benchmarks and commit its outputs as a SECOND prediction set, labelled
   as the vendor's estimator. It is an L2 reference, and its own error against silicon is
   information too.
4. One commit, message beginning "FROZEN PREDICTIONS:". check_ordering already enforces the
   rest.

ACCEPTANCE TESTS:
1. SUITE.md signed by both lanes before prediction generation.
2. ≥ 24 prediction files across ≥ 4 classes; each has a native prediction per available level
   and a U-C0 prediction; NoC benchmarks also have tt-npe predictions.
3. The reference spec loads as design_status: reference, with zero stipulations.
4. UNKNOWNS.md is complete: a test cross-checks it against the stubs the engine read.

GUARDRAILS: DO NOT LOOK AT, REQUEST OR ESTIMATE ANY MEASUREMENT. Do not edit a prediction once
it is committed. Do not tune the reference spec toward published Tenstorrent numbers. If a
documented behaviour cannot be represented at a given level (e.g. a NoC feature the
reservation model lacks), record it in the prediction file's `unrepresented` field. Do not
drop it.

ADR: docs/decisions/U0015-the-mesh-reference-and-what-it-can-support.md.
```
