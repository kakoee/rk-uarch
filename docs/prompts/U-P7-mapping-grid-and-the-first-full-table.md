# U-P7 · U4 M / U7 T · Lane A — Mapping first, then consumer-driven full tables

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, src/rkuarch/{mapping,table,workload}/README.md, build-spec §2.3.3
and §2.3.4 (canonical batches and the reduction error), §7.2 (the nine rules), ADR U0005,
contract/uarch_contract/{request,table}.py. From rk-sim READ-ONLY: rk/engine/f0/compute.py's
comment block above IterationCounts, which says why (B, T, Q) is sufficient for a
roofline and warns that it is exact only while cost is linear.

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Extend U2's saved-input path with the existing TaskGraph; policies are versioned
preparation producers outside engines. Imported mapped inputs bypass policy execution and
are validated unchanged. No engine silently substitutes its own mapping or rebuilds work.

ORDINARY EXECUTION AND BASIC PROVENANCE (U0011 simplification amendment):
Keep the native-first schedule. Use installed software/engine/model versions and existing
hardware/request/prepared-input/result/table data hashes. Ordinary execution requires no
development checkout/evidence, executable digest, host approval records, custom startup
assurance or exhaustive build tracing. Preserve model/capability admission, actual input
and result validation, independent tests and deterministic results. A-F3 is retired by
scope change, not a passing verification; do not retry its stopped experiment. Use an
explicit minimal schema transition, never dummy hashes or a new attestation framework.

TASK: run only the phase named in the handoff. M (U4a) delivers the approved mapped
component boundary; T (U7) delivers the first full product table. A small table may be
built earlier for a named use, but no full grid gates silicon. Passing G4/G7 is not a
prerequisite for producing an honestly labeled table. U0023 replaces the old U4b full grid.

PHASE M — inputs and exit:
- Require exact accepted component scope/semantics and human-installed mapped carriers
  before public mapper/wiring. U-P11a K1 internals may proceed separately.
- Implement only the admitted mapping slice from item 1 and export/import validation in
  item 10, with scope-appropriate fixtures; later policies/operators stay refused.
- Independently derive placements, capacity, jobs/transfers/dependencies; test invalid
  dimensions/resources/capacity and producer-disabled imported replay identity. A changed
  placement changes identity; no implicit remapping. Public execution tests wait for K2/B.
- Handoff schema/producer versions, admitted/refused scope and exact tests. Stop: items
  2–9 and the full-table acceptance below are T, not an M release requirement.

PHASE T — inputs and exit:
- Require verified engine scope and the declared U7 consumer manifest: exact design,
  ModelSpec/shape, precision/tp, coefficients, policies, initial state, grid and error jobs.
- Complete missing full-model/rank/precision/operator admission under the U-P11b model
  discipline and U-P13 mechanisms before generating the grid: all layers, once-only
  head/tail, RoPE/conversions/coefficients, KV and capacity, with independent complete-work
  checks. TPU-specific R completion is neither sufficient nor required for this product scope.
- Deliver items 1–10 at that scope and all applicable full-table acceptance below (G3b).
  The first full demo table is npu-m256 × 70B-class × FP8 × tp8, with G6 for C2.
- Resolve FP8/RoPE, ragged composition, hardware formats/dataflows and public schema changes
  before dependent runs. The accepted npu-l4 remains WS/BF16 until separately revised.
  A missing required point blocks G3b; do not silently drop it or change its precision.
- Product scope changes require their own acceptance. Full npu-l4/32×32 grids have no
  automatic requirement; use declared study/scale points where sufficient.

1. mapping/ — standalone preparation: named, versioned policies, each a pure function
   (validated prepared op graph, HardwareSpec) ->
   TaskGraph (build-spec §2.5): per-core compute jobs, DMA jobs, NoC transfers (unicast and
   multicast), barriers, dependencies.
   - ws-rowsplit@1 for the large-core class (weight-stationary, output rows split across
     cores).
   - os-tiled@1 for the large-core dataflow study when its hardware revision is accepted;
     it is not a prerequisite for an unrelated mesh table.
   - U-P13d owns summa-2d@1 and head-parallel@1 for the mesh consumer. Scope each mapping
     and acceptance case to its actual hardware/operator inputs.
   A policy's name@version is a stipulation on every row. A better policy is a new version,
   never an edit. No search, no autotuning. Every policy declares the matrix dataflow it
   needs (refused on a spec whose dataflows lack it) and its buffer depth (double or triple
   buffering, part of name@version). It places every SRAM-resident buffer (core,
   offset_bytes, bank) and refuses a tile that does not fit with SramCapacityExceeded,
   naming the core and the bytes. KV reads are page-granular DMA jobs. attention_fused is
   tiled so its score tile (query block × KV page block) fits in SRAM: scores never become
   DMA jobs.
2. table/grid.py — the grid from the request's envelope. Refuse a request whose grid does not
   cover its envelope, naming the uncovered region, at REQUEST time.
3. table/pool.py — one process per grid point, parallel ACROSS POINTS only. Results are
   reassembled in grid order, so the table is byte-identical at 1 worker and at N.
