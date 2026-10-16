# U4 Lane A — complete the component mapper and prepare the model-stage join

Start a fresh implementation session in /home/jjaff/AI-infra-simulation/rk-uarch-u4-a.
This is the next substantial A-owned work package, not a request for another architecture
proposal. Verify a clean/index-safe main, fetch and integrate published peer history normally.
Read CLAUDE.md, execution-plan U4 and its serial/parallel dependencies, U0011/U0019/U0022/
U0023/U0024, U-P7 PHASE M and U-P11b phase B. Read this directory's README.md. The accepted
scope and installed carriers govern; historical proposal wording does not override them.

Inspect current code first. The installed workload/mapped.py exposes fixed-delay loader/
export functions; it is not the component mapper. Reuse installed mapped.py carriers,
validate_resources/admit/validate_job and exact installed versions. Read the final M package,
U4-A-loader-K2-preparation-v1, U4-A-K2-construction-v1, accepted U3 stage design interface/
verification/delivery, and B's published verification-inputs/final-reconciliation packages.
Follow the current task scope over the old template's uncommitted-work workflow: publish
owned work to main with normal hooks, preserve peer commits, no force push or CI polling.

START NOW — COMPLETE M COMPONENT INPUTS

1. Implement a deterministic versioned component mapper in A-owned mapping/workload code.
   Consume existing PreparedOp/OpSpec and HardwareSpec carriers, not a new operator language.
   Scope is exactly U0011's admitted npu-l4, ratio1, BF16 inputs/output, FP32 accumulator,
   TP1/rank0, 1–16 q_projection GEMMs, 1<=M<=1024, 1<=K,N<=256, contiguous WS tiles and no
   K split/spill. Preserve cold production versus explicit verification-only resident inputs.
   Production eligibility at the schema layer is not permission to launch the native binary.
2. Emit explicit complete TaskGraphs: canonical IDs/ordering, exact tile coverage, SRAM/HBM/
   accumulator placements, nonaliasing double-buffer slots, bank coordinates, DMA request
   splitting/striping/routes, barriers and dependencies. Follow accepted E3/E4 and owner
   enumeration laws. All work/traffic is represented once. Do not encode a duration computed
   in Python as a substitute for a future native component model. No policy search, hidden
   sharding, retiling, padding policy change, unsupported operator or future full-model path.
3. Complete component saved-bundle/job import/export using exact installed admission and
   independently supplied trust anchors, separate from preparation. Preserve fixed-delay APIs.
   Canonical export refuses overwrite and stale joins. Imported valid mappings replay as
   inputs with mapping/workload/coefficient producers disabled; do not regenerate or silently
   rehash imported work. Public native result replay remains pending until stage B execution.
4. Write meaningful tests first: independent small placement/count/transfer literals, tile
   tails and split rows, capacities/alignment/banks, resource joins, stale/rehashed mappings,
   duplicate/missing coverage, cycles, wrong precision/hardware/rank/state and producer-disabled
   relocation. Verify changed valid placement changes identity. Include expected failure
   reasons and controls that reach the intended guard rather than fail setup. Synthetic unit
   anchors are labelled and never become actual human host/profile authority.
5. Publish an early small API/interface note when B needs it, then finish independently.
   Preserve B's distinct resident/cold and D02/D14 fixtures; do not force A and B placements
   to be identical merely because useful work agrees. Peer findings get a discriminating
   test and correction; no coordinator stop for ordinary owned-code joins.

PREPARE THE NEXT NATIVE STAGE WITHOUT STARTING IT EARLY

6. Produce an implementation-ready U-P11b B checklist against the actual mapper and current
   Rust K2 modules: compute WS staging/overhead/fill/drain, exact edge arithmetic, NoC0 hops,
   refresh-derated rational DRAM service, DMA credit-until-commit/ack, core ports, barriers,
   legal overlap, completion-derived counts, finite-window queues/resources and causal
   attribution. Explicitly cover E4 phase/clock crossings, fifth-read refresh discriminator,
   zero-hop behavior and zero-duration ownership. Map each to B's frozen case/control.
   Prepare tests/fixtures or an unapplied test patch where absent implementation cannot yet
   pass; never commit failing default tests or permanent unconditional skips as completion.
7. Enumerate genuine carrier/observation gaps using exact before/after schema/ADR proposals
   where necessary. Do not silently broaden protected contracts. Full generic prompt cases
   outside admitted B (spill, steady, full decoder, FP8, NoC contention) stay explicitly deferred
   to R/U6/T rather than overriding U0011's narrower stage.
8. Audit import/data edges and selected generator support. No new package, initializer
   shortcut, stale artifact waiver, fixed support-file quota or protected install. If an
   actual selected-support change needs a lifecycle, prepare the minimal exact delta and
   keep the published installed source/artifact pair valid. Provide new build/runtime identity
   requirements prospectively; never copy K2 identity or authority onto component results.

DEPENDENCY BOUNDARY

The coordinator is reviewing/placing the optimized K2 runtime and running its pinned campaign
separately. Do not edit its roots/receipts, run public native jobs, or rebuild its binaries.
Native component implementation, component builds/execution and real profile/host binding
wait for a published coordinator K2 reconciliation plus exact component-stage release and
required input/semantic decisions. A future campaign pass is not assumed. Finish all mapper,
loader, tests and preparation work while that dependency is pending; don't poll/wait or stop
at an initial plan. If the release arrives during work, read its precise scope and continue
only what it actually authorizes. Otherwise return the complete M/code handoff and ready B
implementation checklist; no new design cycle is needed merely because execution waits.

VERIFICATION / DELIVERY

Run affected unit/integration tests, installed schema freshness, both current CI-form mypy
commands with PYTHONPATH/MYPYPATH unset, lint/import contracts and strict vendor currentness.
Run necessary integrated regressions once at final source freeze; coordinate heavy runs with
the campaign so they do not exhaust its CPU/memory. No full 798-call campaign for unrelated
Python mapping changes. Record source origins, counts/skips and actual versus inherited evidence.

Return one published handoff with implemented APIs/versions, exact admitted/refused scope,
independent evidence, B joins, dependency audit, unapplied protected changes if any, and the
next executable native-model work. Preserve STUB/unknown error/unverified energy, component
u_c0_duration_ps=null unless separately admitted, and at-most-C1 scope. No full tables, silicon
execution, new external tools, remote qualification or sprint closure. No subagents unless
Javid separately requests them. Keep commits small enough to review, not copied checkpoint trees.
