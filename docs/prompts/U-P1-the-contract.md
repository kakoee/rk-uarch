# U-P1 · U1 · joint → Lane A — The contract

_From build-spec §8. One prompt, one fresh session._

> This is the one prompt both of you should sit through. Everything downstream (every engine,
> fixture, mapping policy, validation case and the rk-sim integration) codes against what it
> produces.

```text
CONTEXT TO LOAD: CLAUDE.md, docs/build-spec.md §2.3 (the contract), §2.4 (fidelity), §2.6
(applicability bins) and §7 (integration), contract/README.md. From rk-sim, READ-ONLY, from
a local clone at the SHA you record in ADR U0001: rk/provenance.py, rk/engine/f0/compute.py
(IterationCost,
iteration_cost, IterationCounts), rk/engine/f0/power.py (operating_point), rk/schema/
{fidelity,channels,execution,workloads}.py, docs/decisions/0011, 0016, 0021, 0026, 0027, and
docs/prompts/P16-symbolic-operators-and-parallelism.md for its baseline operator list.

TASK: contract/uarch_contract/, the only vocabulary uarch shares with rk-sim. Pydantic v2,
frozen=True, extra="forbid" on every model.

1. sourced.py — SourcedValue. rk-sim's five fields VERBATIM (value, unit, provenance, source,
   date) with rk-sim's validator semantics: provenance=stub requires source=None, anything
   else requires a non-empty source, non-finite values refused. PLUS one field:
   kind: Literal["claim","stipulation"] = "claim".
   A STIPULATION IS NOT A WEAK CLAIM, IT IS A DIFFERENT THING. It is a design choice for a
   chip that does not exist ("tile SRAM = 2 MB") and it defines the question the way n_layers
   does in rk-sim's ModelSpec. So: kind="stipulation" requires provenance=None, source=None,
   date=None, and a non-empty `rationale: str`. kind="claim" forbids rationale. Write the
   validator so both halves fail loudly with a sentence that says which rule was broken.
2. hardware.py — HardwareSpec, design_status: Literal["proposed","reference"].
   - A "reference" describes a real chip and may contain ONLY claims.
   - A "proposed" design may contain stipulations.
   - The loader refuses a stipulation anywhere in a reference, naming the parameter path.
   Structure, per build-spec §2.3.2 (Rev 2): clock_domains; cores (grid shape; core_type with
   a matrix engine and its supported dataflows, a vector engine, SRAM with banks, DMA engines
   with max_outstanding and request_bytes, and job_overhead_cycles); sync (mechanism,
   barrier_latency_cycles); an optional shared_sram; one or more NoCs (topology mesh|torus,
   link_bytes_per_cycle, router_latency_cycles, virtual_channels, buffer_flits, direction for
   multi-NoC designs); memory (interleave granularity and scheme; controllers with attachment
   coordinates, scheduler and page_policy; DRAM standard, channels, bandwidth, capacity,
   organization and timing); numeric formats per engine (byte width, accumulation width,
   block-scale bytes); energy coefficients per activity, with voltage_ratio per frequency
   ratio; static power; tdp. EVERY NUMERIC LEAF IS A SourcedValue, DRAM organisation and
   timing included; a preset may supply DRAM timing only as claims whose source names the
   preset file at a pinned SHA. Categorical fields (dataflows, scheme, scheduler,
   page_policy, sync mechanism) are plain enums. Integer counts that define composition
   (grid rows, number of NoCs) are plain ints, exactly as rk-sim treats device counts.
3. operators.py — THE OPERATOR VOCABULARY. uarch holds the pen here because it has the
   harder requirement: a roofline needs a name and a FLOP count; a tiled model needs
   shapes, layouts, reduction axes and per-operand precision. Start from rk-sim P16's baseline
   list and use its names where they exist: Q/K/V projection, QK score, softmax, AV
   application, output projection, normalization, residual addition, FFN projections,
   activation. Add only what tiling needs (e.g. kv_write, embedding, lm_head). Each OpSpec
   carries its M/N/K (or equivalent) as named dimensions, operand dtypes and the reduction
   axis. COUNTING FOLLOWS rk-sim P7b: A MULTIPLY-ADD IS TWO OPERATIONS. Restate it in the
   module docstring; do not re-decide it.
4. model_shape.py — ModelShape, the sidecar ModelSpec lacks: d_ff, gated_mlp, vocab_size,
   attention: Literal["mha","gqa"], tie_embeddings, expert_d_ff (MoE only). Plus a copy of
   rk-sim's ModelSpec with IDENTICAL field names and validators, and
   implied_params(spec, shape) -> (total, active). check_parity() raises unless both are
   within 1% of ModelSpec's total_params and active_params. Two sources describing
   different models is the failure this exists to make impossible.
5. precision.py — rk-sim's PrecisionFormat, all eight members, same string values.
6. request.py — CharacterizationRequest, field for field as build-spec §2.3.3 lays it out:
   contract version, rk_schema_snapshot, component_id, hardware_spec_hash, model, model_shape,
   precision {compute, kv_cache}, tp, envelope, grid (decode B × context_per_seq, prefill
   n × L, frequency_ratio), mapping_policy, uarch_fidelity, initial_state (steady | cold),
   kv_layout {block_size_tokens}, visit_weights (optional), seed.
7. table.py — UarchCostTable and Row. A ROW IS ONE CHIP'S SHARD, ONE ITERATION, ALL LAYERS,
   WITHOUT INTER-CHIP COLLECTIVES. Write that sentence in the class docstring. Fields per
   build-spec §2.3.3: duration_s, u_c0_duration_s (uarch's own aggregate roofline for the
   same point, which is the floor every C2 row must respect and the "detail delta" rk-sim's
   Compare shows), attribution_s {compute, memory, noc, sync, overhead} (a critical-path
   split whose parts sum to duration_s), counts {matrix_ops, vector_ops, memory_read_bytes,
   memory_write_bytes} (rk-sim Channel names), ext_counts {sram_read_bytes, sram_write_bytes,
   noc_flit_hops}, peak_resident_bytes {hbm, sram}, and diagnostics (build-spec §2.3.3):
   every diagnostic is Optional with NO default of 0, because null means "not modelled".
   Table-level: initial_state, kv_layout, interpolation spec, measured_error
   {interpolation_loo (with weighted_median_rel), composition_reduction, layer_reuse,
   cold_vs_steady; each sampled error with n_samples}, flop_parity {max_rel,
   declared_deviations[]}, composite_fidelity, fidelity_detail, provenance {params,
   model_card hash, conditional_on}, warnings (the declared omissions of build-spec §2.3.4
   among them).
8. model_card.py — ModelCard: model_id (engine, engine version, fidelity_detail, mapping
   policy), badge, evidence (ledger ids), verification {L0, L0m, L1, L2: report hash or
   None}, validated_error_band: None | {rel_low, rel_high, scope {family, op_classes,
   precisions, shape_regimes, load_regimes, mapping_match}}, energy_verification: None |
   {L0, L2: report hash}. None means "unknown" (for energy, "unverified"). THERE IS NO ZERO
   DEFAULT ANYWHERE IN THIS FILE.
9. hashing.py — canonical_json (sorted keys, floats via repr round-trip, no NaN), sha256,
   spec_hash / request_hash / table_hash. CONTRACT_VERSION = "uarch-contract/0.1".
10. errors.py — one exception class per row of build-spec §7.4's error table:
    NoTableForComponent, EnvelopeExceedsGrid, SpecHashMismatch, ContractMajorMismatch,
    ContractMinorMismatch (a warning), ResidencyExceedsCapacity, NonFiniteRow,
    MissingFrequencyAxis, InitialStateMismatch, KvLayoutMismatch, StipulationOnReference,
    ClaimWithoutSource, SramCapacityExceeded, UnnamedPreset (a DRAM timing preset the spec
    does not cite). Each carries the sentence the user will read.
11. make gen writes contract/schema/*.json from the models; CI fails if it is stale.

ACCEPTANCE TESTS (write first):
1. Round-trip: every model survives model_validate(model_dump(mode="json")) unchanged.
2. Hash stability: table_hash of the toy table is identical across two fresh interpreter
   processes (subprocess, not the same process twice) and invariant to input key order.
3. One test per error class, each constructed from a minimal failing input.
4. SourcedValue: a stipulation with a source is refused; a claim with a rationale is
   refused; a non-stub claim without a source is refused; a stub with a source is refused.
5. A reference HardwareSpec holding one stipulation deep in the tree is refused, and the
   message names the full parameter path.
6. UNITS LIVE IN NAMES. A test walks every float field of request.py and table.py and fails
   on any name without a unit suffix from the allow-list in build-spec §6.1.
7. CYCLES NEVER CROSS. A test fails if any field in request.py or table.py is named *_cycles
   or carries unit "cycle". Cycles are an engine-internal quantity.
8. ModelShape parity: a Llama-3.1-70B-shaped sidecar passes against its ModelSpec; the same
   sidecar with d_ff off by 10% fails with both numbers in the message.
9. contract/tests/fixtures/toy_table.json (hand-written by you, two decode rows and one
   prefill row) validates, and the contract CI job is green against it.
10. Rev-2 fields: a reference spec whose DRAM timing names a preset without a pinned source is
    refused (UnnamedPreset); a design with sram.bytes but no energy.pj_per_byte.sram is
    refused, naming both paths.
11. NULL, NOT ZERO: a test fails if any diagnostics field in table.py, or any field in
    model_card.py, has a numeric default.
12. The toy table carries initial_state, kv_layout, all four measured errors, and a
    diagnostics block with at least one null.

GUARDRAILS: Import nothing from rk: copy rk-sim names by reading its source, and let U-P2's
vendored round-trip prove the copy is exact. Do not add a workload IR or an ONNX path. Do not
add fields for later sprints (mapping search, parallel sync, multi-chip): the contract grows
by MINOR bumps with an ADR each. The Rev-2 fields are not later-sprint fields: an engine that
cannot use one lists it as unrepresented. If P16's baseline names and tiling's needs genuinely
conflict, write both options into ADR U0001 and STOP. That is a founders' decision.

ADR: docs/decisions/U0001-the-integration-contract.md, written with both founders. It must
state build-spec §7.2's eight semantic rules in your own words and record the rk-sim SHA the
contract was read against. Rule 1 matters most: a row is one shard, and the rk-sim side must
use a tp divisor of 1. It is the likeliest silent bug in the project. U0001 also records the
Rev-2 decisions, with build-spec §2.6's proposals as the defaults: the shape-regime and
load-regime bins; whether BLOCKFP8 evidence can cover an fp8 request (proposal: no); whether
shared_sram is in contract 0.1 (proposal: yes, optional); the initial_state default
(proposal: steady); and the declared omissions, mixed prefill/decode iterations among them.
```
