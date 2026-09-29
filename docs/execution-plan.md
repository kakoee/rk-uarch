# rk-uarch — Execution Plan

**The working document:** twelve sprints (U0–U11), two lanes, ten gates. For each sprint it
says what to build, who builds it, which prompt to run, and the one thing you must be able to
run at the end.

**Canonical for:** *what order and who*. For *what* and *how* (architecture, contract, repo
layout, conventions and the prompt texts) see `docs/build-spec.md`.

**Sprints here are defined by content, not by the calendar.** A sprint ends when its joint
exit criterion runs, its U-REVIEW loops are ACCEPTED, and a human tags it. §7 gives the
effort each sprint's prompts imply, in hours, derived from the prompts.

---

## STATUS

| | |
|---|---|
| **Not started** | U0–U11 |

Update this block and `docs/how-it-works.md` at every sprint boundary.

---

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
| U-P3 ∥ U-P4 | Provenance works on the table's shape, which U-P1 fixed; a toy table is enough |
| U-P5 ∥ U-P6 | L0 and L0m run against U-C0; they do not need the fork |
| U-P7 ∥ U-P8 | L1 is written against closed forms; L2 against standalone references |
| U-P11 ∥ U-P12 | The harness needs the engine protocol, not the native engine |
| U-P13 ∥ U-P14 | Studies run on any engine through the table interface |
| U-P17 ∥ U-P18 | Pre-registration and the harness can land before the parallel engine does |

**Serial inside a sprint.** Named so nobody schedules them together:

| Order | Why |
|---|---|
| U-P9 → U-P10 (measurement step) | Predictions must be committed before any measurement exists. Lane B writes and dry-runs its kit in parallel, and measures only after the freeze |
| U-P15 → U-P16 (measurement step) | Same rule |
| Boundary schema PR → U-P19 → U-P20 | Both run in rk-sim and touch provenance. The schema PR comes first, then P18, then P19 |

**Where the lanes are uneven.** U6, U7 and U9 are bound by Lane A (§7). If you want those
sprints to close sooner, the cleanest work to move to Lane B is the mesh mapping policies
(U-P13 item 4) and the Ramulator 2 library linking (U-P13 item 2). Both sit behind existing
interfaces.

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
| **Lane A** | *Both founders present:* the contract → **U-P1** |
| **Lane B** | Vendored rk-sim snapshot, FLOP-parity fixtures from rk-sim's own code, round-trip tests → **U-P2** |
| **Joint exit criterion** | **Gate G1** · the `contract` CI job green against the toy table · parity fixtures for ≥3 ModelSpecs × ≥24 queries · ADR U0001 accepted by both |
| **Effort** | A 31 · B 21 h realistic |
| **Depends on** | U0 · a local rk-sim clone at a named SHA |
| **Not in this sprint** | Any engine; any field for a later sprint |

> U-P1 is the one prompt both of you should sit through. Everything downstream codes against it.

### U2 · The first honest number

| | |
|---|---|
| **Goal** | A hashed table end to end, whose every number says what it may claim |
| **Lane A** | Four hardware specs, `derive_rk_params`, the workload graph with FLOP parity, U-C0 (aggregate and per-op), the minimal table path, `uarch validate` and `uarch table` → **U-P3** |
| **Lane B** | Badges (claims, stipulations, the model as contributor, the ceiling), model cards, applicability, `uarch report` through `badged()` → **U-P4** |
| **Joint exit criterion** | `uarch table hw/designs/npu-l4.yaml … --engine analytic` → `uarch report` shows "conditional · N stipulations", "error: unknown", composite C0 · U-C0 aggregate = rk-sim C0 within ±0.1% on every parity fixture |
| **Effort** | A 41 · B 35 |
| **Depends on** | G1 |
| **Not in this sprint** | Fork; native; interpolation |

### U3 · The fork

