# U2 B1 decision package v1

Status: **PENDING JAVID**. Decision ID: U2-B1-decision-v1.
U0003 and its six recommendations are already accepted and are not being reopened.
This decision covers concrete U0004 text and hardware inputs, which the U0003 approval
explicitly left separate. It does not approve B runtime or close B-F16/U2.

Read [coordinator reconciliation](U2-B1-coordinator-reconciliation.md) for verification and
A1 dependencies. Exact B source package: U2-inputs/B1-05daf76bfda1/, manifest SHA256
05daf76bfda1b71a6307bcfeab6fd60ea4045676525991205543454d5cc20747.

## D1 — U0004 text

Recommend accepting [the exact U0004 candidate](U2-B1-U0004-candidate.md),
SHA256 `79269d86dcb7381fd1e70c382e9bd4fa1384d0121ba69ec531c9fe23a18076f1`.

It is B's proposed U0004 (original hash
090482a0f71cb2af9a8d4d5d813e6602e20a62d1dfcb7d1288e600ec0d023cdc) plus this one explicit
U-P4 consequence: “This ceiling can be commercially uncomfortable; it is the thesis applied
without exceptions.” No substantive badge/evidence/display rule changes.
The draft's PROPOSED/awaiting labels will be superseded by the subsequent approval record,
as with U0003, while these exact source bytes remain preserved.

## D2 — H1: npu-l4

Recommend accepting the exact YAML as a **stipulated design input**, not validated hardware:
[hw/designs/npu-l4.yaml](U2-inputs/B1-05daf76bfda1/hw/designs/npu-l4.yaml),
SHA256 `41731f6ac7fe99aaf221edaf917ffdd03cd0fcdd8149ee5f5110bfe42a5911c0`.

Headline choices: 2x2 cores, 256x256 BF16-only matrix arrays at 1 GHz, 16 MiB SRAM/core,
32 GB HBM2e at 1 TB/s. BF16-only declaration does not permit FP8 KV/compute or FP16 compute.
Full approval includes **all 59 sourced stipulations**: vector rate, buffers, SRAM banks,
DMA, mesh links, barrier/overhead, controllers/queues, illustrative direct DRAM organization/
timings, energy coefficients and power. Also includes weight-stationary dataflow, bidirectional
mesh, hardware barrier, no shared SRAM, fixed NoC/DRAM clocks, round-robin interleave,
four attached controllers with FR-FCFS/open-page policy and no timing-preset fallback.

The accepted nominal efficiency1.0 remains a separate labelled model assumption.
Acceptance does not measure any of these values or validate energy/performance.
Change any consequential value by an explicit revised input and identity, not silent tuning.

## D3 — H2: npu-m256

Recommend accepting the exact YAML as a **stipulated design input**:
[hw/designs/npu-m256.yaml](U2-inputs/B1-05daf76bfda1/hw/designs/npu-m256.yaml),
SHA256 `e12d08d40e7b3c0e7ab1443141745a6c082ee544ecfc43c5609c8cd289a35d9e`.

Headline choices: 16x16 cores, 16x16 arrays, BF16/FP8 256/512 MAC/cycle/core at 1.2 GHz,
1 MiB SRAM/core, two counter-directed torus networks, 32 GB GDDR6 at 512 GB/s.
Full approval includes **all 67 sourced stipulations**, including vector/DMA/buffer/NoC/
controller/timing/energy/power values and the coupled SRAM capacity/energy choices.
Categorical settings include weight-stationary dataflow, NoC semaphore sync, no shared SRAM,
fixed NoC/DRAM clocks, round-robin interleave, four corner controllers with FR-FCFS/open-page
policy and direct illustrative DRAM timings without a preset.

The full numeric inventory for both designs is
[hw/U2-sourcing-inventory.md](U2-inputs/B1-05daf76bfda1/hw/U2-sourcing-inventory.md),
SHA256 `6cfe2e0441bc125e10b065f925edd03b8f18417d1d0af78495867b95a8b5bc01`.
Approval must cover that complete input, not merely the headline values in this summary.

## D4 — H3/H4: retain references as incomplete drafts only

Recommend retaining these exact files as quarantined **sourcing/loader drafts**, with no
authorization for physical reference runs, performance reporting or L3 evidence:

- [TPU v5e](U2-inputs/B1-05daf76bfda1/hw/references/tpu-v5e.yaml):
  `acea41f651a5f63e1697937f3879364e5f4342249efeaff1dcc6b6b4345a898d`.
- [Blackhole p100a](U2-inputs/B1-05daf76bfda1/hw/references/blackhole-p100a.yaml):
  `cdd1a51cc9c181b2c9062e8c46ad79989f6873734602152059b05ca363ef3371`.

Numeric positivity in HardwareSpec forced placeholders; schema validity is not physical
plausibility. Comments and stub badges do not by themselves enforce execution quarantine.
For now keep them in preserved review inputs rather than installing them as approved active
runtime specs. Any later executable fixture must distinguish loader-only tests from chip
predictions. No new generic type or broad ban on all genuine stub-backed predictions is
introduced by this file-specific disposition.

Retain the exact cited printed vendor facts with their qualifications; leave usable-capacity,
binary/decimal interpretation, sustained-clock, physical-layout and other missing facts open.
Require reviewed replacements or an explicitly reviewed fidelity limitation before consuming
an unresolved field in a physical reference run. Do not infer a full runnable-reference
deliverable, validate a placeholder, waive an exit or promise a reference-acquisition schedule.

## Suggested reply and consequence

“Approve U2-B1-decision-v1: the U0004 candidate, the exact H1/H2 stipulated designs and
the draft-only reference disposition. Keep A1 API reconciliation, generation/adoption,
commit/push and sprint closure separate.”

Or name D1/D2/D3/D4 and the exact change you want.
After approval, the coordinator records it and prepares the appropriate separate additions
to the common authority; the immutable 262-file baseline v1 remains intact. A1's submitted
APIs still need reconciliation before dependent B implementation. No implementation,
artifact adoption, commit/push/tag or final review verdict is implied by this decision.
