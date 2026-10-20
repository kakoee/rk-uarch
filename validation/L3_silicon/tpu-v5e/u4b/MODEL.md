# Workable pre-measurement interval model, revision 2

This replaces the published-only timing requirement in `0d817ee`. The user approved the
unchanged 52 units as **implementation scope**, not final benchmark acceptance. Recommend
this one finite nominal model for the next substantial implementation milestone. Numeric
STUB estimates are legitimate inputs; they do not require unpublished vendor data to become
available. All laws below remain proposals until interface review/installation.

## Facts, estimates and unknowns

[model-parameters.json](model-parameters.json) contains 9 published numeric facts, 17 numeric
STUB estimates, their bases, diagnostic stress endpoints, and finite mapping/state choices.
Every `value_record` uses the existing `SourcedValue` fields. Estimates are
`kind=claim, provenance=stub, source=null, date=null, rationale=null`. The explanation belongs
in this document/catalogue and existing model assumptions/limitations: `SourcedValue` forbids
rationale on claims. Do not relabel an engineering estimate `spec_derived` merely because
some arithmetic uses a published peak. No new provenance classes or approval records.

A STUB is a **real proposed finite estimate**, not missing data. The existing SourcedValue
requires a finite number; the earlier proposal's `value:null` was incompatible and is
withdrawn. A genuinely missing *required* numeric input is absent and causes ordinary
capability/input refusal with its field name. Unknown mechanisms excluded by the chosen
model are listed as unrepresented, not populated with 0 or 1. Production may use declared
STUBs after the normal implementation/interface review, without `--test-only` or a new
runtime approval token. Results expose used STUB fields and limitations and remain unvalidated.

