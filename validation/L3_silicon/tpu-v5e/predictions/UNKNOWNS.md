# TPU v5e unknown-parameter inventory

**All 52 accepted prediction records are complete.** This inventory is frozen with
the records and their 104 complete prepared-input/native-output archives.

The unchanged nominal reference contains **17 numeric STUB claims** and nine leaves
labelled published facts. Across the 52 completed native predictions, **16 distinct
STUBs are reported consumed**. Every STUB is listed below, including the one absent from
executed consumption. These are `kind: claim`, `provenance: stub`, `source: null`;
none is a stipulation or an observed hardware estimate. The exact hardware appears in
every prepared job and is bound by each prediction's `spec_hash`.

Values/bases are inherited unchanged from [the installed model](../../../../src/rkuarch/workload/tpu_v5e.json)
and [the premeasurement catalogue](../u4b/model-parameters.json). No parameter was tuned
in this freeze. Catalogue prospective status text is historical; Javid's
[U4 acceptance](../../../../docs/reviews/U4-closeout-acceptance.md) is operative.

## Consumed inventory

`Rows` counts native `consumed_stubs` membership, including admission/normalization reads;
it does not count dynamic accesses, establish sensitivity, or prove a timing contribution.
For example both precision rates can be read for admission even on a non-matrix unit.
All serialized hardware fields are schema-validated; absence from the executed consumption
list does not mean a field was absent from parsing. Per-case membership is retained in each
completed prediction JSON, and full native diagnostics remain in its compressed output.

| STUB | Nominal value | Unit | Rows / 52 | Inherited basis |
| --- | ---: | --- | ---: | --- |
| `hbm_capacity_bytes` | 16000000000 | byte | 52 | Conservative decimal interpretation of Cloud 16 GB; unit conflict with JAX remains. A separate 12e9-byte model allocation budget avoids depending on the upper interpretation. |
| `bf16_mxu_mac_per_s` | 24625000000000 | MAC/s | 52 | 197e12 / (2 operations per MAC * 4 MXUs); equal sustained shares at published peak is a model assumption, not four independently measured rates. |
| `int8_mxu_mac_per_s` | 49125000000000 | MAC/s | 52 | 393e12 / (2 * 4); estimates the raw INT8 service rate independently of the BF16 format law. |
| `matrix_fill_equivalent_macs` | 4161536 | MAC-equivalent | 32 | (128+128-2)*128*128 equivalent work from a generic systolic fill/drain model. This is delay-equivalent work, not executed MACs or a derived clock. |
| `vmem_bytes_per_s` | 16384000000000 | byte/s | 52 | Engineering service budget of four 4096-byte register streams per nominal 1 ns vector quantum; aggregate shared local-memory bandwidth, not a physical port count. |
| `hbm_latency_ps` | 200000 | ps | 52 | Untuned engineering prior for a DRAM access plus on-chip/controller path, at hundreds-of-ns scale. Public Pallas documentation identifies high HBM latency but gives no v5e value. |
| `hbm_issue_interval_ps` | 1000 | ps | 52 | One nominal control-service quantum per logical DMA issue; not a physical core period. |
| `hbm_max_outstanding` | 32 | count | 52 | Logical model window: 32 * 8192 B = 256 KiB, enough to cover nominal bandwidth-delay product (~172 KiB); chosen to permit saturation, not an inferred physical credit count. |
| `vector_tile_ps` | 1000 | ps | 39 | One ns for one 8x128 FP32 ordinary vector primitive is an explicit engineering scale prior. JAX supplies layout/relative cost, not this timing; no matrix-peak-to-VPU-rate inference. |
| `vector_group_startup_ps` | 2000 | ps | 39 | Two nominal vector quanta for group setup; charged once to an explicit vector group, not every primitive. |
| `reduction_cost_ratio` | 2 | ratio | 11 | Pairwise reduction stage is assigned twice ordinary vector service, reflecting documented slower cross-lane reductions; numerical multiplier is an estimate. |
| `exp_cost_ratio` | 4 | ratio | 8 | JAX classifies exp as medium cost versus cheap add/multiply; factor four is an untuned model choice, not a measured instruction ratio. |
| `reciprocal_cost_ratio` | 4 | ratio | 8 | Division/reciprocal service is modeled at four ordinary vector quanta; compiler lowering may differ. |
| `rsqrt_cost_ratio` | 8 | ratio | 6 | Conservative multi-step reciprocal-square-root estimate; no claim of an eight-instruction v5e implementation. |
| `scalar_op_ps` | 1000 | ps | 49 | One ns per scalar/index/control primitive as an engineering prior, unrelated to any asserted TPU clock. |
| `kernel_startup_ps` | 1000000 | ps | 52 | Weak engineering prior of 1 us for device executable entry/prologue/exit; chosen on a microsecond control scale, not from v5e measurements or host launch. The stress range is deliberately two orders wide and is not a physical bound. |
| `barrier_latency_ps` | 1000 | ps | 0 | One scalar-service quantum for an explicitly mapped barrier; dependency edges alone incur no extra barrier cost. |

`barrier_latency_ps` is retained in the model but no mapped explicit barrier consumes it
in this accepted suite. Dependency edges alone do not add barrier cost. The per-row lists,
not the catalogue's intended materiality categories, determine reported consumption.

## Non-numeric assumptions and claim limits

This count is a parameter inventory, not a statistical number of free fit parameters or
an uncertainty interval. The later L3 discrepancy combines method error, unknown-parameter
error, compiler/mapping mismatch and measurement-boundary differences. They are not
separated by the prepared predictions. Error remains **unknown**, calibration **stub**, and
energy **unverified**; deterministic verification supplies no accuracy badge or confidence
interval. U-C0 has its own abstraction and uses a subset of the same source/hardware data;
it is not independent physical validation of native timing.

The saved `ws-rowsplit/3` mapping and `tpu-v5e-premeasurement/3` assumptions include
payload-every-invocation, tile-packed HBM, explicit intermediates/casts, one staging slot
for gather/attention/activation packing (F5), and explicit capacity/allocation budgets.
The complete numerical assumptions and limitations are saved in every completed job. Physical
NoC, HBM bank/channel mechanisms, energy and several device counters are unrepresented.
F3 arbitration and F6 critical-path causal adjacency remain incompletely verified; their
diagnostics cannot establish physical causes. F4's direct oversized /4 refusal-code
difference remains disclosed. No compiler or device timing/counter data were observed.

All comparisons are **compiler-chosen**, steady state, device-only at the agreed whole
unit boundary. Raw INT8 matrix work is integer operations, not FLOPs. Native bytes are
executed HBM payload read+write; U-C0 bytes are logical operands. Future measured units
must preserve the exact fusion/materialization/precision/state correspondence or be
labelled incomparable, without revising these predictions.

This reference can support future evidence only for **few large systolic cores**, within
actually compared domains. It cannot support **mesh-shaped architectures**, absent NoC/
bank mechanisms, inter-chip communication or unmeasured chips. See the
[proposed family-scope ADR](../../../../docs/reviews/U5-prediction-freeze-v1/proposed-U0009.md).
