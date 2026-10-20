# TPU v5e reference readiness — prospective, 2026-10-16

> **U4b reconciliation (2026-10-20):** the current consolidated proposal is [u4b/README.md](u4b/README.md). It refreshes source conflicts, proposes the minimum reference model and records the consequential timing blocker. This older dossier remains evidence history; it is not reference admission.

No reference admission, prediction, measurement, device reservation, spend or availability
is asserted. This dossier prepares U-P11b R/U-P9/U-P10. The active
`hw/references/tpu-v5e.yaml` does not exist at the inspected main; historical 1 Hz/1×1
carrier placeholders remain unusable. No reference spec or protected schema is installed.

## Primary source inventory

Google's [v5e documentation](https://docs.cloud.google.com/tpu/docs/v5e), updated
2026-10-13 and read 2026-10-16, specifies one TensorCore/chip, four MXUs/TensorCore,
a vector unit and scalar unit; 197 TFLOP/s BF16, 393 TOP/s INT8, 16 GB HBM/chip and
800 GiB/s HBM bandwidth. The latter converts to 858,993,459,200 bytes/s; preserve the
published binary unit rather than substitute 800 decimal GB/s or an older 819 GB/s figure.
“16 GB” is retained verbatim as a capacity-unit ambiguity to resolve before a byte-valued
spec. ICI is inter-chip; its 2D torus does not establish an on-chip NoC topology. A documented
one-chip slice configuration is not proof that an account has access to one.

