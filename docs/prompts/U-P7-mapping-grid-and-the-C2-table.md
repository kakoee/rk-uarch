# U-P7 · U4 · Lane A — Mapping policies, the grid, interpolation, and the first C2 table

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, src/rkuarch/{mapping,table,workload}/README.md, build-spec §2.3.3
and §2.3.4 (canonical batches and the reduction error), §7.2 (the eight rules), ADR U0005,
contract/uarch_contract/{request,table}.py. From rk-sim READ-ONLY: rk/engine/f0/compute.py's
comment block above IterationCounts, which says why (B, T, Q) is sufficient for a
roofline and warns that it is exact only while cost is linear.

TASK: turn a CharacterizationRequest into a complete, hashed, honestly-errored C2 table,
driven by the fork.

1. mapping/ — named, versioned policies, each a pure function (op graph, HardwareSpec) ->
   TaskGraph (build-spec §2.5): per-core compute jobs, DMA jobs, NoC transfers (unicast and
   multicast), barriers, dependencies.
   - ws-rowsplit@1 for the large-core class (weight-stationary, output rows split across
     cores).
   - onnxim-compat@1: reproduces the chosen fork's own tiling decisions, read from its source
     and cited by file and line in the policy's docstring. It exists so a native engine can
     later be compared with the fork ON THE SAME WORK. Without it every future disagreement
     is ambiguous between "different engine" and "different mapping".
   A policy's name@version is a stipulation on every row. A better policy is a new version,
   never an edit. No search, no autotuning. Every policy declares the matrix dataflow it
   needs (refused on a spec whose dataflows lack it) and its buffer depth (double or triple
   buffering, part of name@version). It places every SRAM-resident buffer (core,
   offset_bytes, bank) and refuses a tile that does not fit with SramCapacityExceeded,
   naming the core and the bytes. KV reads are page-granular DMA jobs.
2. table/grid.py — the grid from the request's envelope. Refuse a request whose grid does not
   cover its envelope, naming the uncovered region, at REQUEST time.
3. table/pool.py — one process per grid point, parallel ACROSS POINTS only. Results are
   reassembled in grid order, so the table is byte-identical at 1 worker and at N.
4. table/interpolate.py — exactly the declared scheme: decode bilinear in (log B, log T),
   prefill bilinear in (log n, log L), linear in 1/f across the frequency axis. OUTSIDE THE
   GRID IS AN ERROR (EnvelopeExceedsGrid), never a clamp and never an extrapolation.
5. table/errors.py — the table measures its own errors and reports them. It never
   corrects them.
   a. interpolation_loo: leave each interior point out, predict it from the rest, report the
      median and max relative error.
   b. composition_reduction: rk-sim reduces a batch to (B, T, Q) sufficient statistics. A
      cycle-level model is not linear (padding, tile quantisation), so for a seeded sample of
      points evaluate UNEQUAL batches with the same (B, T, Q) as the canonical equal-length
      one, and report how far they deviate. This number is a finding. It tells rk-sim how much
      its own sufficient-statistic reduction costs at C2.
   c. layer_reuse: for a seeded sample of grid points, simulate every layer (no reuse) and
      report how far the reused result deviates (build-spec §2.3.4).
   d. cold_vs_steady: for a seeded sample, run both initial states and report the deviation.
   Each sampled error reports n_samples. interpolation_loo also reports
   weighted_median_rel, weighted by the request's visit_weights, or null when there are
   none.
6. Frequency axis: for each frequency ratio in the grid, scale the stipulated core-domain
   clock (and whatever the spec declares scales with it), rerun, and record the row.
   attribution_s is diagnostic only; it is never fed back into a max() form.
7. Rows carry peak_resident_bytes. If HBM residency exceeds the spec's capacity, raise
   ResidencyExceedsCapacity for weights, and warn for KV, mirroring rk-sim's M0 rule.
8. `uarch table ... --engine fork --workers N` builds the full default grid for npu-l4 ×
   Llama-3.1-70B-class × fp8 and bf16, tp=1.
9. initial_state travels in every EngineJob; steady primes one iteration at the same point
   and reports the second.

ACCEPTANCE TESTS (write first):
1. Determinism: two builds byte-identical; --workers 1 vs --workers 8 byte-identical.
2. An out-of-envelope query raises EnvelopeExceedsGrid at request time, naming the region.
3. Interpolating at a grid point returns the grid value exactly.
4. LOO and composition errors are present, finite, and reported. The composition sample is
   seeded and reproducible.
5. G3 (execution-plan §4): the npu-l4 table passes L0, L0m and L1 (U-P6 and U-P8) as run by
   Lane B, and its model card says stub.
6. onnxim-compat@1 reproduces the fork's tile counts per op on three shapes, cited to source.
7. layer_reuse and cold_vs_steady errors are present, finite, seeded and reproducible.
8. A tile larger than a core's SRAM is refused with SramCapacityExceeded, naming the core and
   the bytes.
9. With uniform visit_weights, weighted_median_rel equals median_rel.

GUARDRAILS: No mapping search. Never silently clamp an out-of-grid query. Do not correct the
composition or layer-reuse error, because disclosure is the deliverable. Do not let
attribution_s feed back into anything. Do not add parallelism inside a simulation:
parallelism is across points only.

ADR: docs/decisions/U0007-canonical-batches-and-the-reduction-error.md.
```
