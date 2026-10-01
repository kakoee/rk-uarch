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

AUTHORITY: CLAUDE.md says agents propose and stop on contract/ and docs/decisions/. This
prompt is that proposal. Write contract/ and docs/decisions/U0001 in full, leave them
uncommitted, and stop; both founders review them and commit with UARCH_HUMAN=1.

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
   Structure, per build-spec §2.3.2 (Rev 2.1): clock_domains (each with scales_with_core);
   cores (grid rows and cols; core_type with a matrix engine, its array, supported dataflows,
   accumulator_bytes, operand_buffer_bytes and operand_bytes_per_cycle, a vector engine, SRAM
   with banks, DMA engines with max_outstanding and request_bytes, and job_overhead_cycles);
   sync (mechanism, barrier_latency_cycles); an optional shared_sram; one or more NoCs
   (topology mesh|torus, link_bytes_per_cycle, router_latency_cycles, virtual_channels,
   buffer_flits, direction for multi-NoC designs); memory (interleave granularity and scheme;
   controllers with attachment coordinates, scheduler, page_policy, read and write queue
   depths and noc_credits; DRAM standard, channels, bandwidth, capacity, organization,
   timing_preset and timing); numeric formats (byte width, accumulation width, block-scale
   bytes); energy coefficients per activity, with voltage_ratio per frequency ratio; static
   power; tdp. EVERY NUMERIC LEAF IS A SourcedValue, counts included (grid, array, banks, DMA
   engines, virtual channels, DRAM channels and organisation, queue depths, credits), with an
   integral value for counts; a reference marks an unpublished count as a stub. Only these
   stay plain: categorical enums (topology, direction, dataflows, scheme, scheduler,
   page_policy, sync mechanism), list structure (how many NoCs and controllers), attach
   coordinates, and a format's byte width. A preset supplies DRAM timing only through
   memory.dram.timing_preset {file, sha}; each timing claim it supplies has source
   "<file>@<sha>". Each *_cycles leaf is in its block's clock domain (build-spec §2.3.2).
3. operators.py — THE OPERATOR VOCABULARY. uarch holds the pen here because it has the
   harder requirement: a roofline needs a name and a FLOP count; a tiled model needs
   shapes, layouts, reduction axes and per-operand precision. Start from rk-sim P16's baseline
   list and use its names where they exist: Q/K/V projection, QK score, softmax, AV
   application, output projection, normalization, residual addition, FFN projections,
   activation. Add only what tiling needs (e.g. kv_write, embedding, lm_head) and
   attention_fused (QK score -> softmax -> AV over KV tiles, scores on chip; its operation
   count is the sum of its three parts, and its DRAM operands are Q, K, V and O only; build-spec
   §2.3.5). Each OpSpec
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
   n × L, frequency_ratio), mapping_policy, uarch_fidelity (the fidelity_detail keys and
   values of build-spec §2.4), initial_state (steady | cold), kv_layout {block_size_tokens},
   visit_weights (optional), seed. tp is the shard: the table is ONE rank of a tp-way split
   (build-spec §2.3.4).
7. table.py — UarchCostTable and Row. A ROW IS ONE CHIP'S SHARD, ONE ITERATION, ALL LAYERS,
   WITHOUT INTER-CHIP COLLECTIVES. Write that sentence in the class docstring. Row keys:
   decode {phase, batch, total_context_tokens, frequency_ratio}; prefill {phase, n_prompts,
   prompt_tokens, frequency_ratio}. Fields per build-spec §2.3.3: duration_s, u_c0_duration_s (uarch's own aggregate roofline for the
   same point, which is the floor every C2 row must respect and the "detail delta" rk-sim's
   Compare shows), attribution_s {compute, memory, noc, sync, overhead} (a critical-path
   split whose parts sum to duration_s), counts {matrix_ops, vector_ops, memory_read_bytes,
   memory_write_bytes} (rk-sim Channel names), ext_counts {sram_read_bytes, sram_write_bytes,
   noc_flit_hop_count}, peak_resident_bytes {hbm, sram}, and diagnostics (build-spec §2.3.3):
   every diagnostic is Optional with NO default of 0, because null means "not modelled".
   Table-level: contract, uarch_version, request_hash, table_hash, tp, initial_state,
   kv_layout, interpolation spec, measured_error {interpolation_loo (with
   weighted_median_rel), composition_reduction, layer_reuse, cold_vs_steady (with
   priming_2_vs_1_max_rel); each sampled error with n_samples}, flop_parity {max_rel,
   declared_deviations[{id, deviation_rel, reason}]}, composite_fidelity, fidelity_detail
   (build-spec §2.4's keys and values), provenance {params (derive_rk_params of the spec),
   model_card {hash, badge, evidence, validated_error_band, energy_verification},
   conditional_on}, warnings (the declared omissions of build-spec §2.3.4 among them).
8. model_card.py — ModelCard: model_id (engine, engine version, fidelity_detail, mapping
   policy), badge, evidence (ledger ids), verification {L0, L0m, L1, L2: report hash or
   None}, validated_error_band: None | {low_rel, high_rel, scope {family, op_classes,
   precisions, shape_regimes, load_regimes, mapping_match}}, energy_verification: None |
   {L0, L2: report hash per coefficient family}. None means "unknown" (for energy, "unverified"). THERE IS NO ZERO
   DEFAULT ANYWHERE IN THIS FILE.
