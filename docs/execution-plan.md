# rk-uarch — Execution Plan

**The working document:** twelve sprints (U0–U11), two lanes, ten gates. For each sprint it
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

## STATUS

| | |
|---|---|
| **U0 done** | Tagged `u00-end` at `a5a4cc4`: bootstrap, protected files, build-spec Rev 2, pushed to the private remote |
| **Accepted** | 2026-10-03: both founders accept the Rev 2.1 fixes from `docs/reviews/rev2-plan-review.md` (and Revs 2.2–2.3) |
| **rk-sim pin** | `1e5706e0ebfcc67c1a7333079a35b75f693e9963` (rk-sim `main`, verified 2026-10-04), fixed for U1 so U-P1 and U-P2 use the same baseline; U-P1 records it in ADR U0001 |
| **Next** | Commit and push as separately authorized steps, then hosted CI and Linux-box cold-clone validation; G1/U1 closure remains pending |
| **In progress** | U1: both lane reviews ACCEPTED; Javid accepted complete U0001/U0002 and authorized snapshot adoption/integration on 2026-10-06; integrated locally, uncommitted |
| **Not started** | U2–U11 |
| **Paused** | The `nightly` workflow's schedule (2026-10-03): no self-hosted runner yet. Re-enable it when U3 starts (U3, "Before it starts") |

Update this block and `docs/how-it-works.md` at every sprint boundary.

Current U1 acceptance and artifact identities are recorded in
[U1 acceptance and adoption](reviews/U1-acceptance-and-adoption.md). Earlier proposal
and partial-approval notes below remain historical; they do not override that acceptance.

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
| 4 | **Integrate.** Merge both lanes to `main`, then check the joint exit criterion on the Linux box from a cold clone | both |
| 5 | Run **U-REVIEW** on the *other* lane's work, in a fresh session. All three stages | each, crossed |
| 6 | Run `STANDING-how-it-works-refresh.md` in a fresh session. Tag `uNN-end`, log actual hours, then a 15-minute retro: *what did the agents get wrong?* | both |

**The standing rule:** `main` always builds a table. A sprint whose two lanes did not integrate
did not finish.

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
| U-P5 ∥ U-P6 | L0 and L0m run against U-C0; they do not need the fork |
| U-P7 ∥ U-P8 | L1 is written against closed forms; L2 against standalone references |
| U-P11a–c ∥ U-P12 | The harness needs the engine protocol, not the native engine |
| U-P13a–d ∥ U-P14 | Studies run on any engine through the table interface |
| U-P17 ∥ U-P18 | Pre-registration and the harness can land before the parallel engine does |

**Serial inside a sprint.** Named so nobody schedules them together:

| Order | Why |
|---|---|
| U-P9 → U-P10 (measurement step) | Predictions must be committed before any measurement exists. Lane B writes and dry-runs its kit in parallel, and measures only after the freeze |
| U-P15 → U-P16 (measurement step) | Same rule |
| Boundary schema PR → U-P19 → U-P20 | Both run in rk-sim and touch provenance. The schema PR comes first, then P18, then P19 |
| U-P11a → U-P11b → U-P11c | Kernel, then models, then diagnostics and G5 |
| U-P13a, U-P13b, U-P13c → U-P13d | The three subsystems in any order, then the composite rule that needs all three |