| | |
|---|---|
| **Goal** | A published cycle-level NPU simulator, driven by a uarch request, reproducibly |
| **Lane A** | Pre-register G2, build the engine image, write the adapter, evaluate ONNXim (then PyTorchSim if needed) → **U-P5** |
| **Lane B** | L0 invariants and L0m metamorphic property suites, with mutants that prove they bite → **U-P6** |
| **Joint exit criterion** | **Gate G2** decided and recorded in ADR U0005 · a one-layer decode query built by the fork from a ModelSpec · L0 and L0m green on U-C0 and run on the fork |
| **Effort** | A 53 · B 27 |
| **Depends on** | U2 |
| **Not in this sprint** | Mapping policies; grids |

### U4 · The real table

| | |
|---|---|
| **Goal** | A complete C2 table: verified, with its own errors measured, and badged STUB because it has not yet met silicon |
| **Lane A** | Mapping policies (`ws-rowsplit@1`, `onnxim-compat@1`), grid, pool, interpolation, LOO and composition errors, frequency axis → **U-P7** |
| **Lane B** | L1 analytical limits, including two hand-computed fixtures, and L2 differential against BookSim 2, Ramulator 2 and SCALE-Sim v3 → **U-P8** |
| **Joint exit criterion** | **Gate G3**: the `npu-l4` × 70B-class table, fp8 and bf16 · byte-identical at 1 and N workers · L0, L0m and L1 pass · NoC L2 bound met · model card `stub` |
| **Effort** | A 61 · B 47 |
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
| **Lane A** | The C++20 engine: time base, events, wheel, ownership, compute level 1, NoC and DRAM level 0, TaskGraph executor → **U-P11** |
| **Lane B** | Native-vs-fork differential harness with attribution, determinism gates, simulator metrics and the regression gate → **U-P12** |
| **Joint exit criterion** | **Gate G5** · the full L0, L0m and L1 suites pass on native · npu-m256 (a mesh the fork cannot model) builds a table |
| **Effort** | A 175 · B 49 |
| **Depends on** | G3 (G4 need not have passed: a native engine is worth building either way; it just cannot claim accuracy yet) |
| **Not in this sprint** | Threads, SIMD, GPU |

### U7 · Native engine depth, and the mesh class

| | |
|---|---|
| **Goal** | An honest composite C2 from our own engine, at mesh scale, and the first thing a chip architect would use it for |
| **Lane A** | Reservation NoC with cycle timestamps, Ramulator 2 as a library, SRAM banks and DMA interleave, mesh mapping policies, the composite rule → **U-P13** |
| **Lane B** | Design studies: variants, the diff report, a local-sensitivity tornado, energy with conditions → **U-P14** |
| **Joint exit criterion** | **Gate G6**: npu-m256 composite C2 with honest detail · contention visibly bites at level ≥1 and not at level 0 · the two example studies render |
| **Effort** | A 145 · B 49 |
| **Depends on** | G5 |
| **Not in this sprint** | Parallelism inside a simulation |

### U8 · Silicon II: the mesh class

| | |
|---|---|
| **Goal** | Find out whether our engine tracks a real mesh chip, and whether more detail was more accurate |
| **Lane A** | Blackhole reference model; SUITE.md signed with B; predictions frozen at every fidelity level, plus tt-npe's → **U-P15** |
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
| **Depends on** | G6 |
| **Not in this sprint** | Optimistic sync, SIMD, GPU, MPI |

### U10 · Integration into rk-sim