The [general TPU architecture page](https://docs.cloud.google.com/tpu/docs/system-architecture-tpu-vm)
(read 2026-10-16) describes pre-v6e MXUs as 128×128 MACs and BF16 multiplication with FP32
accumulation; vector units handle activations/softmax and scalar units handle control/address
work. Treat this as version-qualified architecture documentation, not measured latency.
A single installed MatrixEngine cannot silently stand for four independently schedulable
MXUs or be replaced by a guessed 256×256 array. Peak rates do not independently identify
clock, issue behavior, staging bandwidth or pipeline timing.

Google's [BF16 numerical description](https://docs.cloud.google.com/tpu/docs/bfloat16)
(read 2026-10-16) describes BF16/FP32 use, rounding and TPU treatment of subnormals. Pin the
actual compiler's dot precision/accumulation/output conversion configuration at freeze.
INT8 support is explicit in v5e's device table; the exact quantization, scale traffic,
accumulation and conversion contract still needs R agreement. FP8 throughput is not established by these Cloud sources. The separate JAX type-admission
observation below is not a peak-rate or native-contract approval.

The dated [2023-08-29 launch announcement](https://cloud.google.com/blog/products/compute/announcing-cloud-tpu-v5e-and-a3-gpus-in-ga)
provides historical identity context only. Its performance comparisons are not calibration
inputs or measurements for this project. No advertised speedup is used as a prediction.

[Source pins](source-pins.json) record immutable commits, dates and content digests for:

- [JAX profiling](https://github.com/jax-ml/jax/blob/3e7fe2c1cc042aa63b0831f24c50ab12b6abcda9/docs/profiling.md), 2026-08-30:
  trace capture must encompass completion; asynchronous dispatch requires blocking. Compile
  and transfer outside the device interval. Host wall time around a blocking call remains a
  host diagnostic, not device-only execution time.
- [XProf HLO statistics](https://github.com/openxla/xprof/blob/424d7b7041b4198fbcf5350d4750080ae799798f/docs/hlo_op_stats.md), 2025-10-31:
  compiler static FLOPs/byte estimates and profiled execution time have distinct origins.
  Derived bandwidth is not automatically a measured HBM-byte counter. Preserve self versus
  inclusive time and avoid double-counting a fused parent with its children.
- [XProf trace viewer](https://github.com/openxla/xprof/blob/0fc7262d749554782cfb57f3585b919e97097202/docs/trace_viewer.md), 2026-05-21:
  host and device timelines support boundary inspection. The chosen runtime must still
  demonstrate a stable device event for every agreed benchmark unit.

The [JAX hardware reference](https://docs.jax.dev/en/latest/pallas/tpu/hardware.html) and
[pinned inventory source](https://github.com/jax-ml/jax/blob/9e83c4450db4e51162f86b10a4626e0fffb6fd3d/jax/_src/tpu_info.py)
(snapshot 2026-07-22) provide additional v5e values: 128 MiB VMEM, 1 MiB SMEM, four MXUs,
17,200,000,000 HBM bytes, 820,000,000,000 B/s HBM and394 TOP/s INT8. Its unavailable
accumulator-count and FP8-peak sentinels are not zero-capacity/zero-throughput hardware
claims. Its dtype predicate admits selected FP8 input formats, despite unavailable FP8
peak metadata; software type acceptance does not supply a timing model. This is additional
primary evidence, not a reason to widen the proposed suite or infer a generic FP8 rate.

**Source conflict requiring R resolution:** JAX's HBM capacity/bandwidth and INT8 peak differ
from Cloud's16 GB/800 GiBps/393 TOPs. Keep both identities and units. Capacity rounding may
explain part of the discrepancy, but that is an inference, not an accepted byte value.
Do not average the numbers or choose a rate to match a future result. VMEM/SMEM capacities
are now sourced candidate fields; their mapping to the installed SRAM/operand-buffer model,
bank/port behavior and usable allocation budget remains unresolved.

Google's mutable pages have access/update dates, not invented immutable revisions. The Git
pins identify documentation, not selected runtime/tool dependencies. No JAX/TPU package was
installed and no source benchmark was executed.

## Unknowns and exact representation decisions

These are 18 unresolved *model field families*, not a count of wholly unsourced fields or
future leaf stubs (the local-memory capacities above are sourced):
core clock; other domain clocks; MXU timing/dataflow; four-MXU arbitration; operand staging;
accumulator capacity/lifetime; vector operation rates; scalar overhead; local SRAM/VMEM
model binding; banks/ports; DMA engines; DMA credits; DMA request size; on-chip topology/routes;
DRAM channel count/interleave; DRAM latency/refresh timing; synchronization latency;
energy coefficients. Source what is published; otherwise retain unknown/stub claims with
source null. Never use proposed-design stipulations to fill reference hardware gaps.
A future admitted spec must enumerate every actual leaf read, with its source/unknown
status. Eighteen families is not that final count.

R must decide how four MXUs in one TensorCore map to resources and how unavailable timing
inputs are represented without a fabricated scalar. Current positive numeric carriers cannot
be made physically usable by setting unknowns to 1. A source-only inventory can proceed;
reference execution and prediction freeze cannot. Any new carrier/schema/ADR must be an
exact unapplied proposal reviewed before installation. This dossier makes no protected edit.

## Measurement boundaries and initial state

Proposed common unit: one chip, one iteration, no collectives, `compiler-chosen` mapping,
steady/warmed executable. Archive pre/post-optimization HLO, compiled cost analysis,
compiler flags, executable identity, device placement, library/runtime/VM versions and input
hashes. Agreement must bind the actual fused unit, its mathematical work, materialized
outputs, compiler FLOPs and compiler bytes before prediction freeze. A Python function name
alone cannot establish a separable device event. A required operator that is fused remains
covered by an agreed enclosing unit; its separate row stays unresolved until that unit is
agreed, never silently deleted or duplicated into aggregate error statistics.

Proposed protocol for later agreement: compile once, place inputs before timing, 10 warm-up
invocations, then 30 separately identifiable device samples. These are draft statistical
choices, not U0012/U0024 noise qualification or an observed sufficient sample size. Record
host launch/transfer gaps separately. Cache/VMEM/HBM starting contents and warm retention
are not controllable merely by calling block_until_ready. Repeated address sets define a
warm experiment; rotating disjoint buffers is a different declared experiment. No claim of
cold DRAM, cache flushing or saturated streaming without observable evidence and a declared
state procedure. Native steady/priming behavior must match that procedure in R.

HBM read requires an observable reduction/output so XLA cannot erase it. Write needs a
runtime-dependent materialized destination; copy must prove distinct buffers and actual
copy work after optimization (no alias/donation-only result). Such fused/reduction work
belongs in both prediction and measurement. Host-to-device transfers are separately
excluded; they cannot stand in for HBM streaming. Gather uses exact page tables, valid tail
length, ordering and append semantics. Minimal launch may optimize away; zero device events
is unavailable granularity, not zero measured launch overhead.

Actual HBM counters, attribution-to-HLO correlation, device event resolution and repeat
noise remain unobserved. Missing counters remain null. Attribution will guide investigation
only after independent qualification; it cannot physically explain an error by itself.

## Work that can proceed, and first-use blockers

[SUITE.md](SUITE.md) and [suite.json](suite.json) propose 70 rows covering six classes.
[NATIVE-WORK.md](NATIVE-WORK.md) maps each operator family to existing carriers and exact R gaps.
The B agent proposes this agreement; A agreement and human scope/access decisions are
pending. Prepare exact OpSpec/v2 inputs, counts, RoPE coefficients/positions, page tables,
correctness checks and a CPU synthetic dry-run kit without hardware. This task delivers
readiness inputs, not the separately scoped U-P10 kit or a fake measurement.

Before U-P9: A/B resolve fusion granularity, shape-bin characterization, native R operators,
INT8 and four-MXU representation, exact reference unknowns, steady state and observation
coverage; both lanes sign the exact suite. Prediction freeze then commits native and
admitted analytic aggregate/per_op baselines with all first-consumer verification. Real
access/region/project/quota/allocation, compiler/runtime pin and cost ceiling need separate
human decisions before U-P10 measurement. No availability promise or host contact is made.

Optional L2 remains deferred: no matched tool comparison is needed to unblock these inputs.
SCALE-Sim could later test a matched WS tile, but its staging/overhead/dataflow convention
must match and its licence/pin/implementation overlap must be reviewed. No second engine,
installation, full fork or same-code independence claim is introduced. Missing L2 cannot
replace L1 human workings or silicon. U0024 remote/nightly/performance debt remains open.