**Where the lanes are uneven.** U6, U7 and U9 are bound by Lane A; U5, U8 and U10 by Lane B
(§7). If you want U7 to close sooner, the cleanest work to move to Lane B is the mesh mapping
policies (U-P13d item 1) and the Ramulator 2 library linking (U-P13b). Both sit behind
existing interfaces.

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
| **Lane A** | U0003 schema/identity prerequisite; four hardware specs, `derive_rk_params`, standalone versioned workload preparation with FLOP parity/paged KV, prepared bundle export/import, U-C0 over resolved operators, minimal table path and existing CLI → **U-P3** |
| **Lane B** | Badges (claims, stipulations, the model as contributor, the ceiling), model cards, applicability over the full scope vector, `uarch report` through `badged()` with diagnostics and a per-op roofline → **U-P4** |
| **Joint exit criterion** | `uarch table hw/designs/npu-l4.yaml … --engine analytic` → `uarch report` shows "conditional · N stipulations", "error: unknown", "not modelled" for null diagnostics, composite C0 · U-C0 aggregate = rk-sim C0 within ±0.1% on every parity fixture, each fed that fixture's own component params · the graph is one rank of a tp-way split, with attention fused · `uarch characterize` runs on the demo request · local preparation exports a bundle whose analytic replay is byte-identical with the producer disabled; imported supported fixtures run without rk-sim/compiler; input mismatches and stale hashes fail |
| **Effort** | Original baseline A 41 · B 35; re-estimate prepare/replay work at U0003 before scheduling (§7 has the unamended baseline) |
| **Depends on** | G1; settle U0003's concrete prepared-input and any public contract revision before the two lane implementations diverge |
| **Not in this sprint** | Fork; native; interpolation; detailed tiling/mapping policies; compiler or rk-sim exporter |

### U3 · The fork

| | |
|---|---|
| **Goal** | A published cycle-level NPU simulator, driven by a uarch request, reproducibly |
| **Lane A** | Pre-register G2, build the engine image, write the adapter, evaluate ONNXim (then PyTorchSim if needed) → **U-P5** |
| **Lane B** | L0 invariants and L0m metamorphic property suites, with mutants that prove they bite → **U-P6** |
| **Joint exit criterion** | **Gate G2** decided and recorded in ADR U0005 · standalone model preparation and saved prepared-workload replay reach the fork with preserved rank shapes · fork mapping delegation/unsupported exact mappings are explicit · L0 and L0m green on U-C0 and run on the fork |
| **Effort** | A 53 · B 27 |
| **Depends on** | U2 |
| **Before it starts** | Register the Linux box as a self-hosted runner labelled `uarch` (GitHub → Settings → Actions → Runners), then **re-enable the `schedule:` line in `.github/workflows/nightly.yml`**, paused since 2026-10-03. Trigger one run by hand and see it go green before U-P5 starts |
| **Not in this sprint** | Mapping policies; grids |

### U4 · The real table

| | |
|---|---|
| **Goal** | A complete table from the fork, at the composite its levels earn (C2 only if they qualify): verified, with its own errors measured, and badged STUB because it has not yet met silicon |
| **Lane A** | Mapping policies (`ws-rowsplit@1`, `os-tiled@1`, `onnxim-compat@1`) with declared dataflow and SRAM placement, fused attention tiling, grid, pool, interpolation, LOO, composition, layer-reuse and cold-vs-steady (with warm-up) errors, frequency axis → **U-P7** |
| **Lane B** | L1 analytical limits (derated DRAM, latency-bound streams), including two hand-computed fixtures; L2 differential against BookSim 2, Ramulator 2 and SCALE-Sim v3, refusing self-comparisons → **U-P8** |
| **Joint exit criterion** | **Gate G3**: the `npu-l4` × 70B-class table, fp8 and bf16, tp = 8 · composite as §2.4's rule gives for ADR U0005's levels · byte-identical at 1 and N workers · mapped TaskGraph export/import/replay preserves inputs and refuses incompatible mappings · L0, L0m and L1 pass · NoC L2 bound met, or recorded as not independent · model card `stub` |
| **Effort** | Original baseline A 61 · B 47; re-estimate mapped import/replay when U0003 fixes the schema |
| **Depends on** | G2 |
| **Not in this sprint** | Silicon; native |

### U5 · Silicon I: the large-core class

| | |
|---|---|
| **Goal** | Find out whether the method tracks a real large-core chip, and say so either way |
| **Lane A** | Reference model of TPU v5e; SUITE.md signed with B; predictions frozen and committed first → **U-P9** |
| **Lane B** | Measurement kit dry-run on CPU JAX, then measure on Cloud TPU v5e after the freeze; ledger; promotion → **U-P10** |
| **Joint exit criterion** | **Gate G4** evaluated and published · `check_ordering` green · `uarch ledger` shows every entry · promotion, if any, scoped to the large-core family |
| **Effort** | A 35 · B 57 · plus Cloud TPU v5e time (§7) |
| **Depends on** | G3 |
| **Not in this sprint** | Any model change in response to results. That belongs to G4's fail branch, in a later prompt |

