# U2 B1 hardware sourcing and decision inventory

Status: concrete hardware proposals, NOT accepted inputs. U0003 approval did not approve these bytes.

## Source checks and scope

Read on 2026-10-07: [Google TPU v5e](https://docs.cloud.google.com/tpu/docs/v5e) and [Tenstorrent Blackhole cards](https://docs.tenstorrent.com/aibs/blackhole/). Only those vendor pages support nonstub claims here. Dates are retrieval dates, not measurement dates. Pages are live; no immutable source snapshot is claimed.

Google lists one TensorCore with four MXUs, 16 GB HBM and **800 GiB/s**. The input records 858993459200 byte/s, not a guessed 819 GB/s. Capacity follows the printed GB as decimal; usable/binary capacity needs confirmation. One TensorCore maps trivially to a 1x1 logical grid; its four MXUs are not falsely encoded as four TensorCores. Published aggregate 197 TFLOPS is not reverse-fitted into unknown clock/MAC fields.

Tenstorrent lists p100a 28 GB GDDR6, 448 GB/s, up to 1.35 GHz and 120 Tensix cores. The clock claim is the advertised maximum, not measured sustained operation. The 1x120 reference grid is a **stub logical stand-in**, not physical placement or proof of homogeneous harvested cores. BLOCKFP8 throughput is not plain fp8 throughput. Board power/idle power are not chip tdp/static power; those chip fields remain stub. SRAM capacity units and exact usable per-core mapping need confirmation; no silent MB-to-MiB conversion.

## Decisions for Javid

- H1: approve npu-l4 numeric design choices below (2x2, 256x256 BF16-only, 1 GHz, 16 MiB/core, 32 GB HBM, 1 TB/s), or name revised stipulations. No FP16/FP8 compute or FP8 KV support is implied.
- H2: approve npu-m256 choices (16x16, 16x16 array, BF16/FP8 rates256/512 MAC/cycle, 1.2 GHz, 1 MiB/core, two counter-directed torus NoCs, 32 GB GDDR6, 512 GB/s). SRAM capacity and energy coefficient must change together.
- H3: approve reference files only as explicitly incomplete sourcing/loader inputs with quarantined numeric and categorical placeholders; recommended: no physical reference runs/L3 use until a reviewed replacement or explicit fidelity limitation resolves each consumed placeholder. This is an input-readiness decision, not permission to infer evidence.
- H4: confirm source operating-point/unit interpretations and obtain chip-level power, clock/MXU mapping, physical grid/harvesting, vector rates, SRAM/DMA details, DRAM organization/timings and energy facts. No guessed preset or inferred timing conversion is supplied.

## Placeholder semantics and structural limitations

The accepted HardwareSpec requires finite positive numbers for many unknown fields. A genuine stub still needs a numeric carrier. Reference unknowns use conspicuous 1-unit stand-ins (120 columns only to retain the published core total without claiming placement); block-scale0 denotes the plain BF16 representation, not unknown execution cost. These numbers are NOT estimates, citations, accepted assumptions or useful performance inputs. Zero energy/latency facts are not invented. No shared type is changed to admit nulls. If quarantined complete templates are unacceptable, keep reference execution blocked while sourcing actual values; do not silently promote sentinels.

Reference category choices (weight_stationary, mesh/bidirectional, noc_semaphore, round_robin, fr_fcfs/open, one controller at [0,0], no shared SRAM, BF16-only declared subset) are unsupported representation placeholders. Absence of shared SRAM or extra formats is not a claim about silicon. clock scales_with_core is a modelling declaration, not DVFS evidence. timing_source=direct with timing_preset=null means no fallback; every reference timing is stub pending a real vendor/JEDEC or explicitly pinned preset source. Channel/controller correspondence and physical placement are unresolved.

Design DRAM timings are explicit illustrative stipulations at the declared DRAM clock, not JEDEC facts. NoC, DMA, buffers, sync and energy are fully specified questions for review but unrepresented by U-C0 timing as applicable. No dependency on a future mapping or energy implementation is introduced.

## Complete numeric leaf inventory

Each path/value below is the reviewable input, not an output metric. The YAML header enumerates every reference stub. Source claims are spec_derived only; no measurements exist.

### hw/designs/npu-l4.yaml

Claims 0; stipulations 59; stubs 0.

| Path | Value | Unit | Classification |
| --- | ---: | --- | --- |
| `clock_domains.core.freq_hz` | 1000000000.0 | Hz | stipulation |
| `clock_domains.noc.freq_hz` | 1000000000.0 | Hz | stipulation |
| `clock_domains.dram.freq_hz` | 1000000000.0 | Hz | stipulation |
| `cores.grid.rows` | 2.0 | count | stipulation |
| `cores.grid.cols` | 2.0 | count | stipulation |
| `cores.core_type.matrix_engine.array.rows` | 256.0 | count | stipulation |
| `cores.core_type.matrix_engine.array.cols` | 256.0 | count | stipulation |
| `cores.core_type.matrix_engine.macs_per_cycle.bf16` | 65536.0 | MAC/cycle | stipulation |
| `cores.core_type.matrix_engine.accumulator_bytes` | 262144.0 | byte | stipulation |
| `cores.core_type.matrix_engine.operand_buffer_bytes` | 1048576.0 | byte | stipulation |
| `cores.core_type.matrix_engine.operand_bytes_per_cycle` | 1024.0 | byte/cycle | stipulation |
| `cores.core_type.vector_engine.ops_per_cycle` | 256.0 | op/cycle | stipulation |
| `cores.core_type.sram.bytes` | 16777216.0 | byte | stipulation |
| `cores.core_type.sram.banks` | 32.0 | count | stipulation |
| `cores.core_type.sram.bytes_per_cycle_per_bank` | 32.0 | byte/cycle | stipulation |
| `cores.core_type.dma.engines` | 4.0 | count | stipulation |
| `cores.core_type.dma.bytes_per_cycle` | 256.0 | byte/cycle | stipulation |
| `cores.core_type.dma.max_outstanding` | 32.0 | count | stipulation |
| `cores.core_type.dma.request_bytes` | 256.0 | byte | stipulation |
| `cores.core_type.job_overhead_cycles` | 32.0 | cycle | stipulation |
| `sync.barrier_latency_cycles` | 32.0 | cycle | stipulation |
| `nocs[0].link_bytes_per_cycle` | 64.0 | byte/cycle | stipulation |
| `nocs[0].router_latency_cycles` | 2.0 | cycle | stipulation |
| `nocs[0].virtual_channels` | 4.0 | count | stipulation |
| `nocs[0].buffer_flits` | 8.0 | count | stipulation |
| `memory.interleave.granularity_bytes` | 256.0 | byte | stipulation |
| `memory.controllers[0].read_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[0].write_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[0].noc_credits` | 32.0 | count | stipulation |
| `memory.controllers[1].read_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[1].write_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[1].noc_credits` | 32.0 | count | stipulation |
| `memory.controllers[2].read_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[2].write_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[2].noc_credits` | 32.0 | count | stipulation |
| `memory.controllers[3].read_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[3].write_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[3].noc_credits` | 32.0 | count | stipulation |
| `memory.dram.channels` | 8.0 | count | stipulation |
| `memory.dram.bw_bytes_per_s` | 1000000000000.0 | byte/s | stipulation |
| `memory.dram.capacity_bytes` | 32000000000.0 | byte | stipulation |
| `memory.dram.organization.ranks` | 1.0 | count | stipulation |
| `memory.dram.organization.bank_groups` | 4.0 | count | stipulation |
| `memory.dram.organization.banks_per_group` | 4.0 | count | stipulation |
| `memory.dram.organization.row_bytes` | 2048.0 | byte | stipulation |
| `memory.dram.timing.t_rcd_cycles` | 16.0 | cycle | stipulation |
| `memory.dram.timing.t_rp_cycles` | 16.0 | cycle | stipulation |
| `memory.dram.timing.t_cl_cycles` | 16.0 | cycle | stipulation |
| `memory.dram.timing.t_rfc_cycles` | 350.0 | cycle | stipulation |
| `memory.dram.timing.t_refi_cycles` | 3900.0 | cycle | stipulation |
| `formats.bf16.accumulate_bytes` | 4.0 | byte | stipulation |
| `formats.bf16.block_scale_bytes` | 0.0 | byte | stipulation |
| `energy.pj_per_mac.bf16` | 0.4 | pJ/MAC | stipulation |
| `energy.pj_per_byte.sram` | 1.0 | pJ/byte | stipulation |
| `energy.pj_per_byte.noc_hop` | 2.0 | pJ/byte | stipulation |
| `energy.pj_per_byte.dram` | 20.0 | pJ/byte | stipulation |
| `energy.voltage_ratio.1.0` | 1.0 | ratio | stipulation |
| `static_power_w` | 40.0 | W | stipulation |
| `tdp_w` | 300.0 | W | stipulation |

### hw/designs/npu-m256.yaml

Claims 0; stipulations 67; stubs 0.

| Path | Value | Unit | Classification |
| --- | ---: | --- | --- |
| `clock_domains.core.freq_hz` | 1200000000.0 | Hz | stipulation |
| `clock_domains.noc.freq_hz` | 1000000000.0 | Hz | stipulation |
| `clock_domains.dram.freq_hz` | 1000000000.0 | Hz | stipulation |
| `cores.grid.rows` | 16.0 | count | stipulation |
| `cores.grid.cols` | 16.0 | count | stipulation |
| `cores.core_type.matrix_engine.array.rows` | 16.0 | count | stipulation |
| `cores.core_type.matrix_engine.array.cols` | 16.0 | count | stipulation |
| `cores.core_type.matrix_engine.macs_per_cycle.bf16` | 256.0 | MAC/cycle | stipulation |
| `cores.core_type.matrix_engine.macs_per_cycle.fp8` | 512.0 | MAC/cycle | stipulation |
| `cores.core_type.matrix_engine.accumulator_bytes` | 16384.0 | byte | stipulation |
| `cores.core_type.matrix_engine.operand_buffer_bytes` | 65536.0 | byte | stipulation |
| `cores.core_type.matrix_engine.operand_bytes_per_cycle` | 64.0 | byte/cycle | stipulation |
| `cores.core_type.vector_engine.ops_per_cycle` | 32.0 | op/cycle | stipulation |
| `cores.core_type.sram.bytes` | 1048576.0 | byte | stipulation |
| `cores.core_type.sram.banks` | 16.0 | count | stipulation |
| `cores.core_type.sram.bytes_per_cycle_per_bank` | 16.0 | byte/cycle | stipulation |
| `cores.core_type.dma.engines` | 2.0 | count | stipulation |
| `cores.core_type.dma.bytes_per_cycle` | 32.0 | byte/cycle | stipulation |
| `cores.core_type.dma.max_outstanding` | 16.0 | count | stipulation |
| `cores.core_type.dma.request_bytes` | 128.0 | byte | stipulation |
| `cores.core_type.job_overhead_cycles` | 48.0 | cycle | stipulation |
| `sync.barrier_latency_cycles` | 64.0 | cycle | stipulation |
| `nocs[0].link_bytes_per_cycle` | 32.0 | byte/cycle | stipulation |
| `nocs[0].router_latency_cycles` | 3.0 | cycle | stipulation |
| `nocs[0].virtual_channels` | 4.0 | count | stipulation |
| `nocs[0].buffer_flits` | 8.0 | count | stipulation |
| `nocs[1].link_bytes_per_cycle` | 32.0 | byte/cycle | stipulation |
| `nocs[1].router_latency_cycles` | 3.0 | cycle | stipulation |
| `nocs[1].virtual_channels` | 4.0 | count | stipulation |
| `nocs[1].buffer_flits` | 8.0 | count | stipulation |
| `memory.interleave.granularity_bytes` | 256.0 | byte | stipulation |
| `memory.controllers[0].read_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[0].write_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[0].noc_credits` | 32.0 | count | stipulation |
| `memory.controllers[1].read_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[1].write_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[1].noc_credits` | 32.0 | count | stipulation |
| `memory.controllers[2].read_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[2].write_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[2].noc_credits` | 32.0 | count | stipulation |
| `memory.controllers[3].read_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[3].write_queue_depth` | 32.0 | count | stipulation |
| `memory.controllers[3].noc_credits` | 32.0 | count | stipulation |
| `memory.dram.channels` | 8.0 | count | stipulation |
| `memory.dram.bw_bytes_per_s` | 512000000000.0 | byte/s | stipulation |
| `memory.dram.capacity_bytes` | 32000000000.0 | byte | stipulation |
| `memory.dram.organization.ranks` | 1.0 | count | stipulation |
| `memory.dram.organization.bank_groups` | 4.0 | count | stipulation |
| `memory.dram.organization.banks_per_group` | 4.0 | count | stipulation |
| `memory.dram.organization.row_bytes` | 2048.0 | byte | stipulation |
| `memory.dram.timing.t_rcd_cycles` | 16.0 | cycle | stipulation |
| `memory.dram.timing.t_rp_cycles` | 16.0 | cycle | stipulation |
| `memory.dram.timing.t_cl_cycles` | 16.0 | cycle | stipulation |
| `memory.dram.timing.t_rfc_cycles` | 350.0 | cycle | stipulation |
| `memory.dram.timing.t_refi_cycles` | 3900.0 | cycle | stipulation |
| `formats.bf16.accumulate_bytes` | 4.0 | byte | stipulation |
| `formats.bf16.block_scale_bytes` | 0.0 | byte | stipulation |
| `formats.fp8.accumulate_bytes` | 4.0 | byte | stipulation |
| `formats.fp8.block_scale_bytes` | 0.0 | byte | stipulation |
| `energy.pj_per_mac.bf16` | 0.4 | pJ/MAC | stipulation |
| `energy.pj_per_mac.fp8` | 0.2 | pJ/MAC | stipulation |
| `energy.pj_per_byte.sram` | 0.5 | pJ/byte | stipulation |
| `energy.pj_per_byte.noc_hop` | 2.0 | pJ/byte | stipulation |
| `energy.pj_per_byte.dram` | 20.0 | pJ/byte | stipulation |
| `energy.voltage_ratio.1.0` | 1.0 | ratio | stipulation |
| `static_power_w` | 60.0 | W | stipulation |
| `tdp_w` | 300.0 | W | stipulation |

### hw/references/tpu-v5e.yaml

Claims 50; stipulations 0; stubs 46.

| Path | Value | Unit | Classification |
| --- | ---: | --- | --- |
| `clock_domains.core.freq_hz` | 1.0 | Hz | stub |
| `clock_domains.noc.freq_hz` | 1.0 | Hz | stub |
| `clock_domains.dram.freq_hz` | 1.0 | Hz | stub |
| `cores.grid.rows` | 1.0 | count | spec_derived |
| `cores.grid.cols` | 1.0 | count | spec_derived |
| `cores.core_type.matrix_engine.array.rows` | 1.0 | count | stub |
| `cores.core_type.matrix_engine.array.cols` | 1.0 | count | stub |
| `cores.core_type.matrix_engine.macs_per_cycle.bf16` | 1.0 | MAC/cycle | stub |
| `cores.core_type.matrix_engine.accumulator_bytes` | 1.0 | byte | stub |
| `cores.core_type.matrix_engine.operand_buffer_bytes` | 1.0 | byte | stub |
| `cores.core_type.matrix_engine.operand_bytes_per_cycle` | 1.0 | byte/cycle | stub |
| `cores.core_type.vector_engine.ops_per_cycle` | 1.0 | op/cycle | stub |
| `cores.core_type.sram.bytes` | 1.0 | byte | stub |
| `cores.core_type.sram.banks` | 1.0 | count | stub |
| `cores.core_type.sram.bytes_per_cycle_per_bank` | 1.0 | byte/cycle | stub |
| `cores.core_type.dma.engines` | 1.0 | count | stub |
| `cores.core_type.dma.bytes_per_cycle` | 1.0 | byte/cycle | stub |
| `cores.core_type.dma.max_outstanding` | 1.0 | count | stub |
| `cores.core_type.dma.request_bytes` | 1.0 | byte | stub |
| `cores.core_type.job_overhead_cycles` | 1.0 | cycle | stub |
| `sync.barrier_latency_cycles` | 1.0 | cycle | stub |
| `nocs[0].link_bytes_per_cycle` | 1.0 | byte/cycle | stub |
| `nocs[0].router_latency_cycles` | 1.0 | cycle | stub |
| `nocs[0].virtual_channels` | 1.0 | count | stub |
| `nocs[0].buffer_flits` | 1.0 | count | stub |
| `memory.interleave.granularity_bytes` | 1.0 | byte | stub |
| `memory.controllers[0].read_queue_depth` | 1.0 | count | stub |
| `memory.controllers[0].write_queue_depth` | 1.0 | count | stub |
| `memory.controllers[0].noc_credits` | 1.0 | count | stub |
| `memory.dram.channels` | 1.0 | count | stub |
| `memory.dram.bw_bytes_per_s` | 858993459200.0 | byte/s | spec_derived |
| `memory.dram.capacity_bytes` | 16000000000.0 | byte | spec_derived |
| `memory.dram.organization.ranks` | 1.0 | count | stub |
| `memory.dram.organization.bank_groups` | 1.0 | count | stub |
| `memory.dram.organization.banks_per_group` | 1.0 | count | stub |
| `memory.dram.organization.row_bytes` | 1.0 | byte | stub |
| `memory.dram.timing.t_rcd_cycles` | 1.0 | cycle | stub |
| `memory.dram.timing.t_rp_cycles` | 1.0 | cycle | stub |
| `memory.dram.timing.t_cl_cycles` | 1.0 | cycle | stub |
| `memory.dram.timing.t_rfc_cycles` | 1.0 | cycle | stub |
| `memory.dram.timing.t_refi_cycles` | 1.0 | cycle | stub |
| `formats.bf16.accumulate_bytes` | 1.0 | byte | stub |
| `formats.bf16.block_scale_bytes` | 0.0 | byte | stub |
| `energy.pj_per_mac.bf16` | 1.0 | pJ/MAC | stub |
| `energy.pj_per_byte.sram` | 1.0 | pJ/byte | stub |
| `energy.pj_per_byte.noc_hop` | 1.0 | pJ/byte | stub |
| `energy.pj_per_byte.dram` | 1.0 | pJ/byte | stub |
| `energy.voltage_ratio.1.0` | 1.0 | ratio | stub |
| `static_power_w` | 1.0 | W | stub |
| `tdp_w` | 1.0 | W | stub |

### hw/references/blackhole-p100a.yaml

Claims 50; stipulations 0; stubs 47.

| Path | Value | Unit | Classification |
| --- | ---: | --- | --- |
| `clock_domains.core.freq_hz` | 1350000000.0 | Hz | spec_derived |
| `clock_domains.noc.freq_hz` | 1.0 | Hz | stub |
| `clock_domains.dram.freq_hz` | 1.0 | Hz | stub |
| `cores.grid.rows` | 1.0 | count | stub |
| `cores.grid.cols` | 120.0 | count | stub |
| `cores.core_type.matrix_engine.array.rows` | 1.0 | count | stub |
| `cores.core_type.matrix_engine.array.cols` | 1.0 | count | stub |
| `cores.core_type.matrix_engine.macs_per_cycle.bf16` | 1.0 | MAC/cycle | stub |
| `cores.core_type.matrix_engine.accumulator_bytes` | 1.0 | byte | stub |
| `cores.core_type.matrix_engine.operand_buffer_bytes` | 1.0 | byte | stub |
| `cores.core_type.matrix_engine.operand_bytes_per_cycle` | 1.0 | byte/cycle | stub |
| `cores.core_type.vector_engine.ops_per_cycle` | 1.0 | op/cycle | stub |
| `cores.core_type.sram.bytes` | 1.0 | byte | stub |
| `cores.core_type.sram.banks` | 1.0 | count | stub |
| `cores.core_type.sram.bytes_per_cycle_per_bank` | 1.0 | byte/cycle | stub |
| `cores.core_type.dma.engines` | 1.0 | count | stub |
| `cores.core_type.dma.bytes_per_cycle` | 1.0 | byte/cycle | stub |
| `cores.core_type.dma.max_outstanding` | 1.0 | count | stub |
| `cores.core_type.dma.request_bytes` | 1.0 | byte | stub |
| `cores.core_type.job_overhead_cycles` | 1.0 | cycle | stub |
| `sync.barrier_latency_cycles` | 1.0 | cycle | stub |
| `nocs[0].link_bytes_per_cycle` | 1.0 | byte/cycle | stub |
| `nocs[0].router_latency_cycles` | 1.0 | cycle | stub |
| `nocs[0].virtual_channels` | 1.0 | count | stub |
| `nocs[0].buffer_flits` | 1.0 | count | stub |
| `memory.interleave.granularity_bytes` | 1.0 | byte | stub |
| `memory.controllers[0].read_queue_depth` | 1.0 | count | stub |
| `memory.controllers[0].write_queue_depth` | 1.0 | count | stub |
| `memory.controllers[0].noc_credits` | 1.0 | count | stub |
| `memory.dram.channels` | 1.0 | count | stub |
| `memory.dram.bw_bytes_per_s` | 448000000000.0 | byte/s | spec_derived |
| `memory.dram.capacity_bytes` | 28000000000.0 | byte | spec_derived |
| `memory.dram.organization.ranks` | 1.0 | count | stub |
| `memory.dram.organization.bank_groups` | 1.0 | count | stub |
| `memory.dram.organization.banks_per_group` | 1.0 | count | stub |
| `memory.dram.organization.row_bytes` | 1.0 | byte | stub |
| `memory.dram.timing.t_rcd_cycles` | 1.0 | cycle | stub |
| `memory.dram.timing.t_rp_cycles` | 1.0 | cycle | stub |
| `memory.dram.timing.t_cl_cycles` | 1.0 | cycle | stub |
| `memory.dram.timing.t_rfc_cycles` | 1.0 | cycle | stub |
| `memory.dram.timing.t_refi_cycles` | 1.0 | cycle | stub |
| `formats.bf16.accumulate_bytes` | 1.0 | byte | stub |
| `formats.bf16.block_scale_bytes` | 0.0 | byte | stub |
| `energy.pj_per_mac.bf16` | 1.0 | pJ/MAC | stub |
| `energy.pj_per_byte.sram` | 1.0 | pJ/byte | stub |
| `energy.pj_per_byte.noc_hop` | 1.0 | pJ/byte | stub |
| `energy.pj_per_byte.dram` | 1.0 | pJ/byte | stub |
| `energy.voltage_ratio.1.0` | 1.0 | ratio | stub |
| `static_power_w` | 1.0 | W | stub |
| `tdp_w` | 1.0 | W | stub |