4. table/interpolate.py — exactly the declared scheme: decode bilinear in (log B, log T),
   prefill bilinear in (log n, log L), linear in 1/f across the frequency axis. OUTSIDE THE
   GRID IS AN ERROR (EnvelopeExceedsGrid), never a clamp and never an extrapolation. It also
   writes contract/fixtures/interpolation_vectors.json (proposed to both founders, since
   contract/ is theirs): query points inside and on the edges of the toy table's grid, with
   the expected interpolated value of every row field. rk-sim's table-backed cost (U-P19)
   and any later native-code reader must reproduce them within 1e-12 relative; that is what
   keeps the table usable from any language.
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
   d. cold_vs_steady: for a seeded sample, run both initial states and report the deviation;
      on the same sample, run steady with two priming iterations and report how far one is
      from two (priming_2_vs_1_max_rel), so the warm-up length is measured.
   Each sampled error reports n_samples. interpolation_loo also reports
   weighted_median_rel, weighted by the request's visit_weights, or null when there are
   none.
6. Frequency axis: for each frequency ratio in the grid, scale the stipulated core-domain
   clock (and whatever the spec declares scales with it), rerun, and record the row.
   attribution_s is diagnostic only; it is never fed back into a max() form.
7. Rows carry peak_resident_bytes. If HBM residency exceeds the spec's capacity, raise
   ResidencyExceedsCapacity for weights, and warn for KV, mirroring rk-sim's M0 rule.
8. `uarch table ... --engine native --workers N` builds the complete declared consumer
   grid. The npu-m256/70B/FP8/tp8 demo remains required. Additional BF16, npu-l4, tp1 or
   policy variants need a named consumer and accepted scope; capacity failures remain
   explicit, never worked around or omitted to make an envelope pass.
9. initial_state travels in every EngineJob; steady primes one iteration at the same point
   and reports the second.

10. Extend prepare/export and prepared-input loading with complete TaskGraph payloads and
    their hashes: placements, tiles, DMA/NoC transfers, dependencies, barriers and policies.
    Schema and producer versions are explicit. Validate hardware/resource references, SRAM
    capacity, dimensions and dependency consistency before launching an engine. Reject a
    hardware-incompatible imported mapping rather than re-running a local policy.
    Materialize all requested grid and seeded error-experiment jobs during preparation;
    imported bundles must declare sufficient query/state coverage or refuse the experiment.

ACCEPTANCE TESTS (write first):
1. Determinism: two builds byte-identical; --workers 1 vs --workers 8 byte-identical.
2. An out-of-envelope query raises EnvelopeExceedsGrid at request time, naming the region.
3. Interpolating at a grid point returns the grid value exactly.
4. LOO and composition errors are present, finite, and reported. The composition sample is
   seeded and reproducible.
5. G3b (execution-plan §4): the consumer table passes applicable L0/L0m/L1 through Lane B,
   and its card reports only actual applicable evidence: stub/unknown error without it.
   C2 admission requires G6; neither C2 nor a complete grid proves physical accuracy.
6. Every policy in the consumer scope reproduces independent tile/transfer expectations;
   required second-policy studies remain U-P14 work, not a blanket silicon prerequisite.
   No mandatory external-tool compatibility policy is added.
7. layer_reuse and cold_vs_steady errors are present, finite, seeded and reproducible.
8. A tile larger than a core's SRAM is refused with SramCapacityExceeded, naming the core and
   the bytes.
9. With uniform visit_weights, weighted_median_rel equals median_rel.
10. At the U-P14 dataflow-study delivery, os-tiled@1 refuses unsupported dataflows and
    runs on its accepted supporting spec; this does not gate an unrelated mesh table.
11. A prefill row at L = 32768 builds with no SramCapacityExceeded, and its attention DRAM
    bytes equal Q, K, V and O within named deviations.
12. The table's composite follows build-spec §2.4 and the actual U0011 implementation levels.
13. interpolate.py reproduces interpolation_vectors.json, and a query outside the grid in
    that file is refused.

ADDITIONAL ACCEPTANCE — prepared inputs:
- A locally prepared mapped bundle replays with mapping policies disabled and yields
  identical EngineResults/tables for the same engine/version/run conditions.
- A supported external TaskGraph fixture executes without the local mapper. Changing its
  placement changes content/cache identity even if the model and policy label are unchanged.
- Unsupported supplied mapping, stale hardware binding, bad dependencies, and missing error
  sample coverage are refused; no implicit retiling or regeneration occurs.
- Optional reference comparisons must establish resolved-input correspondence; a shared
  policy label alone cannot pass the mapping-match check.

GUARDRAILS: No mapping search. Never silently clamp an out-of-grid query. Do not correct the
composition or layer-reuse error, because disclosure is the deliverable. Do not let
attribution_s feed back into anything. Do not add parallelism inside a simulation:
parallelism is across points only.

ADR: docs/decisions/U0007-canonical-batches-and-the-reduction-error.md.
```