| | |
|---|---|
| **Goal** | A custom ASIC priced at C2 inside a whole-rack rk-sim run, with its conditions visible |
| **Both, first** | rk-sim boundary ADR accepted and its schema PR merged (draft in `rk-sim-side/decisions/`) |
| **Lane A** | rk-sim **P18** (= **U-P19**): the table-backed cost, the six rules, registry, badges, golden |
| **Lane B** | rk-sim **P19** (= **U-P20**): `<Badged>` conditional, the chip panel, picker rules, the Compare banner, Assumptions |
| **Joint exit criterion** | **Gate G9**: rk-sim golden `asic_c2.yaml` runs · the Fidelity Map shows `C2 · uarch@x · <hash>` · tp double-count test, envelope test and mixed-fidelity pair pass · every rk-sim gate green · rk-sim's own P14 ACCEPTED |
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
- *Pass:* ADR U0001 accepted by both founders; the `contract` job is green against the toy
  table; parity fixtures are complete.
- *Fail:* do not start U-P3. A contract that is not frozen is the rework that grows with every
  prompt built on it.

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

**G3 · A C2 table exists (U4).**
- *Pass:* one proposed design, one ModelSpec, fp8 and bf16, tp = 1, over a declared envelope.
  L0, L0m and L1 pass. The NoC is within 10% of BookSim 2 below 70% saturation.
  Leave-one-out interpolation error is ≤5% median and ≤15% max. Composition error is reported.
  Builds are byte-identical. The model card says stub.
- *Fail:* do not measure silicon. An unverified model compared against silicon produces an
  error nobody can attribute. Fix what failed, then rerun G3.

