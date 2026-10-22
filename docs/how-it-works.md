# How rk-uarch works

rk-uarch models the timing of work on one accelerator chip. Python prepares the workload
and mapping; one Rust engine schedules the resulting operations, transfers and resource
use. A retained analytic model provides useful-work rooflines. Verification checks the
implementation against its declared laws. Silicon measurements, which have not yet been
performed for the TPU suite, are needed to assess accuracy.

This description follows the reviewed U4b implementation installed at `3626273` and its
[publication checks](reviews/U4b-native-reference-install-decision-v1/checks.json).
The earlier U3 narrative and its numerical examples remain in Git history at `85e7552`.
Those historical analytic receipts are not fresh verification of today's native code.

## From workload to prediction

1. **Describe the work and hardware.** A workload gives dimensions, operators, precision,
   state, coefficients and data dependencies. Hardware values retain their sources or
   explicit estimate status. A logical decoder layer is higher level than the many tiled
   activities that will execute it.
2. **Map the work.** Python selects the declared tiling, buffers, transfers and dependencies.
   This produces a resolved input graph. It contains work and ordering, not measured timing.
   The engine neither searches for a better mapping nor silently repairs a supplied one.
3. **Execute the model.** Rust schedules ready work subject to modeled resources, clocks,
   capacities and credits. It advances modeled time; it does not numerically multiply all
   the tensor elements. Wall-clock simulation runtime is distinct from the predicted chip
   duration, which is reported in picoseconds.
4. **Check and save.** Contract validation and the shipped independent checker reject
   inconsistent results. Ordinary replay checks saved inputs/results without rebuilding
   their mapping or needing the native executable. Their checks have the limits below.

The public command is `uarch rk-component`; its run/replay interface supports bounded
component `/4` jobs and TPU-reference `/5` jobs in the same engine. These suffixes identify
wire formats, not five simultaneously developed simulators. See the
[ordinary interface](../src/rkuarch/engines/native/ordinary.py) and
[reference interface](../contract/tpu-v5e-r-interface.md). An installed wheel and executable
can run outside a source checkout. Runtime use does not require hashing a developer's
source tree or obtaining a per-run approval. Package-version compatibility still applies;
cross-version replay is not promised.

## What timing represents

The bounded component model includes matrix scheduling, DMA, SRAM transfers, credit
lifetimes and exact rational channel service. Clock transitions round to the appropriate
edge. In the NoC0 examples, network traversal adds latency without network contention;
channel bandwidth service and SRAM ports can still serialize requests. An interval's
presence in the timeline is not by itself evidence that it acquires a contended resource.

The [GEMM worksheet](../validation/L1_limits/hand/H-L1-GEMM-01.md) derives a resident
16×256×256 BF16 operation as 1,048,576 useful MACs and 702 ns under its stated 1 GHz laws.
The [DMA worksheet](../validation/L1_limits/hand/H-L1-DMA-01.md) derives a 256-byte read
as 60 ns, including traversal, DRAM latency, service, alignment and SRAM commit. Two such
reads with two credits finish at 60 and 62 ns; with one credit they finish at 60 and 120 ns.
These are Javid's human-validated calculations with disclosed AI assistance. They establish
agreement with the stated model, not a measurement of a chip. The DMA record preserves the
correction of the earlier mistaken 64 ns two-credit answer.

The TPU reference uses its own explicit [nominal model](../validation/L3_silicon/tpu-v5e/u4b/MODEL.md),
with nine published facts and 17 numeric STUB estimates. Its mapper covers matrix, vector,
scalar, reduction and memory work, including full decoder envelopes, RoPE/casts and KV
traffic. Startup and vector/control timing are particularly uncertain. More detailed
scheduling does not upgrade these estimates to measured facts.

The retained [reference U-C0 resolver](../src/rkuarch/engines/analytic/reference.py)
calculates useful mathematical work and operand bytes. Its aggregate result takes the
maximum of total compute and memory estimates; its per-operation result sums the per-op
maxima. Native padding, local staging, latency, credits and startup are excluded from that
baseline. Comparisons must use the same declared workload and explain those differences.

## What U4 verified

The installed [52-unit suite](../validation/L3_silicon/tpu-v5e/BENCHMARK-PLAN.md) contains
12 matrix, nine memory, 24 operator, four full-layer, two gather and one minimal-kernel unit.
The retained [campaign summary](reviews/U4b-native-reference-implementation-v1/evidence/integration-summary.json)
records 156 release processes, 52 debug processes, 52 two-prime processes, 52 installed
replays and 52 priming comparisons. Its analytic comparisons are all nonshorter. These are
inherited execution records, not new runs for this document and not U5 frozen predictions.
The v2 correction/review establishes the installed loader and dependency-readiness fix;
[the handoff](reviews/U4b-native-reference-implementation-v2/README.md) separates repeated
checks from reused native evidence.

Independent arithmetic, malformed-input controls, wrong-result checks, replay, determinism
and priming tests give different kinds of evidence. A passing file-presence test for a
worksheet does not mean a new native L1 execution occurred. Successful local execution is
not hosted Linux CI or controlled-host performance qualification. Those obligations remain
under [U0024](decisions/U0024-temporary-local-verification-and-deferred-native-ci.md).

Three checker/interface findings remain explicitly unresolved: non-HBM arbitration is not
fully checked (F3), oversized direct `/4` input can use a different refusal code (F4), and
critical-path entries are not fully checked for causal adjacency (F6). Replay does reject
the reviewed impossible early-start schedule. It does not prove every possible schedule
or causal explanation correct.

The current mapping serializes gather, attention and activation packing through one
staging slot. The reviewer reported 862.2 microseconds for one simulated gather versus
19.5 microseconds from bytes/peak-bandwidth; 95% of that simulated critical path was memory
latency. This is a mapping/model observation, not a TPU measurement or a demonstrated
physical bottleneck. Predictions must carry this limitation into U5.

## What remains outside this result

U5 freezes predictions before measurements and compares device intervals at the agreed
benchmark boundaries. TPU compilation may fuse, split or eliminate work; a local mapping
is labelled **compiler-chosen**, not assumed to match XLA. Actual event boundaries,
materialization and retention remain unobserved. The
[benchmark plan](../validation/L3_silicon/tpu-v5e/BENCHMARK-PLAN.md) records those dependencies.
Git ordering checks protect committed predictions/results; they do not establish device
accuracy or authorize hardware access.

Full product characterization tables are U7 work. The existing analytic v1
[table/report workflow](u2-workflow.md) remains available with its own scope, while analytic
RoPE v2 capture and ordinary native results do not automatically become product tables.
No native full-grid or rk-sim integration claim follows from the reference suite.

Production does not import rk-sim. The vendored snapshot supplies test-only nominal
compatibility. Its installed selected-support policy separates original generation inputs,
artifact integrity and current source compatibility. Strict currentness remains required;
the old U3 wording that this migration was still unapplied is superseded by the U4 human
adoption. See [U0002](decisions/U0002-the-vendored-snapshot-and-parity-discipline.md).

STUB means the timing law remains an unvalidated estimate. Error is unknown, not zero;
energy is unverified; deterministic repetitions do not create statistical confidence bands.
The [execution plan](execution-plan.md) separates U4 readiness, U5 silicon accuracy,
remote/performance qualification and later product delivery.