### U6 · Native engine core

| | |
|---|---|
| **Goal** | Our own engine, checked against the fork on the same work |
| **Lane A** | The Rust engine, in three sessions: time base, events, wheel, ownership and the protocol → **U-P11a**; compute level 1, NoC and DRAM level 0, the TaskGraph executor and attribution → **U-P11b**; diagnostics, traces, G5 and the measured speed factor → **U-P11c** |
| **Lane B** | Native-vs-fork differential harness with attribution, determinism gates, simulator metrics and the regression gate → **U-P12** |
| **Joint exit criterion** | **Gate G5**, or its recorded rescheduling to U7 if no fork configuration matches native's levels · the full L0, L0m and L1 suites pass on native · saved mapped inputs execute with producers disabled and comparisons verify resolved mapping correspondence · npu-m256 (a mesh the fork cannot model) builds a table |
| **Effort** | A 175 · B 49 |
| **Depends on** | G3 (G4 need not have passed: a native engine is worth building either way; it just cannot claim accuracy yet) |
| **Not in this sprint** | Threads, SIMD, GPU |

### U7 · Native engine depth, and the mesh class

| | |
|---|---|
| **Goal** | An honest composite C2 from our own engine, at mesh scale, and the first thing a chip architect would use it for |
| **Lane A** | In four sessions: reservation NoC with cycle timestamps and NoC barriers → **U-P13a**; DRAM queues with back-pressure, Ramulator 2 as a library configured from the spec, address interleaving → **U-P13b**; SRAM bank conflicts and DMA interleave (shared SRAM listed as unrepresented) → **U-P13c**; mesh mapping policies, the composite rule, mesh-scale tables → **U-P13d** |
| **Lane B** | Design studies over a versioned workload suite: variants, the diff report with geometric-mean speedup, a local-sensitivity tornado, energy with conditions → **U-P14** |
| **Joint exit criterion** | **Gate G6**: npu-m256 composite C2 with honest detail · contention, interleaving, back-pressure and bank conflicts visibly bite at level ≥1 and not below · the three example studies render · G5, if it was rescheduled from U6 |
| **Effort** | A 145 · B 49 |
| **Depends on** | G5 |
| **Not in this sprint** | Parallelism inside a simulation |

### U8 · Silicon II: the mesh class

| | |
|---|---|
| **Goal** | Find out whether our engine tracks a real mesh chip, and whether more detail was more accurate |
| **Lane A** | Blackhole reference model; SUITE.md signed with B, with an end-to-end class; predictions frozen at every fidelity level, plus tt-npe's → **U-P15** |
| **Lane B** | TT-Metalium kit, dry-run on ttsim, then measure on the card after the freeze; ledger; the per-level error table → **U-P16** |
| **Joint exit criterion** | **Gate G7** evaluated and published · the error table by fidelity level is on the first page · `check_ordering` green |
| **Effort** | A 41 · B 75 · plus the Blackhole p100a and its host (§7) |
| **Depends on** | G6 |
| **Not in this sprint** | Model changes in response to results |

### U9 · Parallel engine, and the synchronisation experiment

| | |
|---|---|
| **Goal** | Parallelism inside a simulation that changes no bytes, then a measurement of whether giving up exactness is ever worth it |
| **Lane A** | Row-band partitions, windowed conservative sync with a computed lookahead, byte-identical to single-threaded; lax mode behind a flag → **U-P17** |
| **Lane B** | Pre-registered error-vs-quantum experiment at a credit-backpressured boundary; published curve; the enforcement rule → **U-P18** |
| **Joint exit criterion** | **Gate G8**: exact mode byte-identical at 1, 2, 4 and 8 threads · the curve published with its verdict in the first sentence · a lax result outside a covering curve reports C1 |
| **Effort** | A 125 · B 61 |
| **Depends on** | G6, and a recorded need: the native engine breaches ADR U0011's single-point wall-clock budget (measured in U-P11c and U-P13d), or both founders record in an ADR that they want the synchronisation experiment (the funded plan's G1) regardless. Without either, U9 is deferred until after U11, which does not depend on it |
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
| **Depends on** | G3 at minimum (G6 recommended) · an rk-sim sprint boundary |
| **Not in this sprint** | Any change to rk-sim beyond the ADR, P18 and P19 |

