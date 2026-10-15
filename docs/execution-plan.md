# rk-uarch — Execution Plan

**The working document:** twelve sprints (U0–U11), two lanes, with G3 split into readiness and table gates. For each sprint it
says what to build, who builds it, which prompt to run, and the one thing you must be able to
run at the end.

**Rev 2, 2026-09-28.** Adds the book-coverage gaps (F1–F17; see build-spec Rev 2). The gates
below carry the new checks, and §7's effort is re-derived from the amended prompts.
**Rev 2.1, 2026-10-01.** Applies `docs/reviews/rev2-plan-review.md`: G3 and G5 read the fork's
levels from ADR U0005, G4 and G7 gain class lists and defined fail-branch metrics, U6 and U7
run split prompts (U-P11a–c, U-P13a–d), U9 is gated on a measured need, and §7.4's calendar
takes the longer lane per sprint.
**Rev 2.2, 2026-10-01.** The native engine is Rust (build-spec Rev 2.2). Sprint content and
effort are unchanged; the seam with rk-sim is unchanged.
**Rev 2.3, 2026-10-01.** Two native-engine time decisions (build-spec Rev 2.3), recorded in
the spec rather than an ADR: resolved integer clock frequencies with rounded edges, and how
Ramulator 2 ticks inside the event kernel. U-P11a and U-P13b gain acceptance tests; sprint
content, gates and effort are unchanged.

**Canonical for:** *what order and who*. For *what* and *how* (architecture, contract, repo
layout, conventions and the prompt texts) see `docs/build-spec.md`.

**Sprints here are defined by content, not by the calendar.** A sprint ends when its joint
exit criterion runs, its U-REVIEW loops are ACCEPTED, and a human tags it. §7 gives the
effort each sprint's prompts imply, in hours, derived from the prompts.

---

**Rev 3 direction, 2026-10-12.** Effective with human-committed U0005: one progressive
production simulator; no mandatory full fork or second substantial Python contention engine.
U3 designs the bounded native stage, U4 builds it and prepares the reference benchmark
scope, U6 qualifies expanded capability, U7 produces the first full product tables.
**Rev 3.1, U0023:** G3a is silicon readiness; G3b is consumed-table readiness. G4/G7
success is not a table-production prerequisite. Correctness, performance and automation
have distinct host requirements. The older notes and §7 estimates are historical.

**Temporary U0024 exception:** local native checks plus independent review can support
interim stage/sprint development during a multi-sprint remote-CI delay. Record remote
qualification as pending and carry its debt at every handoff. This prospectively overrides
only the identified hosted-native entry/checkout requirements below; task authorization,
contracts and other tests still apply. Full G5, U9 entry, performance claims and final
project closure retain their required evidence. See [the ADR and Reza/owner runbook](decisions/U0024-temporary-local-verification-and-deferred-native-ci.md).

## STATUS

| | |
|---|---|
| **U0 done** | Tagged `u00-end` at `a5a4cc4`: bootstrap, protected files, build-spec Rev 2, pushed to the private remote |
| **Accepted** | 2026-10-03: both founders accept the Rev 2.1 fixes from `docs/reviews/rev2-plan-review.md` (and Revs 2.2–2.3) |
| **rk-sim pin** | `1e5706e0ebfcc67c1a7333079a35b75f693e9963` (rk-sim `main`, verified 2026-10-04), fixed for U1 so U-P1 and U-P2 use the same baseline; U-P1 records it in ADR U0001 |
| **Next** | Local K1 review/corrections and the separate approved M/policy installation preparation. Remote native CI and infrastructure deferred under U0024; no automatic K2 implementation release |
| **U1 done** | Published `u01-end` at `1e9e794a84c5173812c23a1cf2fc04b85e6f6831` |
| **U2 done** | Accepted closeout and `u02-end` at `79bc1f0`; approved cleanup preserved the evidence archive and branch history |
| **U3 done** | Human `u03-end` at `6d39a234a14855c86ca54b795501a0b0b2618d7b`, published and verified; final CI passed. [Closeout](reviews/U3-closeout.md). Historical incomplete report outcomes remain explicit |
| **U4 started** | K1 implementation and local A/B checks published; exact M/tool choices accepted. Remote qualification remains pending; M protected installation/artifact lifecycle and G3a remain incomplete |
| **Not started** | U5–U11 |
| **Runner pending** | Registration and executed manual nightly remain unverified. Not a correctness-development prerequisite under U0023; controlled-host performance and G5 nightly qualification remain pending |

Update this block and `docs/how-it-works.md` at every sprint boundary.