**G4 · The large-core method tracks silicon (U5).**
- *Setup:* predictions frozen first; ≥20 measurements across ≥3 classes.
- *Pass:* median |error| ≤25% and no class median above 50% (the funded plan's E6a bar).
  Cards are promoted to estimated for the large-core family and passing classes only.
- *Fail:* the card stays stub, and **the errors are published anyway**.
  - If one subsystem explains ≥70% of the error, allow one bounded fix prompt, measured against
    a **new** frozen prediction set.
  - Otherwise the honest status is "verified, unvalidated", and the plan continues on that
    basis.

**G5 · Native agrees with fork (U6).**
- *Pass:* at matched mapping and levels, durations agree within 3% on ≥95% of grid points;
  results are byte-identical at 1 and N workers; the speed factor is measured against the one
  written in ADR U0011.
- *Fail:* the disagreement is the finding. Bisect it by subsystem with U-P12's attribution,
  then fix it, or narrow the native engine's declared scope in an ADR.

**G6 · Native composite C2 (U7).**
- *Pass:* every shared resource is at level 2 or 1+ts and sync is exact; no row is faster than
  its U-C0 roofline; L2 bounds hold against the native engine.
- *Fail:* report the composite as C1. That is still a shippable, honest answer.

**G7 · The mesh method tracks silicon (U8).** G4's thresholds, applied to native composite C2
on the mesh family.
- *Pass:* cards are promoted for the mesh family.
- *Fail:* the same branch as G4.
- *Either way:* the per-level error table answers whether detail helped. If C2 is not closer
  than level 1, say so on the first page, and keep the level-1 fast path as the default for
  studies.

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
| **U-P7** | U4 · A | Mapping policies, grid, interpolation, measured errors, the C2 table |
| **U-P8** | U4 · B | L1 limits (with hand fixtures), L2 differential |
| **U-P9** | U5 · A | TPU v5e reference model; frozen predictions |
| **U-P10** | U5 · B | TPU measurement kit; ledger; promotion; G4 |
| **U-P11** | U6 · A | Native engine core |
| **U-P12** | U6 · B | Differential harness; determinism; simulator metrics |
| **U-P13** | U7 · A | Native depth: contention, Ramulator 2, mesh policies, composite rule |
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
native-engine prompts (U-P11, U-P13, U-P17) are the softest numbers here, and the least likely
to come in early.

### 7.1 Per prompt

| Prompt | Lane | Best | Realistic |
|---|---|---|---|
| U-P0 bootstrap | either | 4 | 8 |
| U-P1 contract | A (joint) | 14 | 26 |
| U-P2 snapshot + parity | B | 8 | 16 |
| U-P3 hardware, workload, U-C0 | A | 20 | 36 |
| U-P4 honesty layer + report | B | 16 | 30 |
| U-P5 fork + adapter | A | 24 | 48 |
| U-P6 L0 + L0m | B | 12 | 22 |
| U-P7 mapping, grid, C2 table | A | 30 | 56 |
| U-P8 L1 + L2 | B | 22 | 42 |
| U-P9 TPU reference + predictions | A | 16 | 30 |
| U-P10 TPU measurement + ledger | B | 28 | 52 |
| U-P11 native core | A | 90 | 170 |
| U-P12 differential + metrics | B | 24 | 44 |
| U-P13 native depth + mesh | A | 70 | 140 |
| U-P14 design studies | B | 24 | 44 |
| U-P15 Blackhole reference + predictions | A | 20 | 36 |
| U-P16 Blackhole measurement + ledger | B | 36 | 70 |
| U-P17 parallel engine | A | 60 | 120 |
| U-P18 synchronisation experiment | B | 30 | 56 |
| rk-sim boundary schema PR | both | 6 | 12 |
| U-P19 (rk-sim P18) | A | 18 | 32 |
| U-P20 (rk-sim P19) | B | 24 | 44 |
| U-P21 demo hardening | both | 16 | 30 |
| U-REVIEW + refresh, U1–U11 | both | 55 | 110 |

### 7.2 Per sprint and lane

| Sprint | A best | A realistic | B best | B realistic | Sprint realistic | Cumulative realistic |
|---|---|---|---|---|---|---|
| U0 | 4 | 8 | — | — | 8 | 8 |
| U1 | 16.5 | 31 | 10.5 | 21 | 52 | 60 |
| U2 | 22.5 | 41 | 18.5 | 35 | 76 | 136 |
| U3 | 26.5 | 53 | 14.5 | 27 | 80 | 216 |
| U4 | 32.5 | 61 | 24.5 | 47 | 108 | 324 |
| U5 | 18.5 | 35 | 30.5 | 57 | 92 | 416 |
| U6 | 92.5 | 175 | 26.5 | 49 | 224 | 640 |
| U7 | 72.5 | 145 | 26.5 | 49 | 194 | 834 |
| U8 | 22.5 | 41 | 38.5 | 75 | 116 | 950 |
| U9 | 62.5 | 125 | 32.5 | 61 | 186 | 1,136 |
| U10 | 23.5 | 43 | 29.5 | 55 | 98 | 1,234 |
| U11 | 10.5 | 20 | 10.5 | 20 | 40 | 1,274 |
| **Total** | **~405** | **~778** | **~263** | **~496** | **~1,274** | |

### 7.3 Milestones

| Reached at the end of | What exists | Best | Realistic |
|---|---|---|---|
| U4 | A verified C2 table from a published engine, badged STUB | ~170 h | ~324 h |
| U5 | …validated (or not, and published) against a large-core chip | ~219 h | ~416 h |
| U7 | Our own engine at composite C2, mesh scale, design studies | ~437 h | ~834 h |
| U8 | …validated (or not) against a mesh chip, with the "did detail help" answer | ~498 h | ~950 h |
| U9 | Parallel exact mode; the synchronisation verdict | ~593 h | ~1,136 h |
| U11 | Integrated in rk-sim, demo performed cold: **done** | **~667 h** | **~1,274 h** |

### 7.4 Converting to calendar

Converting to calendar time depends only on hours per week, and Lane A is the critical path
(~405 h best, ~778 h realistic).

At rk-sim's own planning rate of 20 h/week per person (its execution-plan §2):
- best case ≈ 20 weeks;
- realistic ≈ 39 weeks.

U6, U7 and U9 hold most of that. Moving the two items named in §2 to Lane B shortens those
sprints.

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

---

*Companion documents: `docs/build-spec.md` (architecture, contract, layout, conventions, prompt
texts) · `rk-uarch-track-verdict-and-plan.md` in the Project (research and reasoning).*