### U11 · Hardening

| | |
|---|---|
| **Goal** | A stranger can run it; either of you can perform build-spec §1.2 cold |
| **Both** | **U-P21** |
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

**G2 · Fork chosen (U3).** All five must hold, and the per-point budget is set in ADR U0005
before measuring:
- (a) the fork builds unattended in the container;
- (b) three runs are byte-identical;
- (c) decode matrix-op parity is within 0.5% after named deviations, with no deviation above 5%;
- (d) per-point wall-clock is within the budget;
- (e) every linked licence is permissive.

*Pass:* U4 uses that fork. *Fail (both candidates):*
- build a Python U-C1 harness and ship it labelled **C1**;
- record "C2 via fork: unbuilt";
- U5 still runs, against C1;
- U6 proceeds with the native engine and no fork reference, and its G5 criterion becomes
  "agrees with U-C1 at matched levels".

For G2, the fork adapter must preserve the prepared workload and disclose internal mapping.
It refuses an exact imported mapping it cannot honor; passing G2 never establishes otherwise.

**G3 · A full table exists (U4).**
- *Pass:* one proposed design, one ModelSpec, fp8 and bf16, tp = 8, over a declared envelope.
  Its composite is what build-spec §2.4's rule gives for the fork's levels in ADR U0005: C2
  only if they qualify, otherwise C1, said so. L0, L0m and L1 pass. The NoC is within 10% of
  BookSim 2 below 70% saturation, unless the fork's NoC is BookSim 2 itself, in which case the
  check is recorded as not independent and waits for U-P13a.
  Leave-one-out interpolation error is ≤5% median and ≤15% max. Composition, layer-reuse and
  cold-vs-steady errors are reported. The derated-DRAM and latency-bound L1 checks pass.
  Builds are byte-identical. The model card says stub.
- *Fail:* do not measure silicon. An unverified model compared against silicon produces an
  error nobody can attribute. Fix what failed, then rerun G3.

**G4 · The large-core method tracks silicon (U5).**
- *Setup:* predictions frozen first; ≥24 measurements covering all six classes of U-P9
  (matrix, memory, operator, end-to-end, DRAM gather, launch overhead), each tagged with its
  mapping match and initial state; device-side timing only.