9. hashing.py — canonical_json (sorted keys, floats via repr round-trip, no NaN), sha256,
   spec_hash / request_hash / table_hash. CONTRACT_VERSION = "uarch-contract/0.1".
10. errors.py — one exception class per raising row of build-spec §7.4's error table:
    NoTableForComponent, EnvelopeExceedsGrid, SpecHashMismatch, ParamsMismatch, TpMismatch,
    ContractMajorMismatch, ContractMinorMismatch (a warning), ResidencyExceedsCapacity,
    NonFiniteRow, MissingFrequencyAxis, InitialStateMismatch, KvLayoutMismatch; plus the
    uarch-side errors StipulationOnReference, ClaimWithoutSource, SramCapacityExceeded,
    UnnamedPreset (a DRAM timing claim citing a preset other than
    memory.dram.timing_preset, or a timing_preset without a pinned sha) and ShardIndivisible
    (heads or FFN width not divisible by tp). Each carries the sentence the user will read.
11. make gen writes contract/schema/*.json from the models; CI fails if it is stale.

ACCEPTANCE TESTS (write first):
1. Round-trip: every model survives model_validate(model_dump(mode="json")) unchanged.
2. Hash stability: table_hash of the toy table is identical across two fresh interpreter
   processes (subprocess, not the same process twice) and invariant to input key order.
3. One test per error class. Where contract code raises it (StipulationOnReference,
   ClaimWithoutSource, UnnamedPreset, ShardIndivisible), build it from a minimal failing
   input; for errors raised later or in rk-sim, assert the class exists, carries its
   sentence, and round-trips through the schema.
4. SourcedValue: a stipulation with a source is refused; a claim with a rationale is
   refused; a non-stub claim without a source is refused; a stub with a source is refused.
5. A reference HardwareSpec holding one stipulation deep in the tree is refused, and the
   message names the full parameter path.
6. UNITS LIVE IN NAMES. A test walks every float field of request.py and table.py and fails
   on any name without a unit suffix from the allow-list in build-spec §6.1, applying §6.1's
   two exceptions exactly (keys of a mapping field inherit its unit; rk-sim Channel names
   are verbatim). The real field names of build-spec §2.3.3 pass.
7. CYCLES NEVER CROSS. A test fails if any field in request.py or table.py is named *_cycles
   or carries unit "cycle". Cycles are an engine-internal quantity.
8. ModelShape parity: a Llama-3.1-70B-shaped sidecar passes against its ModelSpec; the same
   sidecar with d_ff off by 10% fails with both numbers in the message.
9. contract/tests/fixtures/toy_table.json (hand-written by you, two decode rows and one
   prefill row) validates, and the contract CI job is green against it.
10. Rev-2 fields: a reference spec whose timing_preset has no sha, or one timing claim of
    which cites a preset file other than timing_preset, is refused (UnnamedPreset); a design
    with sram.bytes but no energy.pj_per_byte.sram is refused, naming both paths; a reference
    with a stub bank count loads.
11. NULL, NOT ZERO: a test fails if any diagnostics field in table.py, or any field in
    model_card.py, has a numeric default.
12. The toy table carries tp, initial_state, kv_layout, all four measured errors, the
    embedded model card, and a diagnostics block with at least one null.
13. A fidelity_detail value outside build-spec §2.4's legal set (dram: "2+ts", say) is
    refused, naming the key.

GUARDRAILS: Import nothing from rk: copy rk-sim names by reading its source, and let U-P2's
vendored round-trip prove the copy is exact. Do not add a workload IR or an ONNX path. Do not
add fields for later sprints (mapping search, parallel sync, multi-chip): the contract grows
by MINOR bumps with an ADR each. The Rev-2 fields are not later-sprint fields: an engine that
cannot use one lists it as unrepresented. If P16's baseline names and tiling's needs genuinely
conflict, write both options into ADR U0001 and STOP. That is a founders' decision.

ADR: docs/decisions/U0001-the-integration-contract.md, written with both founders. It must
state build-spec §7.2's nine semantic rules in your own words and record the rk-sim SHA the
contract was read against. Rules 1 and 9 matter most: a row is one rank of a tp-way split
that uarch built, the rk-sim side uses a tp divisor of 1, and it refuses a table built for
another tp. Getting this wrong is the likeliest silent bug in the project. U0001 also records
these decisions, each with its proposed default:
- the shape-regime and load-regime bins (build-spec §2.6's proposal);
- whether BLOCKFP8 evidence can cover an fp8 request (proposal: no);
- whether shared_sram is in contract 0.1 (proposal: yes, optional; engines list it as
  unrepresented until after U8);
- the initial_state default (proposal: steady);
- the declared omissions, mixed prefill/decode iterations among them;
- the shard (proposal: build-spec §2.3.4's Megatron-style split; one tp per table);
- where applicability is judged (proposal: per row; a row's evidence applies only if every
  operator in it has its op class and shape regime covered, and its load regime for NoC and
  DRAM classes);
- clock domains (proposal: build-spec §2.3.2's assignment; a frequency ratio scales the core
  domain and every domain with scales_with_core: true);
- fidelity values (proposal: build-spec §2.4's keys and legal values, the same in requests
  and tables);
- row keys (proposal: decode {batch, total_context_tokens}, prefill {n_prompts,
  prompt_tokens});
- the model card in the table (proposal: embedded, as build-spec §2.3.3 shows);
- attention (proposal: one attention_fused operator; scores never in DRAM).
```
