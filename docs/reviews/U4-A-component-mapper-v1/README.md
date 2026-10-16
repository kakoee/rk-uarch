# U4 A component mapper and B preparation handoff

Published implementation: **55681a88e163828d2c90e60a7fcece77cca54e49**, with import-refusal
corrections **cf7261c / 3f54861** integrated with B at **a8b3eeb**; early API note:
b1e9f3e. Started clean/index-safe in the requested Lane A checkout, fetched and fast-forwarded
d9a22f0→490d90b, then published ordinary main commits with normal hooks. Peer history and
all protected/native/campaign paths are preserved. No subagents, force push, CI polling,
new package, initializer edit, binary build, native job or human host binding.

Implemented APIs and exact versions are in [interface.md](interface.md): deterministic
`map_component`, point/bundle/job assembly, and canonical saved component bundle/job
loads/load/export functions with independently supplied registry/profile/engine trust
anchors. Fixed-delay APIs remain intact. Mapping uses existing PreparedOp/OpSpec and
HardwareSpec with installed TaskGraph/MappedBundle/MappedEngineJob carriers, resource
validation and B admission. No Python duration, remapping, coefficient/model producer or
hidden sharding occurs on replay. Export refuses stale identity/joins and overwrite.

Scope: exact npu-l4 hash, ratio1, BF16 X/W/Y, FP32 accumulator, TP1/rank0,1–16 q_projection
GEMMs, M1–1024/K,N1–256, contiguous WS256-row chunks, no K split/spill. Exact HBM/SRAM/
accumulator placements, bank coordinates, nonaliasing second-slot reservations, explicit
striped DMA/routes, canonical owner/barrier dependencies and complete coverage are emitted.
Cold production eligibility and explicit resident verification inputs remain separate;
production eligibility is not native launch authority. Unsupported operators, hardware,
precision/rank/state/padding/full models and capacity failures refuse.

**Known installed-carrier limit:** different accumulator footprints reserve disjoint scratch;
some heterogeneous1–16-op collections exceed capacity despite legal sequential reuse being
possible physically. The installed validator cannot express their transient accumulator
final consumers. Identical footprints share persistent scratch under the exclusive matrix
owner; sixteen maximum-size GEMMs pass. This handoff does not claim universal admission of
all heterogeneous collections. [protected-gaps.md](protected-gaps.md) gives the exact
unapplied lifetime patch, controls and prospective policy/ADR decision. No retile/spill or
protected-contract relaxation hides this limit.

The owned replay consumer closes three independently reproduced admission holes: truncated
operand production, omitted cold output write and wrong barrier owner. The tests first
showed DID NOT RAISE for each; corrected tests now pass. Installed protected source remains
unchanged, and Rust B must enforce these same completeness laws before execution. A fourth
control found missing operand-access keys leaking KeyError from installed validation;
cf7261c and3f54861 refuse them explicitly in bundle and full-job paths before resource
validation. access-red.log/job-access-red.log retain failures; job-access-restored.log
records178 passing restored controls.

[Native B checklist](native-B-checklist.md) maps actual Rust module seams and every required
compute/NoC0/DRAM0/DMA/port/barrier/phase/observation/causal task to B C/D/Q controls, including
fifth-read refresh, rational carry, unequal clocks, corrected D02/D14 and owned zero service.
Unapplied test modules are syntax-checked preparation, not executed native evidence or skipped
default tests. The separate queue-clock proposal is also unapplied. B's published fixtures
remain unchanged and pass installed structural admission under their **synthetic proposal**
anchors; B's six arithmetic worksheets pass. These are neither human L1 working nor native
execution. A's four new input fixtures intentionally retain distinct placements/identities.

[Dependency audit](dependency-and-identity.md) records source origins/import/data edges and
prospective new build/runtime identity requirements. The current selected generator inventory
has56 files, with zero deltas from490d90b; strict vendor currentness passes. No artifact
lifecycle transition or stale acceptance is needed for current owned code. Any future
protected change requires the measured minimal delta and normal human lifecycle.

Verification:58 mapper tests pass, including literal small placements/counts, tails/split
rows, unaligned imported stripes, exact boundaries, bank/alias/resource/owner joins,
missing/duplicate coverage/cycles, wrong scope/state/precision/rank/hardware, stale and
rehashed attacks, changed valid placement identity, independent anchors and three isolated
producer-disabled relocated imports. A fresh clone of the final published source passes178 mapper/fixed-delay/
installed-admission tests with exact module origins checked. Both CI-form mypy commands ran
with PYTHONPATH/MYPYPATH unset (88 source files and33 contract-test files); lint, both import
contracts, all three installed schema checks and strict vendor currentness pass.

Final targeted integration passes **249 tests, zero skips**; exact commands/counts are in
verification.json/integrated.log;
source freeze is **a8b3eeb** (3f54861 complete access guard plus published B history).
The prior broad selection passed **1240 tests, zero skips** at c39c999; its receipt and logs
are retained separately under broad/. The last job-import precondition is covered by the
final focused/replay integration and fresh-clone runs, not credited retroactively to that
broad run. Checks run sequentially on one low-priority CPU and contain no native calls.
Intermediate counts30/169/176/177 and the first1239-pass broad run are not added to final
counts. Retained development logs disclose missing-module tests-first failure, a failed
shell editing command causing missing imports, and the corrected stale-hash reason assertion
(`ArtifactHashMismatch`). An initial rotary command named nonexistent generate_v2; the actual
generate_rotary_v2 passes. A driver-edit failure caused a repeated broad selection; final
and retained broad receipts identify their actual commands/source, with no invented history.

This is author implementation/preparation evidence with independent literal controls and
inherited accepted design/peer inputs; independent review remains required. Local interim
verification under U0024 is not remote qualification. B's new combined-runtime package2664c97 and evidence918ab50 were fetched, read and integrated normally; it
explicitly remains proposal-only and releases no native component work. The coordinator's pinned K2 campaign,
precise component release and required semantic/input decisions gate component implementation,
builds/execution and genuine profile/host binding. No future campaign pass is assumed. The
next executable native work is the checklist after that release; absent it, this package is
the ready M/code handoff. STUB, unknown error, unverified energy, component
u_c0_duration_ps=null and at-most-C1 scope remain. No reference/silicon run, full table,
remote qualification, performance claim or sprint closure.
