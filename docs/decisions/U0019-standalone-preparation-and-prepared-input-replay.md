# U0019 — Standalone preparation and prepared-input replay

**Status:** accepted architectural direction; concrete schemas and implementation remain
pending. Javid approved this record for commit on 2026-10-06.

**Date:** 2026-10-06.

**Decision owner:** Javid (@jjaffari), acting across both U1 lanes while Reza is off duty.
Javid approved amending the plan and prompts while preserving standalone operation.
This records that authorization; it does not claim Reza's approval, acceptance of the
complete U0001/U0002 proposals, or closure of G1/U1.

**Related:** [U0000](U0000-record-architecture-decisions.md),
[build spec §2.5.1](../build-spec.md#251-standalone-preparation-and-externally-supplied-inputs),
[execution plan](../execution-plan.md). U0001 records integration ownership; U0003 will
specify the concrete preparation contract. U0019 is the first unassigned number after the
plan's reserved U0001–U0018; those assignments are preserved.

## Context

rk-uarch simulates performance inside one chip and emits characterization tables for
rk-sim. The original plan intentionally let it run independently: ModelSpec, ModelShape,
precision, tensor parallelism (tp), queries, hardware and a selected mapping policy feed
local workload/mapping producers. An EngineJob carries the resulting work to an engine.
The engine already had a TaskGraph input boundary; mapping was not universally meant to
be invented inside simulation. The fork was an explicit exception, tiling internally.

The missing capability was a supported, versioned way to supply, save and replay prepared
operator shapes and mappings through that boundary. The high-level path alone would
reconstruct work using local assumptions, even when a future compiler or execution-plan
producer already knew the intended rank shapes and placement. A shared policy name does
not establish that a measurement, fork and native engine execute the same mapping.

The initial discussion overstated this as a need to separate all mapping from engines.
The amendment preserves the existing separation and standalone frontend, exposes file
inputs, and makes the fork exception and input identity explicit. A future external
producer must not become a prerequisite for developing or testing the simulator.

## Decision

1. **Keep two entry paths.** Standalone local preparation remains supported. A second path
   accepts validated prepared files and bypasses the corresponding local producers. Both
   reach the same engine boundary. Reuse OpSpec and TaskGraph rather than introduce a
   generic workload IR or an ONNX import language.
2. **Make partitioning ownership explicit.** An external execution plan supplies its
   authoritative rank-local shapes and declared scope. The local frontend may produce
   the explicitly supported split when selected. Engines do not silently re-shard inputs,
   divide counts by tp again, or infer a replacement fusion policy. Initial support remains
   balanced TP/representative-rank scope; unsupported scope is refused.
3. **Treat resolved mapping as input.** The selected producer supplies placement, tiles,
   transfers, dependencies and scheduling policies. Simulation determines actual timing,
   resource contention and stalls under those policies. Operator-only imports may explicitly
   select a local mapper; that is preparation, not replay of an externally supplied mapping.
4. **Declare engine limitations.** U2 analytic inputs carry resolved operators and an
   explicit analytic scope, without fabricated detailed placement. The fork may delegate
   mapping to its pinned internal implementation, with that fact in provenance. It must
   refuse exact imported mappings it cannot honor. Mapping equivalence requires evidence
   of resolved correspondence, not just equal policy names.
5. **Give prepared inputs content identity.** Versioned payloads declare producer, scope,
   hardware binding, query/state coverage and replay conditions. Their content hashes and
   relevant versions participate in request/cache identity and remain traceable from results
   and tables. Paths alone are not identity. Validate versions, hashes, dimensions, dependency
   references and compatibility before execution; refuse missing coverage instead of
   invoking hidden preparation. Same bundle and engine/run conditions reproduce the same
   deterministic result/table bytes.
6. **Settle schemas before implementation.** U0003 specifies exact fields, canonicalization,
   fixtures, validation, and any public contract-version change before U2 lanes diverge.
   U1 records ownership without speculative future payload fields. Later upstream exporters
   need their own integration decision; rk-sim continues consuming table files at runtime.

## Alternatives and tradeoffs

| Alternative | Benefit | Reason for the decision |
|---|---|---|
| Keep only model-based local preparation | Smallest immediate implementation and schema surface | Cannot directly replay authoritative external work or isolate producer changes from engine changes |
| Require external compiler/rk-sim preparation for every run | A single external authority supplies all shapes/mapping | Blocks independent development, synthetic tests and design exploration before that producer exists |
| Let each engine rebuild shapes and mapping | Adapters can use convenient native frontends | Creates duplicate assumptions and makes matched-work comparisons difficult to substantiate; retain only explicit, bounded fork delegation |
| Add a general compiler/workload IR and import ecosystem now | Broad future integration flexibility | Exceeds the current scope and duplicates the existing operator/task vocabulary |
| Preserve local preparation and expose prepared files (chosen) | Standalone operation plus reproducible external-input execution | Adds schema/version ownership, validation, fixtures, provenance and adapter work |

Local policies remain useful modeling assumptions; preserving them does not prove a real
compiler chooses the same mapping. Imported data is authoritative only within validated,
supported scope. This decision improves reproducibility and attribution, not fidelity or
accuracy by itself. Existing evidence and badge rules still apply.

Prepared bundles can be larger than model descriptions, especially across grids and error
experiments. Compatibility checks may reject inputs that a permissive adapter could
approximate. Supporting multiple input scopes increases maintenance and requires explicit
version transitions. These are accepted costs of making the simulated work inspectable.

## Delivery and affected prompts

| Stage / prompts | Change and rationale |
|---|---|
| U1 / U-P1 | Record ownership in proposed U0001; do not expand U1 into implementing replay |
| U2 / U-P3, U-P4 | U0003 schema prerequisite; standalone preparation, operator bundle export/import and analytic replay; report preparation provenance |
| U3 / U-P5, U-P6 | Preserve prepared shapes at the fork boundary; declare delegation/refusals; test producers and engine execution separately |
| U4 / U-P7, U-P8 | Serialize mapped TaskGraphs, validate coverage and hardware bindings, replay with policies disabled; compare corresponding resolved work |
| U5 / U-P9 | Freeze prepared input identity with predictions so later producer changes cannot change the prediction workload |
| U6 / U-P11a, U-P11b, U-P12 | Reuse versioned schemas in Rust, consume supplied graphs, and verify mapping correspondence in differential tests |
| U7 / U-P13d, U-P14 | Policies emit the same file format; studies explicitly choose local re-preparation or fixed imported mappings |
| U8 / U-P15 | Apply the same input freeze and mapping-evidence discipline to the mesh reference |
| U9 / U-P17, U-P18 | Vary simulator parallelism/synchronization while keeping workload and mapping fixed |
| U10 / U-P19, U-P20 | Preserve preparation provenance in table consumption/reporting; keep runtime integration file-based |
| U11 / U-P21 | Demonstrate cold standalone operation and saved-input replay without compiler services |

The breadth of edits follows the lifetime of the same input: creation, execution,
comparison, prediction freeze, study variation and consumption. It is not authorization
for each worker to redesign the preparation schema. Build-spec §8 mirrors the standalone
prompts; the two shipped rk-sim-side prompts mirror U-P19/U-P20. Module READMEs and
CLAUDE.md explain the same boundary.

Existing effort figures are historical baselines. Re-estimate affected work when U0003
settles the schema, particularly U2 and U4, and propagate changes into the overall schedule.
The amendment does not establish a new delivery-date commitment.

## Verification and remaining work

The planning amendment passes the current four repository tests, including prompt-text
synchronization, and whitespace checks. Those checks validate documentation consistency;
they are not evidence that preparation/replay has been implemented.

Implementation exits require local export/replay with producers disabled, independently
specified supported input fixtures, stable identities when files move, cache invalidation
when content changes, and refusals for stale hashes, incompatible hardware, unsupported
scope and incomplete coverage. Detailed replay and adapter correspondence follow in the
sprints above. U0003 records concrete acceptance fixtures before implementation.

U1 workers must incorporate the ownership reference during integration without losing
their pending contract revisions. Their worktrees, vendor snapshots and rk-sim pin are
not changed by this record. U0001/U0002 acceptance, independent review and G1 remain open.

## What this decision does not do

It does not implement a compiler, mapping search, new parallelism modes, an upstream
exporter, or simulator code. It does not require live rk-sim or a compiler. It does not
change the one-chip result scope, channel mapping, numerical parity criteria, fidelity
rules or evidence thresholds. It does not accept concrete schema fields in advance or
supersede U0001/U0002 as a whole. Replacing this direction requires a subsequent ADR.

## U0003 accepted rank-scope addendum

Accepted by Javid under U2-U0003-acceptance-v1; see
[the exact acceptance record](../reviews/U2-U0003-acceptance-record.md).

Extend balanced TP imports only to selected ranks with unequal embedding hits explicitly
supplied as a conserved integer vector: length tp, sum M. All other shard extents remain
balanced. Representative ranks require equal physical work. tp2/M1 [1,0] is valid selected
work; [1,1] cannot establish rank equivalence. High-level no-token inputs require explicit
synthetic balanced assignment (floor(M/tp), remainder in rank order). Imports remain
immutable, never re-sharded; heterogeneous non-embedding splits/PP/EP/CP remain unsupported.
