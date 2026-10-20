# Recommended TPU v5e representation

Revision 2 continues `0d817eebc8ff2668eae277eebc8475b09122406f`. The 52-unit implementation
scope is approved; the revised model/interface is proposed and remains unapplied.

## Evidence reconciliation

Accessed 2026-10-20. Sources are facts about published specifications, not silicon results.
The existing [source pins](../source-pins.json) remain documentation pins, not runtime pins.

| Property | Evidence and resolution | Use |
| --- | --- | --- |
| Chip organization | [Cloud v5e](https://docs.cloud.google.com/tpu/docs/v5e): one TensorCore, four MXUs, one vector and one scalar unit | One shared local-memory domain, four separately identified matrix owners; **not** four cores with replicated VMEM |
| Array | [Cloud architecture](https://docs.cloud.google.com/tpu/docs/system-architecture-tpu-vm): pre-v6e MXUs are 128×128; BF16 multiply, FP32 accumulation | Keep array dimensions and accumulation precision; independent scheduling/issue rules remain unknown |
| Peaks | Cloud v5e: BF16 197e12 operations/s, INT8 393e12 operations/s | Published chip maxima for selection/roofline inputs, not interval service times |
| HBM rate | Cloud v5e: 800 GiB/s = 858,993,459,200 B/s; [JAX hardware table](https://docs.jax.dev/en/latest/pallas/tpu/hardware.html): 820e9 B/s | Recommend Cloud's explicit chip-specific unit/value as the nominal source. Retain conflict, do not average or tune. Do not apply a guessed refresh derating to this published bandwidth claim |
| HBM capacity | Cloud says 16 GB; current JAX table displays 17 GB; pinned inventory in the previous dossier says 17,200,000,000 B | Exact physical/usable byte capacity unresolved. Record published strings separately. Recommend a **STUB capacity estimate** of 16,000,000,000 B with a separate 12,000,000,000 B mapper allocation budget, as in MODEL; neither establishes exact physical/usable bytes, and the actual runtime budget remains unknown |
| Local storage | JAX table: 128 MiB VMEM, 1024 KiB SMEM per TensorCore | 134,217,728 B and 1,048,576 B nominal capacities; compiler reservation/usable budget unresolved. SMEM is not accumulator memory; VMEM is not four independent SRAMs |
| Other formats | Cloud establishes INT8; JAX table additionally lists INT4 and unavailable FP8 rate | No expansion beyond BF16 decoder and raw INT8 dot controls |

The pinned JAX raw-file URLs could not be fetched by this turn's web tool; their exact
17.2e9 capacity and sentinel details remain **inherited** from READINESS/source-pins, not
freshly verified. The mutable Cloud/JAX pages were revisited for revision 2. The live JAX table independently confirms VMEM/SMEM, 820 GB/s and
394 TOP/s INT8, so the rate conflict persists. Cloud is preferred for headline rates
because it names this chip and units directly; that preference is a source-selection
recommendation, not proof that the other figure is wrong. Approximate rounding is a
possible explanation for capacity/INT8 differences, not an accepted conversion.

## Recommended model and provenance correction

[MODEL.md](MODEL.md) and [model-parameters.json](model-parameters.json) now specify a complete
nominal model: published facts, 17 reasoned numeric STUB estimates, exact service/resource
laws, finite mapping/state choices and sensitivity alternatives. U-P9 explicitly anticipates
unpublished parameters. The previous requirement for independently established timing inputs
before implementation, and the suggested target deferral on that basis, are withdrawn.

Keep the same engine, one TensorCore/four MXUs, shared VMEM, vector/reduction and scalar/control
work, aggregate HBM, explicit tiles/transfers and ordinary execution. Equal peak shares,
generic fill/drain, vector costs, logical memory credits, local budgets and startup are
model assumptions/estimates. They are not TPU facts just because the equations are precise.
The source conflicts above remain visible. No clock is inferred from peak throughput.

The strongest inputs are organization, array geometry and headline rates/capacities.
The weakest estimates are device entry (1 us nominal, diagnostic 0.1..10 us), vector
service (1 ns per ordinary 8×128 tile) and control service. HBM 200 ns and logical concurrency
also materially affect short streams/gather. Each has an explicit rationale and limitations;
the ranges are not empirical bounds, error bars or a new experiment campaign. Unknown
physical clocks/channels/transactions/banks/energy are unrepresented, not placeholders.

Use existing `SourcedValue`: finite claim/stub/source=null for numeric estimates, with
basis recorded outside the claim. No null value, rationale-on-claim or new provenance kind.
Mapped allocation/residency/dataflow choices belong in ordinary assumptions. A truly absent
required parameter refuses by name; a reasoned numeric STUB may be admitted in production
after the normal interface/implementation process. It does not need test-only admission.

## Why the installed hardware cannot be copied

`HardwareSpec` requires positive clocks, one MatrixEngine per CoreType, local SRAM bank/port
and DMA details, physical controller/channel/routing and DRAM timing fields, plus energy.
`hardware_projection`, `canonical_owners` and ordinary /4 validation consume that model.
`Compute` has core_id but no MXU index; `Fragment` fixes 256 B transactions and non-null
channels/routes. `MappedAssumptions.hbm_addressing` fixes stripe256/channel8/controller-pairs.

Native `component_admission.rs` additionally requires 256×256 arrays, eight HBM channels,
256 B requests, 32-cycle overhead/barrier and a 510-cycle wave fill/drain. The component
mapper uses four row-split cores, two SRAM slots per tile, replicated weights, no K/N
reduction tiling, BF16 output and FP32 accumulator. Production /4 pins npu-l4's data hash,
1 GHz in all domains, cold state and zero priming. None of those numbers or placements is
a sourced TPU property. Merely relaxing the hardware hash, shape bound or `--test-only`
check would preserve the wrong law and is expressly excluded.

## Remaining decision

Approve the concrete revised model/interface as one package, including its visible STUB
estimates and sensitivity limitations, then implement/verify the full 52-unit scope in one
substantial milestone. Scope approval is already recorded; no new suite or target decision
is requested. Keep TPU v5e. Published internal timing values are not prerequisites.

The nominal model has no unfilled required numeric fields. Actual compiler fusion/event
boundaries, device startup inclusion, usable allocations and retention remain unobserved;
modeled choices cannot prove correspondence. Reconcile those at their existing consumer
without claiming observations now. No held-out tuning, accuracy claim, device work or U4
closure follows. [Exact protected changes](protected-amendments.patch) remain unapplied.