Published facts and the Cloud/JAX conflicts remain in [REFERENCE.md](REFERENCE.md).
Additional [JAX Pallas documentation](https://docs.jax.dev/en/latest/pallas/tpu/details.html)
describes 8×128 FP32 vector layouts, padded execution, slower reductions across the last
axis, differing primitive costs, sequential control and asynchronous memory/matrix work.
It gives **no v5e vector timing**. Adopt the layout and qualitative cost ordering as model
choices; the absolute rates and multipliers below are estimates, not facts from that page.
The discussion is version-qualified/general, not proof of a particular XLA v5e lowering.

## Recommended parameter choices

Stress alternatives are sensitivity probes, not confidence intervals, guarantees of true
hardware bounds, extra benchmark rows, or new mandatory sample-count gates. They need not
form a full factorial grid. Freeze chosen values and rationale before held-out results;
record discrepancy afterward rather than tuning these values to pass G4.

| Quantity | Nominal choice | Basis and limitation; material workloads |
| --- | --- | --- |
| BF16 / INT8 service per MXU | 24.625e12 / 49.125e12 MAC/s | Chip peak / 2 / 4; assumes equal shares and peak sustained tile service before fill/staging. STUB, not measured per-MXU rate. Probe half-rate. All dots/projections/attention |
| Matrix fill/drain | 4,161,536 equivalent MACs per K slice | Generic `(128+128-2)*128*128` wave penalty; equivalent service work **not executed MACs**. Probe half/double. Small M and repeated tile launches |
| Aggregate VMEM rate | 16.384e12 B/s | Four 4096-byte streams per 1 ns vector service quantum; no physical four-port claim. Probe 4.096e12 / 32.768e12. Staging, reductions, spills |
| HBM latency | 200,000 ps (200 ns) | Engineering hundreds-of-ns DRAM/controller-path prior; no v5e measurement. Probe 50 ns / 1 us. Short memory, gather, low-concurrency cases |
| HBM issue spacing / window | 1,000 ps / 32 logical requests | One control quantum; window covers ~172 KiB nominal bandwidth-delay product with 256 KiB in flight. Probe spacing 250..4000 ps and window 8/64. Not physical DMA credits |
| Ordinary 8×128 vector primitive | 1,000 ps | Explicit 1 ns engineering service quantum, **not a clock** and not inferred from matrix peak. Probe 500..4000 ps. Underfilled decode and vector-heavy work |
| Reduction / exp / reciprocal / rsqrt | 2 / 4 / 4 / 8 vector quanta | Relative-cost guesses; reduction stage is slower than a cheap op, medium exp/divide more expensive. Probe 1..4 / 2..16 / 2..16 / 2..32. Norm/attention/SiLU/read-sum |
| Vector group setup | 2,000 ps | Two nominal quanta, once per explicit group, not each primitive. Probe 1..8 ns. Small operators/casts |
| Scalar/index work / explicit barrier | 1,000 ps each | Nominal control-service quantum, no physical frequency claim. Probe 250..4000 ps. Page lookup/dispatch/synchronization |
| Device executable startup | 1,000,000 ps (1 us) once per invocation | **Weakest estimate:** engineering microsecond-scale device entry/prologue/exit prior. No v5e timing source or host-launch substitution. Probe 0.1..10 us; actual value may lie outside. Minimal-kernel row and small operators are particularly assumption-sensitive |
| HBM capacity estimate | 16e9 B | Conservative decimal reading of Cloud's ambiguous 16 GB, kept STUB. Compare JAX's inherited 17.2e9 only for capacity sensitivity, not averaging |

The startup and absolute vector/control priors are deliberately weak. Their basis is an
engineering scale and explicit cost decomposition, not empirical v5e evidence. Accepting
this model means accepting conditional, potentially poor predictions of these mechanisms.
These are visible proposed estimates with stress alternatives, not silent placeholders or
validated physical bounds. If reviewers reject a prior, replace that concrete choice
before freeze; do not reinstate a requirement for a published value for every internal.
No scientific claim about likely error follows from the endpoints.

Model choices, kept in the ordinary assumptions vocabulary:

- One TensorCore; four MXU owners; shared VMEM, vector and control owners; one aggregate
  HBM bandwidth resource and logical DMA issue resource. No physical channel or NoC model.
- HBM allocation budget 12e9 B, VMEM budget 96 MiB, SMEM budget 512 KiB. These leave explicit
  headroom below the chosen nominal capacities; they are mapper limits, not vendor usable
  memory claims. Largest selected standalone copy uses 512 MiB of payload buffers. Layer
  live ranges and weight/KV allocations are checked, not assumed to fit a complete 8B model.
- Per-MXU logical accumulator window 512 KiB, reserved **inside shared VMEM budget**. This
  is a conservative software storage model for partial sums, not an inferred physical
  accumulator/CMEM size. Operand double buffers also count against shared VMEM. Register
  and dedicated accumulator structure remain unrepresented.
- Deterministic M chunks <=1024, N/K slices <=128. Output tile `(M,N)` stays on one MXU
  through its K chain; stable output-tile order round-robins MXUs 0..3. K/N tails pad to
  128 for service; M is a streamed row count, not padded to 1024 or 128. Preserve useful
  counts and issued padding separately. No mapping search or second policy.

## Exact scheduling laws

**Common arithmetic:** service values are rational ps. Integer event completion is the
ceiling of the exact finish. Preserve a shared bandwidth server's rational cursor across
consecutive spans; do not round each byte/span rate and accumulate rounding drift. Finite
integer/rational overflow refuses. Keep the existing kernel/tie ordering, deterministic
FIFO-ready arbitration, lifetime checks and corrected release-before-issue semantics.
The clocked B branch and `next_edge()` are unchanged. No clock is derived or populated.

**Matrix:** after required staging and one scalar dispatch quantum, a K-slice owns its MXU
for `1e12*(M*K_physical*N_physical + fill_equivalent_macs)/mac_per_s[precision]` ps.
Useful work is `2*M*K_valid*N_valid`; issued work is `2*M*K_physical*N_physical`.
Fill-equivalent work appears only as a timing assumption, not either executed count.
A shared control owner serializes dispatch, while distinct MXUs can execute concurrently.
Each rate is capped at its chosen quarter-chip share; halving a service rate also lengthens
its fill component. The four nominal shares cannot exceed the published chip peak.

A supplied graph declares read/write spans for staging and partial sums. For the initial
VMEM-backed accumulator policy, each K slice writes the FP32/INT32 partial result to its
logical window; every later slice reads the previous partial result. First slice has no
partial read. Final conversion reads the final partial once and writes the final output.
Those local transfers are charged exactly once to the shared VMEM server, not HBM, unless
an explicit capacity-driven spill mapping places them there. Matrix multiply-accumulate
already includes accumulation arithmetic: do not add another vector sum. Computation may
overlap another tile's staging only when buffer slots, live partials and owners permit it.
The native engine executes supplied choices, never silently spills/retiles.

**HBM:** split a supplied logical span at 8192 B, page boundaries and holes; never round
payload to 8192. This is mapping service granularity, not physical transaction size.
An issue gets one available window slot at a legal DMA issue edge, no earlier than readiness
and the previous issue plus `hbm_issue_interval_ps`. Its bandwidth eligibility is
`issue + hbm_latency_ps`. Service starts at max(eligibility, rational HBM cursor), lasts
`payload_bytes*1e12/hbm_peak_bytes_per_s`, then releases the slot at integer completion.
Reads and writes share the server/window. VMEM writes/reads for HBM endpoints are separate
local stages. Keep exact payload, index and output bytes. Physical transaction counts stay
null. Random-page bank/row penalties are unrepresented; page-size effects here come from
index work, boundaries, staging and available overlap, not invented DRAM row hits.

**Vector:** scalar-valued FP32 math, including `launch-minimal`, maps to the vector unit
with a 1×1 logical shape. It is **not** proof of FP arithmetic on the scalar/control unit.
For logical last axes `(r,c)`, physical elements are `8*ceil(r/8)*128*ceil(c/128)`; leading
axes multiply independent tile counts. The mapper supplies the axes and grouping; execution
must not flatten everything to hide underfill. Add/subtract/multiply/compare/select/negate,
cast and broadcast use one nominal quantum per physical 8×128 tile. Special functions use
the table's multiplier. One explicit vector group has setup once, plus its sequential typed
primitive services and declared external VMEM transfers. Register intermediates stay in
that group's declared local scope: process 8×128 work tiles with a 64 KiB transient scratch
budget reserved within VMEM (a software limit, not a physical register-file claim); explicit spills incur VMEM traffic. No implicit
capacity-free persistent cache or unreported extra materialization.

For a last-axis reduction of R rows of length L, stage s has
`A_s=ceil(L/2^(s+1))` active outputs, until `ceil(log2(L))` stages. Its physical tiles are
`ceil(R/8)*ceil(A_s/128)`; service is that count times reduction_cost_ratio*vector_tile_ps.
Useful combines total `R*(L-1)`, with odd tails forwarded, not combined with invented data.
L=1 has no combine stages. Track the reduction dependency chain, not just its total work.
Causal attention counts valid pairs as useful work but charges the declared dense/padded
score, mask and reduction operations actually executed; masking is not free.

**Control and overhead:** each dispatched matrix slice/vector group pays one scalar control
quantum; page lookup/index instructions have explicit counts and use that same owner.
HBM issues use their own serialized issue resource above; do not also charge a scalar
instruction per fragment without an explicitly supplied control task. A dependency edge is
free; only an explicit barrier task consumes barrier_latency_ps. Charge kernel_startup_ps
once before the benchmark invocation graph, including the entire layer once, never once
per HLO/member/tile. It covers device executable entry/prologue/exit only; host gaps remain
excluded. Actual device event inclusion of that work is still an observability question.

**State:** each invocation uses the same logical values/addresses and context length.
Reinitialize per-invocation output/partial/scratch lifetimes; preserve only explicitly
marked persistent SMEM coefficient-index/position/page-table metadata. The 1 MiB full
coefficient table stays in HBM; selected coefficient rows are staged per invocation. A
full-layer mapping may declare a shared read-only row for Q and K; standalone units each
stage their own row. Reload HBM payload inputs on each
invocation by default; do not assume cross-call VMEM retention of weights or activations.
Prime one invocation, report the next; compare two primes. The model may reach a trivial
fixed point under this explicit reload policy: say so, and test nontrivial metadata
retention separately. Do not infer matching device HBM traffic from that convergence.

## Work decomposition and independent expectations

The existing analytic 5*softmax_pairs / 6*RMSNorm_elements conventions remain named semantic
counts; they are **not** typed execution counts or equal-cost instructions. The R result
must retain semantic totals, typed useful and issued counts, casts, actual traffic and
service-only overhead separately. Native and analytic U-P9 baselines use the same envelope
and declared count meaning. Preserve the retained U-C0 aggregate/per-op structure under
an explicit reference profile: per-op useful compute time is matrix_ops/chip_peak plus
sum(typed useful primitive counts / effective rate). Ordinary vector effective rate is
1024*1e12/vector_tile_ps; special functions and reduction combines divide it by their cost
ratios, and useful scalar/index work uses scalar_op_ps. Per-op memory time is mathematical operand HBM bytes for the admitted analytic
scope / HBM rate; do not substitute dynamic native reload/partial traffic to force agreement. Aggregate is max(sum compute, sum memory); per_op is the sum
of per-op maxima. C0 does **not** charge native fill/padding, VMEM staging, HBM latency/
credits, vector setup, dispatch or kernel startup; list those as unrepresented. Preserve
old analytic profiles/results, and version this reference resolver/count decomposition.
No fabricated physical clock is needed to derive the effective rates.

Separately verify the native schedule against an independent **native resource-demand
lower bound**: kernel startup once plus the maximum occupied demand across exclusive
owners (each MXU separately, VPU, VMEM, HBM, control and DMA issue). This is a synthetic
verification identity, not a replacement for U-C0, a second engine or an assertion that
the old additive-compute C0 formula is a lower bound on every permitted overlap. For the
native bound, latency-only waits contribute only when their dependency/critical-path
constraint justifies it. Do not smuggle native overhead into U-C0 to make the comparison
agree, or drop overhead from the native result.

[ARITHMETIC.md](ARITHMETIC.md) fixes concrete tile/reduction/traffic/work examples and
[check_model.py](check_model.py) checks them independently of engine/count/mapper code.
They are finite mathematical fixtures, not TPU duration predictions, human L1 answers or
an executable second simulator. No 52-row performance results are generated here.

## Material uncertainty and remaining decisions together

| Selected workload | Material uncertainty to carry into interpretation |
| --- | --- |
| Small BF16/INT8 dots and decode projections | Fill/drain, MXU assignment, padded work, staging and startup; peak alone is insufficient |
| Large dots / FFN / full layer | MXU service share, VMEM partial traffic, operand reuse, HBM overlap and capacity policy |
| Norm / SiLU / softmax / RoPE | Vector layout underfill, absolute vector quantum, reduction and exp/reciprocal/rsqrt ratios, numeric conversion points |
| Read/write/copy/gather/KV | Latency, logical issue/window/granularity and retention; physical random-bank penalties remain omitted |
| Minimal kernel | Device entry estimate and event boundary dominate; this is a conditional minimal-kernel prediction, not a validated launch-latency estimate |

**Recommendation for review:** accept this finite law/parameter set, including its STUBs
and explicit reload/local-memory abstractions, as the pre-measurement implementation model.
The 52-unit scope is already approved. The exact protected interface remains the one pending
semantic decision; do not split its parameters into separate approval packets.

There is no missing required numeric model input in this nominal proposal. Actual compiler
fusion/event membership, usable allocations and retention have no defensible *observational*
bounds yet; modeled choices do not resolve those facts. They require later input/compiler/
measurement-boundary reconciliation, not a published-value gate before implementation.
Exact physical clock, channels, bank behavior and energy are unresolved but unused by this
model. Keep TPU v5e. Do not defer or change the target just because internal details remain
undocumented. If an implemented required unit truly cannot be represented or observed,
return that specific problem under the existing U0023 process. No pilot or tuning is implied.