Current U1 acceptance and artifact identities are recorded in
[U1 acceptance and adoption](reviews/U1-acceptance-and-adoption.md). Earlier proposal
and partial-approval notes below remain historical; they do not override that acceptance.
See the [U1 closeout](reviews/U1-closeout.md) for publication and durable validation evidence.
[U0020](decisions/U0020-u1-cold-clone-validation-exception.md) records Javid's already-approved
U1-only substitution of fresh ElfinKidsLaptop Ubuntu/WSL2 validation plus same-commit hosted
Ubuntu CI for the separate Linux-box check. Later runner/hardware/performance-host requirements
are unchanged. Javid approved G1 and accepted the complete closeout, including U0020, on
2026-10-07. The approval is recorded in the closeout. Read-only remote verification on 2026-10-07
confirmed the published closeout and annotated tag, plus successful
[closeout CI](https://github.com/kakoee/rk-uarch/actions/runs/37588171798) on the exact tagged
commit. Historical pending wording in U1 evidence is retained as history. See the
[U2 kickoff record](reviews/U2-publication-history.md#kickoff) for verified identities, isolated
worktrees, ownership, carry-forward obligations and bounded worker prompts.
[U0021](decisions/U0021-u2-cold-clone-validation-exception.md) records Javid's newly approved
U2-only WSL2 fresh GitHub clone plus same-published-commit hosted Ubuntu CI exception.
U0020 is unchanged; later Linux-host, runner and hardware requirements are not waived.

**U2 publication workflow:** keep the A, B and integration worktrees isolated and their
development branches local. Main remains the publication branch; no development-branch
push or mandatory PR workflow without discussion with Javid. Prepare reviewed local
checkpoints, keeping commit and push separate; uncommitted files are not protected by branch
history. Integrate the tested, approved result onto main and tag the approved main revision
at closure. Preserve worker worktrees until publication is verified. The
[kickoff sequence](reviews/U2-publication-history.md#kickoff)
explains each transfer and validation step.

Current [U2 closeout evidence](reviews/U2-closeout.md) supersedes earlier pending-status
notes below without rewriting them. U2 is not G2: under U0005, G2 is U3's native-stage design/readiness decision.

**U3/U4 Git workflow, requested by Javid:** A and B use separate working folders against
main, each committing and pushing to main, synchronizing and resolving conflicts as needed.
Before pushing, fetch the current remote main and integrate it; use ordinary fast-forward
pushes and rebase only unpublished local commits. Never force-push shared main or rewrite
published commits. Integrate on demand with Git diffs and commit IDs; do not copy checkpoint
trees or create another manual revision-control process. Generated-artifact provenance and
reproducibility manifests retain their narrow purpose. This records the requested workflow;
host obligations now follow U0023; it does not waive performance or nightly qualification. Actual hours and
retro remain unreported until Javid supplies them.

**U1 pin update, 2026-10-04:** Javid (@jjaffari) approved advancing from `11bb530` to
`1e5706e` before implementation. The seven intervening commits leave `rk/schema/`,
`rk/provenance.py`, `rk/engine/f0/`, the component library, generated schema and types,
dependency files, generation scripts, and U-P1's required reference ADRs unchanged.
P16 adds S6 compatibility guidance without changing its operator baseline. The comparison
checked source identity; it was not a new rk-sim test-suite run. Keep this exact pin throughout
U1; both U0001 and the vendored snapshot must record the full SHA above.

---

**Preparation-boundary amendment, 2026-10-06:**
[ADR U0019](decisions/U0019-standalone-preparation-and-prepared-input-replay.md) records the
rationale, alternatives, consequences and affected prompts. Javid approved preserving the standalone
frontend while exposing validated prepared-input import/replay (build-spec §2.5.1). This
approves the architecture direction, not U0001/U0002 in full or G1. U1 records ownership;
U2 first settles U0003's concrete schema/identity revision, then implements local preparation
and analytic replay; U4 adds mapped TaskGraph replay. Fork/native adapters, comparisons,
prediction freezes and studies consume that boundary. No compiler or live rk-sim dependency
is added, and no implementation work is claimed by this planning amendment. Existing effort
figures remain historical baselines; re-estimate affected work at U0003 and update the
overall schedule, particularly for U2/U4, before treating those figures as commitments.

## §1 · THE SPRINT LOOP

| # | Step | Who |
|---|---|---|
| 1 | Open the sprint below. Read your lane's row and the joint exit criterion | both |
| 2 | Run your lane's prompt in a **fresh session** with `TEMPLATE-implementation-session.md`. One prompt, one session | each |
| 3 | Answer the agent when it stops. A prompt that says *stop* or *ask* means stopping is correct | each |
| 4 | **Integrate.** Publish the approved main revision, then run applicable correctness exits from a fresh hosted Linux checkout and a separate fresh local clone on that same commit; add controlled-host checks where required by U0023 | both |
| 5 | Run **U-REVIEW** on the *other* lane's work, in a fresh session. All three stages | each, crossed |
| 6 | Run `STANDING-how-it-works-refresh.md` in a fresh session. Tag `uNN-end`, log actual hours, then a 15-minute retro: *what did the agents get wrong?* | both |

**The standing rule:** preserve the working analytic table path on main. This does not
require every native checkpoint to emit a table. A sprint whose required lane work did not
integrate did not finish. Missing silicon resources keep that campaign open; they do not
block independent native work or honestly labeled table production.

---

## §2 · LANES

| | **Lane A: Engine** (Ray, @kakoee) | **Lane B: Evidence & Product** (Javid, @jjaffari) |
|---|---|---|
| Owns | `src/rkuarch/{hw,workload,mapping,engines,table}`, `native/`, `third_party/`, `containers/`, `cli.py` | `hw/`, `src/rkuarch/{provenance,report,study}`, `validation/`, `measure/`, `scripts/`, `.github/workflows/` |
| The question it answers | *What does this chip do?* | *Why should anyone believe it, and what would they do with it?* |
| The risk it owns | wrong physics | wrong meaning: evidence scope, provenance leaks, anchor semantics |
| Both approve | `contract/`, `tests/golden/expected/`, `CLAUDE.md`, `docs/decisions/` | same |

**Genuinely parallel pairs.** Neither prompt in a pair consumes the other's output:

| Pair | Why it works |
|---|---|
| U-P1 ∥ U-P2 | One writes schemas; the other vendors rk-sim's and generates fixtures by running rk-sim |
| U-P3 ∥ U-P4 | After U0003's prepared-input/public-schema prerequisite is accepted, provenance uses the fixed table shape and a toy table; it need not wait for the producer/engine implementation |
| U-P5 ∥ U-P6 | Native-stage design and analytic verification can proceed independently |
| U-P7 M ∥ U-P11a K1 ∥ U-P8 | Accepted semantics allow internal kernel mechanics and independent expectations while public mapped carriers are prepared |
| U-P11a/b ∥ U-P12 foundations | Accepted mapped protocol enables independent tests alongside the kernel; executions wait for it |
| U-P13a–c ∥ U-P14 preparation | Study schemas/suites can be prepared independently; execution waits for the admitted engine, point/table adapter and declared inputs |
| U-P17 ∥ U-P18 | Pre-registration and the harness can land before the parallel engine does |

**Serial inside a sprint.** Named so nobody schedules them together:

| Order | Why |
|---|---|
| U-P9 → U-P10 (measurement step) | Predictions must be committed before any measurement exists. Lane B writes and dry-runs its kit in parallel, and measures only after the freeze |
| U-P16 S → U-P15a → U-P15 → U-P16 M | B reference/readiness, A native admission, separate freeze, then measurement; no implementation in the freeze session |
| Boundary schema PR → U-P19 → U-P20 | Both run in rk-sim and touch provenance. The schema PR comes first, then P18, then P19 |
| U-P5 → (U-P7 M and U-P11a K1) → K2 → U-P11b B | Internal kernel work may overlap mapping; public wiring waits for approved carriers; models wait for the verified boundary |
| B → U-P11b R / reference readiness → G3a → U-P9 freeze → U-P10 measurement | U4b covers the actual U5 suite, not a full unrelated grid |
| Verified B → U-P11c / U-P12 completion → G5 | U6 qualifies the expanded scope without requiring G4 success or TPU availability |
| G5-correctness → U7 depth/G6 plus U-P7 T/G3b → U10 | Full G5 performance/automation remain separately open without blocking these correctness/product milestones |
| U-P13a, U-P13b, U-P13c → U-P13d | The three subsystems in any order, then the composite rule that needs all three |

**Lane allocation after the amendment.** U4 now carries native core work previously in U6.
Re-estimate the critical path and ownership in U-P5 before scheduling; §7 is historical.
Internal mechanics and independent derivations may overlap M; public protocol wiring waits for its accepted boundary.

---

## §3 · THE SPRINTS

### U0 · Bootstrap

| | |
|---|---|
| **Goal** | The repository exists, and explains itself before any code does |
| **Either lane** | `BOOTSTRAP-PROMPT.md` (= **U-P0**) |
| **Joint exit criterion** | `uv sync --extra dev` and `make test` pass on a cold clone · every CI job exists · import-linter forbids `rkuarch → rk` · `tests/unit/test_prompt_sync.py` green |
| **Effort** | A 8 h realistic (§7) |
| **Not in this sprint** | Any logic |

### U1 · The contract

| | |
|---|---|
| **Goal** | The one thing everything else codes against exists, and it is proven identical to rk-sim's vocabulary |
| **Lane A** | Contract → **U-P1**, with Javid acting as human owner/approver for both U1 lanes |
| **Lane B** | Vendored rk-sim snapshot, FLOP-parity fixtures from rk-sim's own code, round-trip tests → **U-P2** |
| **Joint exit criterion** | **Gate G1** · the `contract` CI job green against the toy table · parity fixtures for ≥3 ModelSpecs × ≥24 queries · ADR U0001 accepted by Javid (@jjaffari), acting human approver for both U1 lanes, including the Rev-2 decisions (applicability bins, the BLOCKFP8 rule, shared SRAM, the initial-state default, the declared omissions) |
| **Effort** | A 31 · B 21 h realistic |
| **Depends on** | U0 · a local rk-sim clone at the pinned SHA in STATUS (`1e5706e`). U-P2 starts from that SHA without waiting for U0001; U-P1 writes the same SHA into U0001, and a different SHA there is a stop |
| **Not in this sprint** | Any engine; any field for a later sprint |

> U-P1 receives Javid's complete contract review under the recorded U1 delegation. Everything downstream codes against it.

### U2 · The first honest number

| | |
|---|---|
| **Goal** | A hashed table end to end, whose every number says what it may claim |
| **Lane A** | Accepted U0003 schema/identity; consume B-owned hardware specs, `derive_rk_params`, standalone versioned physical preparation with independent correctness/paged KV and test-only nominal compatibility, prepared bundle export/import, U-C0 over resolved operators, minimal table path and existing CLI → **U-P3** |
| **Lane B** | Four hardware specs and sourcing; badges (claims, stipulations, the model as contributor, the ceiling), model cards, applicability over the full scope vector, `uarch report` through `badged()` with diagnostics and a per-op roofline → **U-P4** |
| **Joint exit criterion** | `uarch table hw/designs/npu-l4.yaml … --engine analytic` → `uarch report` defaults to hidden STUB magnitudes (explicit labelled prediction opt-in), shows "conditional · N stipulations", "error: unknown", "not modelled" for null diagnostics, composite C0 · test-only nominal candidate = stored rk-sim duration within ±0.1% for every adopted fixture using its own params/model; unchanged nominal count budgets; independent physical shape/count/timing correctness and complete bound physical discrepancies; no physical full-workload duration validation claim · the graph is one rank of a tp-way split, with attention fused · `uarch characterize` runs on the demo request · local preparation exports a bundle whose analytic replay is byte-identical with the producer disabled; imported supported fixtures run without rk-sim/compiler; input mismatches and stale hashes fail |
| **Effort** | Accepted conditional range A 140–222 · B 100–154 · independent review 16–24 = 256–400 engineering hours; human waits separate (§7 remains historical) |
| **Depends on** | G1 and U0003 acceptance-v1 complete as prerequisites; implement the exact common baseline, with A2 runtime interfaces, reference readiness and artifact decisions still outstanding |
| **Not in this sprint** | Fork; native; interpolation; detailed tiling/mapping policies; compiler or rk-sim exporter |

### U3 · Native-stage design and verification readiness

| | |
|---|---|
| **Goal** | A useful bounded stage with executable tasks, independent checks and real consumers |
| **Lane A** | U-P5: component scope, M/K1/K2/B boundaries, toolchain/license proposal and exact schema decision package; with B, reference representability |
| **Lane B** | U-P6: record each analytic obligation's first consumer; independent native expectations; reference sourcing/measurement feasibility and a bounded test-only consumer-conformance proposal |
| **Joint exit** | G2 design accepted, outstanding implementation/evidence explicit; independent review and human closure remain required |
| **Prerequisites** | Accepted semantics and toolchain before K1; exact schema before K2. Unrelated analytic reporting and runner registration do not block internal kernel work |
| **Accepted boundary** | U0011 records the approved design scope; exact schema installation, toolchain/licence pins, numeric performance budgets and U4 authorization remain separate. No native accuracy or completed implementation claimed |

### U4 · Bounded native engine and silicon readiness

| | |
|---|---|
| **Lane A — U4a** | U-P7 M and U-P11a K1, then K2 and U-P11b B: single-threaded verified execution of the approved component slice |
| **Lane A — U4b** | U-P11b R: complete the actual U5 workload/reference admission, including required operators, RoPE/conversions, memory and initial-state behavior |
| **Lane B** | U-P8 and foundational U-P12: independent cases/faults, required analytic floor checks, attribution qualification; source the reference and establish measurable benchmark granularity with A |
| **Joint exit** | G3a: actual reference-suite readiness and verification; no full-grid table prerequisite |
| **Depends on** | G2; exact stage/schema/toolchain decisions; reference feasibility and admission before G3a |
| **Parallel progress** | If reference feasibility/access is unresolved, retain the open G3a/campaign gate and proceed only with independently ready U6 tasks; do not call U4/U5 closed |
| **Not in this sprint** | No C2 depth, threads, mandatory FP8/os-tiled/ragged grid or automatic silicon measurement authorization |
| **Effort** | Re-estimate M/K1/K2/B/R; old full-table T effort is not a current U4 forecast |

### U5 · Silicon I: the large-core class

| | |
|---|---|
| **Goal** | Find out whether the method tracks a real large-core chip, and say so either way |
| **Lane A** | Use the already admitted usable TPU v5e reference and signed suite; freeze predictions → **U-P9**. Engine/reference readiness is U4b work, not an implicit task in the freeze session |
| **Lane B** | Measurement kit dry-run on CPU JAX, then measure on Cloud TPU v5e after the freeze; ledger; promotion → **U-P10** |
| **Joint exit criterion** | **Gate G4** evaluated and published · `check_ordering` green · `uarch ledger` shows every entry · promotion, if any, scoped to the large-core family |
| **Effort** | A 35 · B 57 · plus Cloud TPU v5e time (§7) |
| **Depends on** | G3a plus authorized hardware access/budget; no product-table dependency |
| **Not in this sprint** | Any model change in response to results. That belongs to G4's fail branch, in a later prompt |

### U6 · Native qualification and diagnostics

| | |
|---|---|
| **Goal** | Qualify the native core built in U4, including initial mesh execution and absolute simulator cost |
| **Lane A** | U-P11c: diagnostics/traces, npu-m256 admission at declared representative points, integrated regression and absolute time/memory measurements |
| **Lane B** | Complete U-P12: independent native verification, discriminating faults, determinism, comparison-scope checks and performance regression gate |
| **Joint exit criterion** | Full **G5** = correctness + performance + automation. Each has its own recorded outcome; correctness alone releases ready U7/U10 work, never closes full G5/U6 |
| **Depends on** | Verified U4a bounded engine and admitted inputs for the scope being qualified. G3a/TPU availability and G4 success do not gate independent U6 work; no accuracy claim without evidence |
| **Not in this sprint** | Rebuilding the U4 core, mandatory fork agreement/speed ratio, C2 depth or threads |
| **Effort** | Re-estimate qualification scope after U-P5; U-P11a/b no longer charged here |

### U7 · Native engine depth, and the mesh class

| | |
|---|---|
| **Goal** | An honest composite C2 from our own engine, at mesh scale, and the first thing a chip architect would use it for |
| **Lane A** | U-P13a–d: deeper NoC/DRAM/compute and composite C2; U-P7 T: first full product table for the declared npu-m256 demo/consumer scope, after required hardware/precision/semantic decisions |
| **Lane B** | U-P14 studies at declared suite points (or grids when consumed), with a tested point/table adapter; prepare Blackhole sourcing/measurement feasibility with A before U8 native admission/freeze |
| **Joint exit criterion** | **G6 + G3b**: verified native C2 mechanisms, first full product table with errors/replay/worker checks, and three study examples. Representative scale points suffice where no grid consumer exists |
| **Effort** | A 145 · B 49 |
| **Depends on** | G5-correctness plus exact product input/semantic decisions. G5-performance/automation may remain open; neither they nor passing G4/G7 gate tables, G6/G3b or U10 |
| **Not in this sprint** | Parallelism inside a simulation |

### U8 · Silicon II: the mesh class

| | |
|---|---|
| **Goal** | Find out whether our engine tracks a real mesh chip, and whether more detail was more accurate |
| **Lane A** | U-P15a implements/tests Blackhole reference admission after B's U-P16 S; then a separate U-P15 session verifies inputs and freezes the signed suite at each available level, with any admitted matched tt-npe scope |
| **Lane B** | U-P16 S owns reference YAML completion/sourcing and measurement feasibility without card access; after U-P15a and U-P15, U-P16 M dry-runs the kit and measures on the authorized card, recording per-level outcomes and optional-reference dispositions |
| **Joint exit criterion** | **Gate G7** evaluated and published · the error table by fidelity level is on the first page · `check_ordering` green |
| **Effort** | A 41 · B 75 · plus the Blackhole p100a and its host (§7) |
| **Depends on** | G6, verified Blackhole suite/reference readiness and authorized hardware access; full table rows are not the measurement input |
| **Not in this sprint** | Model changes in response to results |

### U9 · Parallel engine, and the synchronisation experiment

| | |
|---|---|
| **Goal** | Parallelism inside a simulation that changes no bytes, then a measurement of whether giving up exactness is ever worth it |
| **Lane A** | Row-band partitions, windowed conservative sync with a computed lookahead, byte-identical to single-threaded; lax mode behind a flag → **U-P17** |
| **Lane B** | Pre-registered error-vs-quantum experiment at a credit-backpressured boundary; published curve; the enforcement rule → **U-P18** |
| **Joint exit criterion** | **Gate G8**: exact mode byte-identical at 1, 2, 4 and 8 threads · the curve published with its verdict in the first sentence · a lax result outside a covering curve reports C1 |
| **Effort** | A 125 · B 61 |
| **Depends on** | G6, full G5 (including controlled-host performance and executed self-hosted nightly), and a recorded need: the native engine breaches the prospective U0011-Q representative single-point wall-clock budget, once separately accepted and measured in U-P11c/U-P13d (the small K2/B diagnostic ceiling is not this trigger), or both founders record in an ADR that they want the synchronisation experiment (the funded plan's G1) regardless. Without either, U9 is deferred until after U11, which does not depend on it |
| **Not in this sprint** | Optimistic sync, SIMD, GPU, MPI |

### U10 · Integration into rk-sim

| | |
|---|---|
| **Goal** | A custom ASIC priced at C2 inside a whole-rack rk-sim run, with its conditions visible |
| **Both, first** | rk-sim boundary ADR accepted and its schema PR merged (draft in `rk-sim-side/decisions/`) |
| **Lane A** | rk-sim **P18** (= **U-P19**): the table-backed cost, the nine rules, registry, badges, golden |
| **Lane B** | rk-sim **P19** (= **U-P20**): `<Badged>` conditional, the chip panel, picker rules, the Compare banner, Assumptions |
| **Joint exit criterion** | **Gate G9**: rk-sim golden `asic_c2.yaml` runs · the Fidelity Map shows `C2 · uarch@x · <hash>` · tp double-count test, tp-mismatch test, envelope test and mixed-fidelity pair pass · every rk-sim gate green · rk-sim's own P14 ACCEPTED |
| **Effort** | A 43 · B 55 |
| **Depends on** | G6 + G3b and separately accepted rk-sim boundary at its own sprint boundary. Reader must reject non-C2/inconsistent composites; no silicon-pass prerequisite |
| **Not in this sprint** | Any change to rk-sim beyond the ADR, P18 and P19 |

### U11 · Hardening

| | |
|---|---|
| **Goal** | A stranger can run it; either of you can perform build-spec §1.2 cold |
| **Both** | **U-P21**, with full G5 performance/automation complete before final closure |
| **Joint exit criterion** | **Gate G10**: each of you performs the §1.2 demo cold, twice, with no crashes · a stranger builds a table from the README |
| **Effort** | A 20 · B 20 |
| **Not in this sprint** | Model, threshold or badge-rule changes |

---

## §4 · THE GATES

Every threshold is written before the experiment it judges. A gate decided in the room where
the result was discovered is a retrospective.

**G1 · Contract frozen (U1).**
For U1, Javid (@jjaffari) is the already-authorized acting owner and human approver
for both lanes while Reza is off duty. No Reza approval is claimed or required again
under that recorded delegation. Reviewer acceptance does not accept ADRs or close G1.
- *Pass:* ADR U0001 accepted under the recorded human ownership, with the Rev-2 decisions
  and standalone/prepared-input ownership recorded (concrete payload fields remain U2); the
  `contract` job is green against the toy table; parity fixtures are complete.
- *Fail:* do not start U-P3. A contract that is not frozen is the rework that grows with every
  prompt built on it.

**U2 preparation boundary prerequisite and exit.** At U0003 kickoff, load
[U2 kickoff obligations](reviews/U2-kickoff-obligations.md) and U0002: carry forward
B-F16 and unresolved embedding accounting with their existing owners, budgets and acceptance
requirements; neither is resolved by U1's self-tests. Before implementation, accept U0003's
prepared envelope, identity/validation rules and any public contract revision, then share
its schema with Lane B. Before U3, prove standalone preparation and file replay agree, run
an external fixture without producer dependencies, and prove mismatches fail before execution.
This is part of U2's exit, not a new claim of accuracy or a dependency on rk-sim P16.

**G2 · Native-stage design readiness (U3).** Required before the authorized native tasks:
- exact bounded scope/refusals and M/K1/K2/B/R task acceptance; independent derivations,
  public-boundary faults and conservative U0006 reductions;
- human-approved mapped schema plan; exact protected installation before K2, not K1;
- accepted kernel semantics and exact toolchain/license closure before K1; prospective
  performance workloads/budgets separately accepted before measurements;
- each analytic U-P6 obligation assigned a consumer and deadline, with existing outcomes
  preserved. Required floor/correctness cases precede their first reliance; unrelated
  report completion does not block kernel development;
- reference feasibility and later product decisions scheduled, ownership and revised effort
  recorded. A proposal is not a runtime pass or blanket approval of all its details.

U3 closeout records the accepted design, first-consumer deadlines and explicit pending
implementation/evidence. Exact toolchain/licence approval is required before K1 and exact
protected schema installation before K2; neither is a claim that those U4 tasks ran in U3.
U0011's shared decisions assign B independent component bounds (no new analytic component
API), real Linux CI preparation before K1 credit, and finite-window checks at B versus
stationary Little's law at first qualifying claim. U-P6/build-spec hold the exact approved
DMA/clock statements. The prospective U0002 policy is selected; its code/migration remain
uninstalled and separately authorized. U4 is not released by U3 decision recording.

**G3a · Silicon-suite readiness (U4b).** Gates U5 prediction freeze, not product tables:
- usable sourced TPU reference, explicit unknowns and structural assumptions, representability
  and measurement-observability review; required native formats/operators admitted;
- complete required suite work, including decoder/RoPE/casts/KV/traffic where applicable;
  steady/priming checks at benchmark points; no silent work omission;
- applicable independent L0/L0m/L1, complete-work observations, public-boundary faults,
  mapped producer-disabled replay, debug/release determinism and relied-on U-C0 checks;
- critical-path attribution and diagnostics actually used by G4 verified; attribution is
  a model accounting convention, not proof of the physical cause of error;
- signed suite and frozen-prediction/order infrastructure ready. Hardware access/spend
  is separately authorized. Unsupported required benchmark work blocks this gate or needs
  a human scope amendment; unknown numerical placeholders are not usable chip estimates.

**G3b · First full consumed table (U7).** Separate from silicon success:
- freeze the actual consumer request/envelope, hardware, exact model/precision/tp, policies,
  initial state, coefficients and prepared error jobs. The full npu-m256/70B/FP8/tp8 demo
  remains required unless separately amended; resolve U0022 precision/ragged and hardware
  extensions before dependent work, never omit RoPE or substitute BF16 silently;
- public table/report pipeline, complete required coverage, applicable verification and
  composite from implemented mechanisms. U10's C2 consumer additionally requires G6;
- LOO interpolation error ≤5% median and ≤15% max; composition, layer-reuse, cold/steady
  and priming errors reported with sample counts; envelope refusal and contract vectors;
- repeat and workers 1/N byte identity, authenticated prepared replay with producers off;
- model card reflects actual applicable evidence: STUB/unknown error without validation.
  Failing or unrun G4/G7 does not prohibit tables. Missing required table points or semantic
  prerequisites blocks G3b, not an otherwise ready unrelated silicon campaign.

No mandatory full npu-l4 C1 grid gates U5 and no full C1 mesh grid gates U6. Small tables
and direct results may be used earlier for declared tests/consumers. Large generated grids
must name their consumer; input breadth and engine detail do not establish accuracy.

**G4 · The large-core method tracks silicon (U5).**
- *Setup:* predictions frozen first; ≥24 measurements covering all six classes of U-P9
  (matrix, memory, operator, end-to-end, DRAM gather, launch overhead), each tagged with its
  mapping match and initial state; device-side timing only.
- *Pass:* median |error| ≤25% and no class median above 50% (the funded plan's E6a bar).
  Cards are promoted to estimated for the large-core family and passing classes only. The
  verdict is stated per mapping-match group (matched, compiler-chosen); an empty group is "no
  evidence", never a pass.
- *Fail:* the card stays stub, and **the errors are published anyway**.
  - If the attribution heuristic assigns ≥70% of the error to one subsystem, allow one bounded investigation/fix prompt, measured against
    a **new** frozen prediction set. This selects a hypothesis, not a proven cause.
    Compute the allocation by script from the frozen predictions: each benchmark's |error| is assigned to the subsystem with the largest share
    of that prediction's `attribution_s`, and the test is whether one subsystem receives ≥70%
    of the summed |error|.
  - Otherwise the honest status is "verified, unvalidated", and the plan continues on that
    basis.

**G5 · Independent native qualification (U6), three explicit obligations.**
- **G5-correctness:** required scope-qualified literal/behavioral cases pass: counts,
  transfers, clocks/critical paths, conservation, ordering, capacity/queue limits,
  serialization/overlap, public-boundary faults with restored controls, L0/L0m/L1,
  mapped producer-disabled replay and debug/release identity. Batch workers 1/N where
  delivered; full-table worker checks are G3b. Qualify diagnostics/attribution and
  representative npu-m256 admission, rerun integrated regressions and obtain independent
  review. Missing/failed required correctness blocks U7/G6/G3b/U10 dependent work.
- **G5-performance:** prospective U0011 budgets and U0012 noise/regression controls evaluated
  on the designated controlled Linux host, with exact workload/environment and observations.
  Publish exceeded budgets honestly; those findings inform U9 rather than imply accuracy.
- **G5-automation:** an executed applicable self-hosted nightly, with real suite/environment
  receipts. A registered idle runner or no-op job is not completion.
- **Full G5:** all three obligations complete. Missing performance or automation leaves
  full G5/U6 closure pending, and blocks U9 entry, any simulator-performance claim and final
  closure. It does not block U7/G6/G3b/U10 once correctness and their own requirements pass.
  Observations collected to establish performance readiness are provisional while either
  host evidence or nightly is missing, never qualified claims.
- Optional external comparisons retain scope/failures/unavailable/not-independent outcomes;
  no whole-fork agreement or speed-ratio requirement. Missing optional evidence cannot
  discharge correctness. No G5 outcome establishes silicon accuracy.

**G6 · Native composite C2 (U7).** Requires G5-correctness, not G5-performance/automation.
U-P13d separates functional scale admission from host metrics; missing host/nightly cannot
silently become a C2/table/integration prerequisite. Performance obligations remain open.
- *Pass:* compute is at level 2, NoC and DRAM at level 2 or 1+ts, and sync is exact (build-spec
  §2.4); no row is faster than its U-C0 roofline; new mechanisms pass independent mathematical/behavioral
  checks, and any prospectively admitted compatible L2 bounds hold. Absent optional references
  stay disclosed; C2 denotes represented detail, never validated accuracy.
- *Fail:* report the actual lower composite, honestly usable within that scope. It does
  not satisfy G6 or U10's C2-only admission; no relabeling to complete G9.

**G7 · The mesh method tracks silicon (U8).** G4's thresholds, applied to native composite C2
on the mesh family, over ≥36 measurements covering all eight classes of U-P15 (end-to-end
among them).
- *Pass:* cards are promoted for the mesh family.
- *Fail:* the same branch as G4.
- *Either way:* the per-level error table answers whether detail helped. "Closer" means a
  lower median |error| per class, reported per class and as the median across classes, never
  pooled. If C2 is not closer than level 1, say so on the first page, and keep the level-1
  fast path as the default for studies.

**G8 · Synchronisation verdict (U9).**
- *Pass:* exact mode is byte-identical at every thread count, and the error-vs-quantum curve
  meets the pre-registered criterion (≥5× over conservative at ≤10% distribution deviation,
  labelled as the funded plan's own assumption). Lax mode becomes available as C2 inside its
  covered range.
- *Fail:* publish the curve anyway. Lax mode stays C1 everywhere, and exact mode remains the
  only C2 path. The funded plan's G1 has its answer.

**G9 · Integrated (U10).**
- *Pass:* G6 + G3b and the exit criterion above, including non-C2/inconsistent-detail
  rejection; rk-sim's P14 is ACCEPTED. G5-correctness gates this work; full G5
  performance/automation may remain open. No silicon-pass requirement is added.
- *Fail:* uarch stays standalone (a CLI, tables and reports), and rk-sim's main is untouched
  beyond the accepted ADR.

**G10 · Definition of done (U11).**
- *Pass:* full G5, including controlled-host performance and executed self-hosted nightly,
  is complete; build-spec §1.2 is performed cold twice by each founder, and a stranger
  builds a table from the README. Starting U7/U10 earlier does not waive final closure gates.
- *Fail:* file each failure as a bug against its owning prompt, fix it, and rerun.

---

## §5 · PER-SPRINT VERIFICATION CHECKLIST

This is the same list U-REVIEW walks.

| # | Check | Where the rule lives |
|---|---|---|
| 1 | Applicable exits run from a fresh hosted Linux checkout and separate fresh local clone on the same published commit; controlled-host checks where required | U0023 / §3 |
| 2 | No number reaches a human without badge, conditions and error band | `report/README.md` |
| 3 | No stipulation outside `hw/designs/`; no claim without a source | `hw/README.md` |
| 4 | Golden diffs: none, or each justified by an ADR | `tests/golden/README.md` |
| 5 | Required stage-applicable L0/L0m/L1 and mutants executed; unsupported/not_run stays explicit, real nightly required by G5 | U0006 / U0023 |
| 6 | Replay/debug-release determinism at native stages; 1/N table workers when that path is delivered; 1/N threads from U9 | build-spec §6.6 |
| 7 | No composite C2 that breaks the rule; no row below its U-C0 | build-spec §2.4 |
| 8 | Predictions precede results; nothing frozen was edited | `validation/L3_silicon/README.md` |
| 9 | Model cards promoted only by the ledger, and only in scope | `validation/ledger/README.md` |
| 10 | Nothing from build-spec §1.3's out list was built | build-spec §1.3 |
| 11 | Every README is still true | build-spec §4 |
| 12 | U-REVIEW's three stages are complete per lane; how-it-works.md is refreshed by a fresh session | `docs/prompts/` |
| 13 | Unmodelled quantities are null, never 0; energy says "unverified" until its rung exists; no engine reads a DRAM preset the spec does not name | build-spec §2.6, §6.11 |

---

## §6 · PROMPT INDEX

| Prompt | Sprint · Lane | What it builds |
|---|---|---|
| **U-P0** | U0 · either | Repo bootstrap (prefer `BOOTSTRAP-PROMPT.md`) |
| **U-P1** | U1 · joint → A | The contract |
| **U-P2** | U1 · B | Vendored rk-sim snapshot and FLOP parity |
| **U-P3** | U2 · A | Hardware specs, workload graph, U-C0, first table |
| **U-P4** | U2 · B | Badges, model cards, applicability, the report |
| **U-P5** | U3 · A | Bounded native-stage design, protocol and verification readiness |
| **U-P6** | U3 · B | L0 invariants, L0m metamorphic, mutants |
| **U-P7** | U4 M / U7 T · A | Early mapping/fixtures; later consumer-driven grid, interpolation/errors and first full product table |
| **U-P8** | U4 · B | L1 limits (with hand fixtures), L2 differential |
| **U-P9** | U5 · A | TPU v5e reference model; frozen predictions |
| **U-P10** | U5 · B | TPU measurement kit; ledger; promotion; G4 |
| **U-P11a** | U4a · A | K1 internal kernel; K2 approved public protocol wiring |
| **U-P11b** | U4a B / U4b R · A | Bounded models, then required reference-suite coverage/admission and attribution |
| **U-P11c** | U6 · A | Native qualification, diagnostics, G5 and absolute host cost |
| **U-P12** | U4/U6 · B | Independent verification, scoped comparisons, determinism and metrics |
| **U-P13a** | U7 · A | Native NoC at 1+ts; NoC barriers |
| **U-P13b** | U7 · A | Native DRAM: queues with back-pressure, Ramulator 2, interleaving |
| **U-P13c** | U7 · A | Native compute level 2: bank conflicts, DMA interleave |
| **U-P13d** | U7 · A | Mesh policies, the composite rule, C2 at mesh scale |
| **U-P14** | U7 · B | Design studies |
| **U-P15a** | U8 preparation · A | Implement/verify Blackhole native admission from U-P16 S reference handoff |
| **U-P15** | U8 · A | Verify admitted Blackhole reference; freeze predictions per level |
| **U-P16** | U8 · B | S reference completion/readiness; M kit, measurements and per-level verdict/G7 |
| **U-P17** | U9 · A | Parallel engine: exact conservative mode, labelled lax mode |
| **U-P18** | U9 · B | The synchronisation experiment; G8 |
| **U-P19** | U10 · A · *in rk-sim* | rk-sim P18: characterized C2 cost |
| **U-P20** | U10 · B · *in rk-sim* | rk-sim P19: stipulations and chip views |
| **U-P21** | U11 · both | Demo hardening |
| **U-REVIEW** | every sprint end, per lane | Adversarial review, three stages |
| **STANDING** | every sprint end | how-it-works refresh |

---

## §7 · Historical effort baseline — re-estimation required

The tables below are the superseded Rev 2 effort/calendar/cost baseline, retained for audit.
They are **not estimates for Rev 3**. Retired U-P5 work cannot simply be subtracted: U-P11a/b
move into U4, independent verification grows, and mapped-v2 scope needs concrete design.
U-P5 must provide a new stage-by-stage engineering/review estimate and separate human/host
waits. No current savings, completion date or measured hours are claimed. The feasibility
package's Python U-C1 design/implementation estimates are not authorized scope.

Historical section follows unchanged:

**Method.** Each prompt is estimated per prompt from its task items and acceptance tests, in
person-hours of a founder driving and reviewing agent sessions. That is the same unit as
rk-sim's plan. Every sprint also carries U-REVIEW and the how-it-works refresh: 2.5 h best and
5 h realistic per lane per sprint from U1 on.

The spread is deliberately wide. Lane A in rk-sim's S3 ran about 60 h against about 35
nominal. In the other direction, rk-sim's recorded actuals for S1–S3 ran at a third to a half
of committed. So for the non-engine prompts the "best" column may be the honest one. The
native-engine prompts (U-P11a–c, U-P13a–d, U-P17) are the softest numbers here, and the least
likely to come in early.

### 7.1 Per prompt

Rev 2 raised U-P1, U-P3–U-P11, U-P13–U-P16, U-P19 and U-P20 for the book-coverage items.
That adds about 94 h realistic in total. Rev 2.1 split U-P11 and U-P13 without changing their
totals. The other Rev 2.1 fixes (tp sharding, fused attention, the end-to-end mesh class, an
output-stationary policy, controller queues, the deferred energy rung and shared-SRAM support)
are **not yet re-estimated**; until they are, treat every row they touch as a lower bound.

| Prompt | Lane | Best | Realistic |
|---|---|---|---|
| U-P0 bootstrap | either | 4 | 8 |
| U-P1 contract | A (joint) | 16 | 30 |
| U-P2 snapshot + parity | B | 8 | 16 |
| U-P3 hardware, workload, U-C0 | A | 23 | 42 |
| U-P4 honesty layer + report | B | 18 | 34 |
| U-P5 fork + adapter | A | 26 | 52 |
| U-P6 L0 + L0m | B | 14 | 26 |
| U-P7 mapping, grid, C2 table | A | 34 | 64 |
| U-P8 L1 + L2 | B | 27 | 52 |
| U-P9 TPU reference + predictions | A | 18 | 34 |
| U-P10 TPU measurement + ledger | B | 30 | 56 |
| U-P11a native kernel | A | 25 | 45 |
| U-P11b native models + executor | A | 45 | 90 |
| U-P11c native diagnostics + G5 | A | 25 | 45 |
| U-P12 differential + metrics | B | 24 | 44 |
| U-P13a native NoC 1+ts | A | 22 | 44 |
| U-P13b native DRAM + Ramulator 2 | A | 20 | 40 |
| U-P13c native compute level 2 | A | 18 | 36 |
| U-P13d mesh policies + composite | A | 18 | 36 |
| U-P14 design studies | B | 27 | 50 |
| U-P15 Blackhole reference + predictions | A | 22 | 40 |
| U-P16 Blackhole measurement + ledger | B | 39 | 76 |
| U-P17 parallel engine | A | 60 | 120 |
| U-P18 synchronisation experiment | B | 30 | 56 |
| rk-sim boundary schema PR | both | 6 | 12 |
| U-P19 (rk-sim P18) | A | 19 | 34 |
| U-P20 (rk-sim P19) | B | 25 | 46 |
| U-P21 demo hardening | both | 16 | 30 |
| U-REVIEW + refresh, U1–U11 | both | 55 | 110 |

### 7.2 Per sprint and lane

| Sprint | A best | A realistic | B best | B realistic | Sprint realistic | Cumulative realistic |
|---|---|---|---|---|---|---|
| U0 | 4 | 8 | — | — | 8 | 8 |
| U1 | 18.5 | 35 | 10.5 | 21 | 56 | 64 |
| U2 | 25.5 | 47 | 20.5 | 39 | 86 | 150 |
| U3 | 28.5 | 57 | 16.5 | 31 | 88 | 238 |
| U4 | 36.5 | 69 | 29.5 | 57 | 126 | 364 |
| U5 | 20.5 | 39 | 32.5 | 61 | 100 | 464 |
| U6 | 97.5 | 185 | 26.5 | 49 | 234 | 698 |
| U7 | 80.5 | 161 | 29.5 | 55 | 216 | 914 |
| U8 | 24.5 | 45 | 41.5 | 81 | 126 | 1,040 |
| U9 | 62.5 | 125 | 32.5 | 61 | 186 | 1,226 |
| U10 | 24.5 | 45 | 30.5 | 57 | 102 | 1,328 |
| U11 | 10.5 | 20 | 10.5 | 20 | 40 | 1,368 |
| **Total** | **~434** | **~836** | **~281** | **~532** | **~1,368** | |

### 7.3 Milestones

| Reached at the end of | What exists | Best | Realistic |
|---|---|---|---|
| U4 | A verified table from a published engine (C2 if its levels qualify), badged STUB | ~190 h | ~364 h |
| U5 | …validated (or not, and published) against a large-core chip | ~243 h | ~464 h |
| U7 | Our own engine at composite C2, mesh scale, design studies | ~477 h | ~914 h |
| U8 | …validated (or not) against a mesh chip, with the "did detail help" answer | ~543 h | ~1,040 h |
| U9 | Parallel exact mode; the synchronisation verdict (if U9's gate opens) | ~638 h | ~1,226 h |
| U11 | Integrated in rk-sim, demo performed cold: **done** | **~714 h** | **~1,368 h** |

### 7.4 Converting to calendar

A sprint ends only when both lanes integrate (§1), so the calendar follows the longer lane in
each sprint, not either lane's total. Lane A is longer in U0–U4, U6, U7, U9 and U11; Lane B in
U5, U8 and U10. Summing the longer lane per sprint from §7.2 gives ~469 h best and ~906 h
realistic.

At rk-sim's own planning rate of 20 h/week per person (its execution-plan §2):
- best case ≈ 23 weeks;
- realistic ≈ 45 weeks.

That is before U5 and U8's serial step (measurement starts only after the freeze), before the
Rev 2.1 fixes are re-estimated (§7.1), and with U9 included. U6, U7 and U9 hold most of it.
Moving the two items named in §2 to Lane B shortens U7; a deferred U9 removes ~125 h realistic
from the calendar.

### 7.5 Money

These costs are listed as facts, not as constraints. Prices were checked on 2026-09-27.

| Item | Cost |
|---|---|
| Cloud TPU v5e, U5 | $1.20 per chip-hour on demand. 50–100 chip-hours ≈ $60–120 |
| Tenstorrent Blackhole p100a, U8 | $999 per the vendor's store page, plus a PCIe 5.0 ×16 host running Ubuntu 22.04. The host is not priced |
| Optional large-machine parallel-scaling run, U9 | An AWS c7a.48xlarge (192 physical cores) at $3.489/h spot. An 8-hour run ≈ $30 |

---

## §8 · THINGS THAT WILL BE TEMPTING AND ARE WRONG

| Temptation | Why it's wrong |
|---|---|
| "One production engine means it only needs self-consistency tests" | Independent mathematical derivations, behavioral mutants and silicon evidence remain necessary; a production helper cannot generate its own expected answers |
| "The chip is ours, so its parameters are claims" | Until silicon exists they are design choices. Call them stipulations, or every badge downstream lies |
| "Composite C1 looks bad in the deck. Call it C2" | The composite rule exists so the level means something. C1 is an honest, shippable answer |
| "Tune the reservation NoC until it matches BookSim" | Tuning to a reference turns an independent check into a mirror. Record the gap and its mechanism |
| "That measurement is obviously wrong. Adjust the prediction" | Predictions are frozen. A new prediction is a new file in a new commit, and the old one stays |
| "Averaged over all classes we're under 25%" | Averaging across classes to pass a gate is the one failure the ledger refuses |
| "It's deterministic, so the error bar is zero" | Determinism is not accuracy. The band is "unknown" until the ledger says otherwise |
| "Lax sync is 5× faster. Make it the default" | Lax sync is C1 outside a covering curve, and exact mode stays the default |
| "Add an ONNX importer so customers can bring any model" | It is a second workload IR. That is the rework the contract exists to prevent |
| "rk-sim could just import uarch and call it. It's all Python" | Files, not calls. rk-sim's engine stays pure, and neither side can break the other's build |
| "Put uarch inside rk-sim. One clone is easier" | Then every `git add -A` in rk-sim sweeps it in, and every rk-sim agent sees a C2 simulator it must not build |
| "Skip the hand fixtures. The tests pass" | They are the defence against plausible garbage: numbers that look right and aren't |
| "Ramulator's default preset is close enough; skip the DRAM timing fields" | Then numbers that decide the answer are not claims, and nobody can say where they came from |
| "Unmodelled? Just put 0" | Zero is a result. Null is the honest answer when a level does not model something |
| "Average the speedups across the suite" | An arithmetic mean of ratios rewards whichever workload moved most. Use the geometric mean, and show each workload |
| "The kit warms up; the simulator doesn't need to" | Then every L3 error mixes warm silicon with a cold prediction. Stipulate the initial state |
| "Use `unsafe` in the hot loop; it's faster" | Only the Ramulator 2 bridge may hold `unsafe`. Measure first: the engine's speed comes from its event design, not from skipping bounds checks |
| "Rust or agreement with another simulator makes the result accurate" | Language safety and L0–L2 verification are not L3 validation; fidelity follows represented mechanisms and accuracy requires applicable silicon evidence |
| "Build the table at tp = 1 and let rk-sim divide" | The tp divisor is 1. A table is one rank of the split uarch built, for one tp; any other tp is refused |

---

*Companion documents: `docs/build-spec.md` (architecture, contract, layout, conventions, prompt
texts) · `rk-uarch-track-verdict-and-plan.md` in the Project (research and reasoning).*

U0003 S replaces the physical nominal-parity subject, not its evidence by implication. The
accepted U0021 host arrangement remains; its check-scope addendum names both tracks,
complete discrepancy inventory, null policy and contributor-safe display tests. Historic
nominal inputs, A-F12, oracle lifecycle, U3 runners and later silicon work remain required.

Current U2 authority: [accepted decision](reviews/U2-U0003-acceptance-record.md) and
[common baseline](reviews/U2-common-baseline-v1.md). Accepted S replaces the old physical
nominal-parity gates; it does not claim they passed. All runtime exits remain outstanding.

B1 input decision accepted: [U0004/H1/H2 and draft-only references](reviews/U2-B1-acceptance-record.md).
The [frozen B1 addition](reviews/U2-common-baseline-b1-addendum.md) supplements unchanged
baseline v1. Input acceptance is not physical validation or a completed B-F16 exit.

Corrected A1 checkpoint: [coordinator recheck](reviews/U2-publication-history.md#a1).
Shared interfaces are reconciled; A2/B2 handoffs are prepared. Remaining runtime,
artifact, independent-review and publication checks are not completed by this checkpoint.

B2 intermediate intake: [coordinator review](reviews/U2-publication-history.md#b2-intake).
One source-scope correction precedes active B2 integration. Declared A2/report/tooling
dependencies remain open; the generator fingerprint gate has not been waived.

Corrected B2: [recheck and partial integration](reviews/U2-publication-history.md#b2-correction).
B2-C1 is resolved; the integrated generator fingerprint gate still fails. Exact
proof/energy protocol, A2-dependent runtime/report checks and tooling freeze remain pending.

A2 interfaces: [coordinator reconciliation](reviews/U2-publication-history.md#a2).
Delivered to B; standalone production and full runtime exits remain pending. B
consumer input-kind mismatch and the generator fingerprint gate remain explicit.
