# Component input API join (early publication)

Base: published `490d90b`. Installed carriers govern: prepared-op/1, uarch-taskgraph/1,
uarch-prepared/3, uarch-engine/3, U0011-stage2/1, E4-named-edges-rational-service/2.
This is the A-owned M input implementation; native component execution remains gated.

- `rkuarch.mapping.component.map_component(ops, hardware_spec, *, initial_state="cold")`
  returns installed `TaskGraph`. Inputs are existing PreparedOp/OpSpec and HardwareSpec.
  Policy is ws-rowsplit@1, buffer depth 2. Only the exact npu-l4 hardware hash is generated.
- `rkuarch.workload.component.component_point(ops, graph, *, initial_state="cold")` returns
  the ratio1/priming0 point. Freeze this before preparing a test profile: no hash cycle.
- `prepare_component_bundle(ops, hardware_spec, point, *, producer, assumptions, rank,
  admission)` assembles supplied content and applies installed `validate_resources`.
  Producer implementation hash is an explicit source-provenance input, never host authority.
- `prepare_component_job(bundle, *, point_hash, registry, profile, invocation,
  trusted_registry_hash, trusted_profile_hash, expected_engine)` constructs an input job
  with complete canonical owners and installed numeric hardware projection. No launch.
- `rkuarch.workload.mapped`: `loads_`, `load_`, `export_component_bundle` take explicit
  invocation, registry/profile and independent trust hashes. `loads_`, `load_`,
  `export_component_job` take invocation, trust hashes and expected engine. Export is
  canonical and exclusive; loading calls installed B admission without any producer.
  Fixed-delay APIs retain their signatures and K2-only scope.

Call sequence: map → point → independently frozen profile if verification → assemble
bundle → admit/export → construct/admit/export job. There is no implicit profile creation,
resolver, native process, coefficient producer or analytic duration. Examples/tests use
synthetic unit anchors; they cannot become accepted human profiles or deployment roots.

Placement: canonical sorted op IDs indexed o000..o015; 256-row chunks use cores0..3,
full K/N with physical K=N=256. Each tile reserves separately aligned X/W/Y and a second
slot of equal padded allocation size. Only slot0 is populated. Slots of independent ops
are disjoint; no hidden overlap or pipeline duration is promised. Cold HBM operands are
separate tile allocations, including W copies. DMA fragments split at 256-byte stripes,
channel=(address//256)%8, XY NoC0 route to controller channel//2. X/W DMA use local engines
0/1; output uses0. Resident maps have no HBM or DMA. Operator dependencies join all terminal
tile jobs through an explicit canonical-owner barrier. Independent ops remain independent.

Accumulator scratch for identical (core, footprint) is a single allocation used under the
exclusive matrix owner; distinct footprints reserve disjoint storage. Installed admission
omits accumulator readers from final-consumer derivation, so it cannot represent ordinary
lifetime reuse of differently sized allocations. If their sum exceeds capacity, the mapper
refuses `CapacityExceeded`, naming the resource/bytes. No retile/spill or protected change.
A discriminating reproduction and exact unapplied proposal follow in the final package.

B's C01/C02 resident, C05 cold, D02 write and corrected D14 producer-dependent zero-hop
fixtures retain their own placements, hashes and expected timings. A's small cold placement
starts HBM X/W/Y at0/256/512, unlike B's1536/3584/5632; useful work agrees, cold timing need
not. Compare resolved work and transfer placement explicitly. Do not transplant B's whole
cold-job answers to A's mapping or K2 implementation/build authority to component results.

Implementation is published at `55681a88e163828d2c90e60a7fcece77cca54e49`; final import-access
refusal corrections `cf7261c` and `3f54861` are integrated with B at `a8b3eeb`.
The loader also applies three conservative completeness guards after installed admission:
full operand production, complete cold-output writes and canonical barrier owners.
A structural access-key precondition also protects bundle/assembly/full-job paths from
an installed-helper KeyError before resource validation. See
[exact gap/control evidence](protected-gaps.md). These guards reject incomplete mappings;
they do not regenerate input or authorize a broader schema. Four new author input fixtures
and their synthetic profiles are under fixtures/; no native result accompanies them.