- *Pass:* median |error| ≤25% and no class median above 50% (the funded plan's E6a bar).
  Cards are promoted to estimated for the large-core family and passing classes only. The
  verdict is stated per mapping-match group (matched, compiler-chosen); an empty group is "no
  evidence", never a pass.
- *Fail:* the card stays stub, and **the errors are published anyway**.
  - If one subsystem explains ≥70% of the error, allow one bounded fix prompt, measured against
    a **new** frozen prediction set. "Explains" is computed by script from the frozen
    predictions: each benchmark's |error| is assigned to the subsystem with the largest share
    of that prediction's `attribution_s`, and the test is whether one subsystem receives ≥70%
    of the summed |error|.
  - Otherwise the honest status is "verified, unvalidated", and the plan continues on that
    basis.

**G5 · Native agrees with fork (U6).**
- *Pass:* at matched mapping and levels (the fork's levels as ADR U0005 classifies them),
  durations agree within 3% on ≥95% of grid points; results are byte-identical at 1 and N
  workers; the speed factor is measured against the one written in ADR U0011. If no fork
  configuration matches native's U6 levels, G5 is not run on mismatched levels: the mismatch
  is recorded and G5 runs in U7, after U-P13a–c, at the closest matching configuration.
- *Fail:* the disagreement is the finding. Bisect it by subsystem with U-P12's attribution,
  then fix it, or narrow the native engine's declared scope in an ADR.

**G6 · Native composite C2 (U7).**
- *Pass:* compute is at level 2, NoC and DRAM at level 2 or 1+ts, and sync is exact (build-spec
  §2.4); no row is faster than its U-C0 roofline; L2 bounds hold against the native engine.
- *Fail:* report the composite as C1. That is still a shippable, honest answer.

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
- *Pass:* the exit criterion above, and rk-sim's P14 is ACCEPTED.
- *Fail:* uarch stays standalone (a CLI, tables and reports), and rk-sim's main is untouched
  beyond the accepted ADR.

**G10 · Definition of done (U11).**
- *Pass:* build-spec §1.2 is performed cold, twice by each founder, and a stranger builds a
  table from the README.
- *Fail:* file each failure as a bug against its owning prompt, fix it, and rerun.

---

## §5 · PER-SPRINT VERIFICATION CHECKLIST

This is the same list U-REVIEW walks.

| # | Check | Where the rule lives |
|---|---|---|
| 1 | The joint exit criterion runs on the Linux box from a cold clone | §3 |
| 2 | No number reaches a human without badge, conditions and error band | `report/README.md` |
| 3 | No stipulation outside `hw/designs/`; no claim without a source | `hw/README.md` |
| 4 | Golden diffs: none, or each justified by an ADR | `tests/golden/README.md` |
| 5 | L0, L0m and L1 green for every engine; mutants caught (nightly) | `validation/README.md` |
| 6 | Determinism: 1 vs N workers, and 1 vs N threads from U9, byte-identical | build-spec §6.6 |
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
| **U-P5** | U3 · A | Fork selection, engine image, adapter |
| **U-P6** | U3 · B | L0 invariants, L0m metamorphic, mutants |
| **U-P7** | U4 · A | Mapping policies, grid, interpolation, measured errors, the first full table |
| **U-P8** | U4 · B | L1 limits (with hand fixtures), L2 differential |
| **U-P9** | U5 · A | TPU v5e reference model; frozen predictions |
| **U-P10** | U5 · B | TPU measurement kit; ledger; promotion; G4 |
| **U-P11a** | U6 · A | Native kernel: time, events, wheel, ownership, protocol |
| **U-P11b** | U6 · A | Native models (compute 1, NoC 0, DRAM 0), TaskGraph executor, attribution |
| **U-P11c** | U6 · A | Native diagnostics, traces, G5, measured speed factor |
| **U-P12** | U6 · B | Differential harness; determinism; simulator metrics |
| **U-P13a** | U7 · A | Native NoC at 1+ts; NoC barriers |
| **U-P13b** | U7 · A | Native DRAM: queues with back-pressure, Ramulator 2, interleaving |
| **U-P13c** | U7 · A | Native compute level 2: bank conflicts, DMA interleave |
| **U-P13d** | U7 · A | Mesh policies, the composite rule, C2 at mesh scale |
| **U-P14** | U7 · B | Design studies |
| **U-P15** | U8 · A | Blackhole reference model; frozen predictions per level |
| **U-P16** | U8 · B | Blackhole measurement kit; the per-level verdict; G7 |
| **U-P17** | U9 · A | Parallel engine: exact conservative mode, labelled lax mode |
| **U-P18** | U9 · B | The synchronisation experiment; G8 |
| **U-P19** | U10 · A · *in rk-sim* | rk-sim P18: characterized C2 cost |
| **U-P20** | U10 · B · *in rk-sim* | rk-sim P19: stipulations and chip views |
| **U-P21** | U11 · both | Demo hardening |
| **U-REVIEW** | every sprint end, per lane | Adversarial review, three stages |
| **STANDING** | every sprint end | how-it-works refresh |

---

## §7 · EFFORT, DERIVED FROM THE PROMPTS

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
| "Skip the fork and write our own engine first. That's the interesting part" | With no fork, the native engine's only reference is itself. U6's G5 is only meaningful because U4 exists |
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
| "The fork is a cycle-level simulator, so its table is C2" | Levels come from build-spec §2.4's table, per sub-model, recorded in ADR U0005. A fork with no bank-conflict model gives C1 |
| "Build the table at tp = 1 and let rk-sim divide" | The tp divisor is 1. A table is one rank of the split uarch built, for one tp; any other tp is refused |

---

*Companion documents: `docs/build-spec.md` (architecture, contract, layout, conventions, prompt
texts) · `rk-uarch-track-verdict-and-plan.md` in the Project (research and reasoning).*
