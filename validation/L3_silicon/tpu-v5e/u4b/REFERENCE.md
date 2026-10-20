# Recommended TPU v5e representation

Preparation at `c6438fe42fe458fc8f75af884c9c04b95ff4f96a`; no installed spec or admission.

## Evidence reconciliation

Accessed 2026-10-20. Sources are facts about published specifications, not silicon results.
The existing [source pins](../source-pins.json) remain documentation pins, not runtime pins.

| Property | Evidence and resolution | Use |
| --- | --- | --- |
| Chip organization | [Cloud v5e](https://docs.cloud.google.com/tpu/docs/v5e): one TensorCore, four MXUs, one vector and one scalar unit | One shared local-memory domain, four separately identified matrix owners; **not** four cores with replicated VMEM |
| Array | [Cloud architecture](https://docs.cloud.google.com/tpu/docs/system-architecture-tpu-vm): pre-v6e MXUs are 128×128; BF16 multiply, FP32 accumulation | Keep array dimensions and accumulation precision; independent scheduling/issue rules remain unknown |
| Peaks | Cloud v5e: BF16 197e12 operations/s, INT8 393e12 operations/s | Published chip maxima for selection/roofline inputs, not interval service times |
| HBM rate | Cloud v5e: 800 GiB/s = 858,993,459,200 B/s; [JAX hardware table](https://docs.jax.dev/en/latest/pallas/tpu/hardware.html): 820e9 B/s | Recommend Cloud's explicit chip-specific unit/value as the nominal source. Retain conflict, do not average or tune. Do not apply a guessed refresh derating to this published effective-rate claim |
| HBM capacity | Cloud says 16 GB; current JAX table displays 17 GB; pinned inventory in the previous dossier says 17,200,000,000 B | Exact physical/usable byte capacity unresolved. Record published strings separately. Recommend a **workload allocation ceiling** of 16,000,000,000 B, explicitly a conservative modeling limit, not a new physical claim; allocated runtime budget still unknown |
| Local storage | JAX table: 128 MiB VMEM, 1024 KiB SMEM per TensorCore | 134,217,728 B and 1,048,576 B nominal capacities; compiler reservation/usable budget unresolved. SMEM is not accumulator memory; VMEM is not four independent SRAMs |
| Other formats | Cloud establishes INT8; JAX table additionally lists INT4 and unavailable FP8 rate | No expansion beyond BF16 decoder and raw INT8 dot controls |

The pinned JAX raw-file URLs could not be fetched by this turn's web tool; their exact
17.2e9 capacity and sentinel details are **inherited** from READINESS/source-pins, not
freshly verified. The live JAX table independently confirms VMEM/SMEM, 820 GB/s and
394 TOP/s INT8, so the rate conflict persists. Cloud is preferred for headline rates
because it names this chip and units directly; that preference is a source-selection
recommendation, not proof that the other figure is wrong. Approximate rounding is a
possible explanation for capacity/INT8 differences, not an accepted conversion.

## Smallest useful model

Recommend a scoped extension of the existing interval model: one TensorCore, four matrix
owners sharing VMEM, one vector/reduction owner, one scalar/control owner and **one aggregate
HBM service resource**. The last is a model abstraction, not a claim of one physical channel.
Use explicit mapped tensor tiles, dependencies, buffer lifetimes and useful versus issued
work; reuse the event kernel and resource scheduling. No inter-chip collectives/ICI, physical
NoC, DRAM bank/refresh model or general hardware topology framework is needed for this suite.
No energy estimate is needed. All omitted mechanisms remain named as unrepresented.

This is a proposed R law, **not** permission to relabel the component model or C0 peak-rate
arithmetic as verified C1. Physical internal clock is unknown. Prefer absolute-time service
parameters (ps and work/s) for this narrowly scoped resource model rather than an invented
clock. The existing kernel handles rational time; this requires a reviewed explicit model
version and carrier transition. Clocked B execution and `next_edge()` remain unchanged.
If the owners instead require a cycle-accurate MXU interpretation, a sourced clock and
issue/fill rules are prerequisites; throughput divided by MAC count is not such a source.

| Required representation | Minimum inputs and semantics | What is still missing |
| --- | --- | --- |
| Matrix | 4 resource IDs on core 0; 128×128 shape; BF16→FP32 and signed INT8→INT32; M/N/K tiles, partial-sum lifetime, useful/issued MACs, startup and tile service law | Per-precision service/issue law, startup/fill/drain and inter-MXU issue sharing, accumulator capacity, staging rate/capacity. Dividing the chip peak by 4 is only an aggregate upper bound |
| VMEM | Shared allocation ranges and lifetimes, operand staging and materialized intermediates; capacity limit at most published nominal size | Usable allocation budget, transfer service rate and overlap/arbitration. No invented bank count/ports |
| HBM | Explicit read/write payload spans, shared aggregate byte service, request startup and finite outstanding window; tail byte counts | Startup/latency and concurrency/issue behavior. Physical transaction quantum unknown: payload is not a transaction count. Gather depends on these even when bandwidth is known |
| Vector | Per-operation work records for add/mul/compare, reduction, exp/reciprocal/rsqrt, and cast; one shared owner; FP32 reduction/rotary arithmetic | Rates and startup, reduction scheduling, special-function versus ordinary arithmetic service. BF16 matrix peak cannot supply these |
| Scalar/control | Address/page-index work and minimal runtime scalar add; kernel startup separate from mathematical add | Device dispatch/startup latency and scalar service. A barrier's B constant is not a launch estimate |
| State | One simulation primes the fixed graph once, reports the next invocation; optional second priming comparison. Explicit persisted weights/KV/coefficient residency and per-iteration scratch | What compiled runtime retains. Warm invocations alone do not prove VMEM residency or cold HBM |

Admission must enumerate the **actual used leaves**, including their source or missing status.
Unknown required values are absent/null in the proposal and refuse prediction, not 0 or 1.
The 18 families in the prior dossier are not an exact unknown-leaf count. The absolute-time
abstraction removes the need for physical clock, NoC topology, physical channels/interleave,
refresh and energy inputs; it does **not** remove the matrix, vector, memory-latency or startup
unknowns listed above. A source-only inventory is not a runnable HardwareSpec.

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

## Consequential choice, with recommendation

**No credible complete-suite native prediction follows from the public sources inspected.**
The launch row alone needs unknown device startup, and attention/normalization need vector
and reduction timing that peak matrix/HBM data cannot determine. Even isolated matrix
underfill cannot be identified from peak throughput. The analytic full-layer baseline has
the same missing vector-rate problem; it is not a loophole.

Recommend retaining TPU v5e and the 52-unit workload proposal, approving the narrow structural
and work-accounting interface, and implementing all source-independent work first. Before
numerical reference admission, the human model/target decision is: **can this project supply
an independently justified, pre-measurement timing model for these missing service laws?**
If yes, bind that source/model and exact values before dependent timing implementation.
If no, explicitly defer the TPU prediction milestone or change the target/model requirement
under U0023. Do not commission an unfunded pilot, invent reference stipulations, or accept a
peak-only model as the complete U-P9 campaign. This package recommends deferral of numerical
admission over guessed values; it does not request 18 unrelated approvals or claim readiness.

The [unapplied amendment](protected-amendments.patch) makes the representation and refusal
boundary concrete. It installs no serializer or executable admission. Timing calibration,
if ever proposed, needs a separate development/held-out decision and is not authorized here.
