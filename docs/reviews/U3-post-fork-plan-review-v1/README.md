# U3 post-fork plan review (v1)

Independent review of the plan after U0005 removed the mandatory external fork.
2026-10-12. **Recommendations only.** No plan, prompt, ADR, contract, workflow, code or
evidence was changed. Nothing here accepts a proposal, closes a gate, authorizes lane
implementation or represents Javid's decision.

## Reviewed scope and authority

| Item | Identity |
| --- | --- |
| rk-uarch HEAD / tree | `afb35022971e56703fe35104b818b8a226c039d7` / `b3dd42e39ca86d765df10c9c732c61009050b687`; clean; a dry-run fetch showed no newer remote commits |
| Architecture amendment | `1f2beb9` (U0005 and the 27-path documentation patch). This is the **accepted** direction and the currently installed requirements |
| A proposal | `bc01563` `docs/reviews/U3-native-stage-design-v1/` (**unaccepted**, including proposed U0011) |
| B readiness | `14f40ad` + `afb3502` `docs/reviews/U3-B-verification-readiness-v1/` (**unaccepted**; C1–C5 are proposals) |
| rk-sim (read only) | Local checkout `34f5706` (not fetched): `CLAUDE.md`, `docs/execution-plan.md` STATUS, `rk/engine/f0/compute.py`. `docs/vision/` was not read |

Other authority categories:

- **Historical:** the execution plan's §7 effort, `U3-fork-feasibility-v2`, and pre-amendment
  text at `7fbb0f3`. These were used only to trace where obligations came from.
- **Conversation-only, not adopted:** the coordinator's narrower runner policy (it appears
  only in A's description of it) and the four intermediate-table hypotheses.

## 1. Verdict

**Sound with bounded amendments.** The architecture is right: one progressive Rust engine,
the retained U-C0 baseline, independent literal and behavioral verification, optional scoped
references, and frozen-prediction silicon validation. A's first stage (M → K → B) is modest,
useful, and grows into the intended engine.

The schedule after that stage is not executable as written. Four problems block it:

- **G3 gates the wrong thing.** G3 makes a full npu-l4 table a prerequisite for the first
  silicon campaign, but that campaign consumes none of it.
- **Gates and prompts cannot be met.** G3 cannot be satisfied on the accepted hardware and
  RoPE semantics. U-P9 cannot run, because no task produces a usable TPU v5e reference or
  native support for it.
- **U10 is stale.** It still depends on "G3 at minimum", which now produces a C1 table for a
  reader that admits only C2 and labels everything it admits as C2.
- **Inherited obligations tax unrelated work.** The U0002 support inventory and the runner
  prerequisite both impose recurring costs on work their rationale does not cover.

Each of these can be fixed locally: amend U0005's ordering section, the execution plan for
U4–U6 and U10, and a few prompts. None requires redesign. Section 5 compares this minimal
amendment with broader replanning.

## 2. Five most consequential conclusions

1. **The intermediate tables should not gate silicon.** U4b has become the fork's old "first
   complete table" stage without the fork's purpose. That purpose was an early C2 product
   table that rk-sim could read (`7fbb0f3` execution-plan U4). A native C1 table for npu-l4
   has no consumer before U7/U10. The first silicon campaign needs decoder-layer coverage,
   verification and the reference chip. It does not need a 672-point grid, FP8, os-tiled,
   interpolation or composition error.
2. **The current critical path runs through unscheduled or blocked work.** G3 waits on three
   undecided semantic and hardware changes. U5 waits on a TPU reference spec (only a draft
   exists, with a 1-unit stub clock and array) and on native admission of that chip. No
   prompt schedules either, and U-P9 forbids engine changes.
3. **Two inherited obligations tax every future step.** Every Python file in the repo is
   bound to the U1/U2 nominal-oracle adoption lifecycle; the probe in §9 confirmed this. A
   self-hosted runner gates even compiling the engine. Neither rationale covers native
   correctness work.
4. **The integration risk is real but cheap to retire early.** The actual rk-sim work is
   bounded by rk-sim's own schedule (post-S12; rk-sim is in S6). A test-only conformance
   check in rk-uarch against the already-vendored `IterationCost` can find contract gaps now,
   without claiming C2 or touching rk-sim.
5. **Accuracy feedback comes too late.** A's compute-1 interval law is a convention that
   only silicon can test. The current order puts the largest investment (T, which A estimates
   at 116–204 h; U4 totals 264–444 h) before the first accuracy signal. Reorder so the first
   silicon campaign follows the verification and decoder coverage it actually needs.

## 3. Findings (most severe first)

Classification key:

- **C:** contradiction
- **U:** unjustified dependency
- **M:** missing decision or deliverable
- **W:** likely waste
- **R:** unresolved uncertainty

### PF-01 · High · U, W — The full U4b table gates silicon that does not use it

- **Evidence.**
  - `docs/execution-plan.md:239`: U5 depends on G3.
  - `:355-367`: G3 requires npu-l4 × 70B, fp8 and bf16, tp8, both policies, LOO ≤5%/15%,
    composition, layer-reuse and cold/steady errors. Its fail branch says "do not measure
    silicon". U0005 repeats this order at lines 60-66.
  - U-P9 (`docs/build-spec.md:2632-2647`) predicts TPU v5e microbenchmarks: 8B-class
    operators, one decoder layer, bf16 and int8. It uses no npu-l4 row, no FP8 and no
    interpolated value.
  - U-P9 selects shapes with `uarch characterize`, which has existed since U2. It does not
    need table rows.
  - A sizes T at A 64–112 h, B 40–72 h and review 12–20 h, "low confidence"
    (`U3-native-stage-design-v1/delivery.md:16,19-24`).
  - A's ceiling of 60 s per point over 672 points allows 11.2 h per serial build, before
    error jobs and the repeated determinism builds (`delivery.md:150-157`).
  - The FP8 rows cannot be promoted by U5 evidence in any case, because U-P9 names only bf16
    and int8.
- **Scenario.** B passes. The team spends T effort and several human decisions on FP8, the
  output-stationary policy and ragged batches, then runs 11 h+ builds. U5 then shows that the
  interval law misprices small-m decode tiles, and every npu-l4 table is regenerated anyway.
- **Strongest case for the plan.** G3 stops an unverified, incomplete engine from meeting
  silicon. The grid also exercises breadth and determinism at scale.
- **Assessment.** Verification and decoder completeness should be kept, and §5 keeps them.
  Grid density, interpolation, composition error, the frequency axis, FP8 and os-tiled are
  properties of a *consumed table*, not of readiness to meet silicon. Smaller declared runs
  also exercise determinism.
- **Minimum correction.** Split G3:
  - **G3a, silicon readiness**, gates U5.
  - **G3b, first consumed table**, is evaluated when a consumer needs it (U7/U10).
  - **Alternative:** keep G3 as written but let U5 depend only on G3a's content.
- **Affects:** U0005 ordering; execution-plan U4/U5/G3; U-P7 item 8 and its acceptance;
  U-P9; U-P11b.
- **Preserve:** every G3 verification item; "unsupported required points block, never drop
  silently"; the measured table errors (moved, not deleted); STUB and unknown error.
- **Human decision:** yes, because it changes the ordering in an accepted ADR.

### PF-02 · High · C, M — G3 cannot pass on the accepted inputs

- **Evidence.**
  - `hw/designs/npu-l4.yaml:31-33` declares only `weight_stationary`, and `:159-165` declares
    only bf16. G3 needs fp8 (`execution-plan.md:356`) and `os-tiled@1`
    (`build-spec.md:2426,2497`).
  - U0022 refuses FP8 and mixed formats (`U0022:125-126`) and packed, ragged or offset
    sequences (`:89`).
  - U-P7's composition error needs unequal batches with the same (B, T, Q)
    (`build-spec.md:2451-2455`).
  - A lists all three as blockers (`delivery.md:40-51,66-71`; `next-decision.md:36-40`).
  - `npu-l4.yaml` is a support-bound file (PF-05), so revising it also costs an adoption
    cycle.
- **Scenario.** T stalls on decisions about FP8 RoPE semantics that no TPU benchmark uses, and
  U5 waits behind it.
- **Strongest case for the plan.** U0005 says unsupported points block G3 or need an accepted
  scope change, so the plan blocks honestly.
- **Assessment.** The honesty holds, but the block sits on the path to the first accuracy
  signal.
- **Correction.** Under PF-01, defer each decision to its real consumer:
  - FP8 semantics: npu-m256 fp8 demo rows.
  - Ragged extension: composition error for any consumed table.
  - npu-l4 output-stationary/FP8 revision: the U-P14 dataflow study.
  - If G3 stays unchanged, all three must be decided now.
- **Human decision:** yes.

### PF-03 · High · M — U5's real prerequisites are unscheduled, and U-P9 cannot run as written

- **Evidence.**
  - `hw/references/` contains only `.keep`.
  - `hw/U2-sourcing-inventory.md:24-32` keeps the TPU and Blackhole specs as drafts: "No
    physical runs, performance reporting or L3 use is approved".
  - The draft `tests/fixtures/u2_b/hardware-review/tpu-v5e.yaml` has:
    - core `freq_hz` as a stub with carrier value 1.0 (line 5);
    - array rows and columns as 1×1 stubs (lines 70-71);
    - bf16 MAC/cycle as a 1.0 stub (line 75);
    - 46 stub leaves against 4 sourced claims (my count).
  - U-P3 required a usable reference (`build-spec.md:1983-1988`). U2 accepted it as a draft
    only.
  - U-P9 says "Configure the native engine for the reference" (`:2657-2661`). Its guardrail
    says "Do not change the engine in this prompt" (`:2682-2683`).
  - A admits only the npu-l4 hash; T covers npu-l4 and U6 covers npu-m256
    (`proposed-U0011.md:22-31`; `delivery.md:76-80`).
  - Nothing admits TPU v5e or int8 (`build-spec.md:2636`).
  - The old plan configured "the fork via config_writer" (`7fbb0f3` build-spec 2680-2681).
    That capability was removed without a replacement.
- **Scenario.** A worker running U-P9 literally finds no reference and an engine that refuses
  the TPU hash, so it must stop.
- **Uncertainty.** I did not check whether HardwareSpec can represent TPU v5e's matrix-unit
  organization. The answer may require a protected contract change.
- **Correction.** Add three items to G3a:
  - B: a sourced `hw/references/tpu-v5e.yaml`, with unknowns counted. This is desk research
    with no spend and can start now.
  - A: native admission of that spec, including int8 if it is declared, with literal cases.
  - A and B: a representability note.
- **Human decision:** yes to commission the work and to decide any contract extension.

### PF-04 · High · C — U10's minimum dependency puts a C1 table into a C2-only reader

- **Evidence.**
  - `execution-plan.md:300` reads "G3 at minimum (G6 recommended)". Git blame dates it to
    bootstrap `0868dd3`, when G3 could be C2 (`7fbb0f3` lines 353-355). G3 is now at most C1
    (`:357-358`).
  - The boundary draft admits only C2 ("It does not admit C1"; `rk-sim-side/decisions/DRAFT-…:32-34,99`).
  - P18 registers the table reader as the compute C2 path and writes "C2" into the Fidelity
    Map (`rk-sim-side/prompts/P18-…:63-75`). Neither its task nor its acceptance tests
    (`:82-96`) check the table's `composite_fidelity`.
- **Scenario.** U10 runs on its stated minimum. rk-sim then shows `C2 · uarch@x · <hash>` for
  a table whose subsystem levels are compute 1, NoC 0 and DRAM 0.
- **Strongest case for the plan.** G6 is recommended, and U10's goal says C2.
- **Assessment.** A literal worker following P18 would admit the C1 table and label it C2,
  because nothing refuses it.
- **Correction.**
  - Set U10's dependency to G6 (plus G3b).
  - Add a P18 refusal and test for `composite_fidelity ≠ C2`.
  - Admitting declared composites in rk-sim would be a larger scope change against rk-sim's
    own §1.3. I don't recommend it now.
- **Human decision:** yes, for both founders (rk-sim boundary).

### PF-05 · High · U, W — The U0002 support inventory binds all Python to oracle adoption

- **Evidence.**
  - `scripts/u2_inputs.py:44-63` binds every `*.py` under `src/rkuarch`,
    `contract/uarch_contract` and `scripts`, plus `pyproject.toml`, `uv.lock` and
    `hw/designs/npu-l4.yaml`.
  - The binding is enforced at `:168-173` through `scripts/vendor_rk.py:478-480`, which the
    hosted CI `contract` job runs (`.github/workflows/ci.yml:52-53`).
  - Any change needs the U0002 lifecycle (`U0002:231-247`): freeze, human generates twice,
    audit, compare, explicit approval, adoption.
  - Prior cycles: U2 v1–v3 and U3 v1, each with 3–29 record files.
  - B and A both carry this forward (`U3-B-verification-readiness-v1/README.md:137-138`;
    `proposed-U0011.md:107-108`).
  - **Probe:** see §9. Even deleting the leftover `src/rkuarch/engines/fork/__init__.py`
    ("Adapter to the pinned fork. Lands in U-P5.") would trigger a cycle.
- **Scenario.** Every U4 checkpoint turns hosted CI red until a human runs a two-run oracle
  regeneration. That includes M's contract carriers, mapping policies, the native Python
  adapter, table grid/pool code and CLI flags. The subject being refreshed is the nominal
  FLOP-parity of U-C0 against rk-sim at pin `1e5706e`.
- **Strongest case for the plan.** It proves the committed oracle came from exactly the
  present code. Over-binding is simpler than proving an import closure.
- **Assessment.** The binding is to file bytes, not to oracle behavior. It also penalizes
  cleanup.
- **Correction.** Pick one:
  - Bind only the generator's real dependency closure.
  - Replace source hashing with a CI regenerate-and-compare check, requiring human adoption
    only when outputs change.
  - Keep the binding but budget batched adoption windows.
  Changing `scripts/u2_inputs.py` is itself bound, so one final cycle is unavoidable.
- **Uncertainty.** I did not trace the generator's actual import closure.
- **Human decision:** yes (U0002 is an accepted ADR).

### PF-06 · Medium-High · U — The runner prerequisite gates work that ordinary CI covers

- **Evidence.**
  - Where the requirement lives:
    - U0005:89-92 and `execution-plan.md:213-214,226`;
    - the U-P11a prerequisites (`build-spec.md:2774-2777`);
    - `containers/README.md:5-6`;
    - "Docker, built on the Linux box only" (`build-spec.md:816`).
  - Where it came from: the old U3 "Before it starts" row required the runner before U-P5
    (`7fbb0f3` execution-plan:106), in the fork-container era.
  - Current CI state:
    - Hosted CI already defines a `native` job: cargo fmt, clippy `-D warnings`, test and
      cargo-deny on `ubuntu-latest` (`ci.yml:74-85`).
    - Only `nightly.yml:11` targets `[self-hosted, linux, uarch]`, and its schedule is paused.
  - Past exceptions: U0020 and U0021 were needed because the per-sprint Linux-box cold-clone
    exit (`execution-plan.md:119,445`; `build-spec.md:3818`) could not be met.
  - GitHub limits: a hosted job can run for 6 h and a self-hosted job for 5 days
    ([GitHub Actions limits](https://docs.github.com/en/actions/reference/limits), fetched
    2026-10-12).
- **Needs the controlled host:**
  - U0011/U0012 absolute time/memory budgets and the noise-aware regression threshold
    (G5 performance);
  - U9 scaling measurements;
  - runs longer than about 6 h (full tables, the sync experiment).
- **Ordinary hosted CI is enough for:**
  - Rust build, lint, licences and tests;
  - debug/release and repeat determinism;
  - the literal corpus and fault injection;
  - Python suites and small native goldens;
  - cold-clone correctness exits.
- **Strongest case for the plan.** One controlled environment, image digests in provenance,
  no WSL performance claims, and no no-op readiness.
- **Assessment.** These concerns all attach to *performance* evidence and long runs. A
  second platform actually strengthens the determinism evidence.
- **Correction.**
  - Implementation and correctness proceed on hosted Linux with a pinned toolchain.
  - Require the designated host, with receipts, before any performance claim (G5
    performance, U9).
  - Require the self-hosted nightly before the first suite that cannot run within hosted
    limits, and in any case before G5.
  - Replace per-sprint exception ADRs with a standing rule: a fresh hosted checkout plus one
    fresh local clone.
  - Keep "no no-op readiness" and "no WSL performance claim".
- **Human decision:** yes.

### PF-07 · Medium · U — The kernel is serialized behind the protected schema and the runner

- **Evidence.**
  - U-P11a: "No kernel work before" M's human-committed protocol, the fixtures and the runner
    (`build-spec.md:2774-2777`).
  - U0005:55-56 orders U-P7 first, then U-P11a.
  - U-P11a acceptance tests 1, 1a, 2, 3 and 5 cover time, edges, events, the wheel,
    ownership and fixed-delay critical paths. None of them needs the mapped schema. Only
    tests 4 and 6 (the Python round-trip and protocol drift) do (`:2837-2856`).
- **Scenario.** Kernel work waits for protected carrier installation, an adoption cycle
  (PF-05) and runner registration (PF-06), although its core has no technical dependency on
  any of them.
- **Strongest case for the plan.** It avoids a "parallel Rust-only format".
- **Assessment.** In-crate unit fixtures are not a protocol. The rule only needs to bind the
  subprocess boundary.
- **Correction.**
  - **K1:** kernel internals after the toolchain/licence pin is accepted, on hosted CI.
  - **K2:** protocol wiring after M.
- **Human decision:** light, because it changes the order U0005 states.

### PF-08 · Medium · C — U5's fail branch uses attribution that is only qualified after U5

- **Evidence.**
  - G4's fail branch assigns each benchmark's |error| using `attribution_s` from the frozen
    predictions (`execution-plan.md:378-382`).
  - Attribution and diagnostics are qualified in G5/U6 (`:391-393`; U-P11c), after U5.
    U0005:65-66 deliberately removes any U5→U6 dependency.
- **Scenario.** G4 fails. The single allowed fix prompt then targets the subsystem chosen by
  unqualified attribution.
- **Correction.**
  - Add critical-path attribution tests and discriminating faults to G3a.
  - Diagnostics may stay null for U5, which is honest; U-P10 just records fewer
    diagnostic-fidelity entries.
- **Human decision:** included in the PF-01 decision.

### PF-09 · Medium · W — U6 repeats U4 and builds a mesh table that U7 replaces

- **Evidence.**
  - G5 (`execution-plan.md:387-394`) re-lists L0/L0m/L1, replay, debug/release and worker
    determinism. U-P11b and U-P12 already require these at U4 (`build-spec.md:2913-2930,3020-3023`).
  - U6 builds a full npu-m256 table at NoC 0 (`:2953-2957`; A's ceiling is 120 s per point).
    U-P13d then builds the C2 mesh table (`:3215-3228`).
  - The only consumer of the C1 mesh table is G5.
- **What U6 adds that is genuinely new:**
  - independent review of the expanded scope;
  - diagnostics and traces;
  - host cost and the regression gate (on the designated host);
  - mesh route, clock and controller admission.
- **Correction.** Reduce U6 to that delta, with mesh admission at prospectively declared
  representative points. Move the full mesh table to U7, at the composite it earns.
- **Preserve:** U6 independent review, and "missing measurements leave qualification pending".
- **Human decision:** yes (G5 scope).

### PF-10 · Medium · U — G2 bundles analytic U-P6 completion with native design acceptance

- **Evidence.**
  - G2 requires "required U-P6 analytic checks executed" (`execution-plan.md:347`;
    U0005:52-54).
  - B's remaining proposals C1–C5 are substantial analytic-only work
    (`U3-B-verification-readiness-v1/README.md:50-139`).
  - The native K and B stages consume none of it.
  - U-C0 does have consumers: the predictions in U5/U8 and the roofline floor.
- **Assessment.** That work belongs before the U5 freeze, not before the native kernel. For a
  closed-form max/sum engine whose arithmetic is already pinned by literal tests, an elaborate
  new property-profile revision (such as C1's 24-anchor campaign) adds little. Disclosing what
  remains `not_run` is enough unless a U5 prediction depends on it. This proportionality point
  is a judgment call, not a defect.
- **Correction.** G2 means native design acceptance. Analytic completion moves to G3a,
  limited to the cases U-C0 predictions rely on.
- **Human decision:** yes (G2 text).

### PF-11 · Medium · R — rk-sim integration risks are found late, though a cheap early check exists

- **Evidence.**
  - rk-sim timing: P18/P19 are post-S12 (`rk-sim-side/prompts/P18-…:1`). rk-sim is in S6,
    with S7–S12 not started (`rk-sim/docs/execution-plan.md:9-20`). Its §1.3 excludes C1+ and
    memoization surrogates (DRAFT:22-23). So earlier integration on the rk-sim side would
    require rk-sim to replan.
  - The vendored snapshot already includes `rk/engine/f0/compute.py`. `IterationCost` keys
    prefill on (total prompt tokens, Σ squared tokens) and carries DVFS, spill/HBM-KV and
    power-point hooks. Table rows allow null `vector_ops` and `memory_write_bytes`
    (`contract/uarch_contract/table.py:63-66`), while rule 5 forbids null conversion.
  - P18's test 2 proves only rk-sim's own plumbing, using a table generated from C0.
- **Correction.** Add a test-only consumer-conformance check in rk-uarch, which invariant 1
  permits:
  - Feed a real uarch table (U2 analytic tables today) through the nine rules and an
    `IterationCost`-equivalent reader built on the vendored snapshot.
  - Produce `interpolation_vectors.json` from a U-C0 grid when the pipeline exists.
  - This makes no fidelity claim and does not change rk-sim.
- **Human decision:** none; this is routine (B or A tests).

### PF-12 · Medium · R — The compute-1 law is tested only against itself until silicon

- **Evidence.**
  - A's law (`verification.md:42-57`): no weight retention across jobs; staging is
    serialized; 255 fill and 255 drain cycles per 256×256 wave.
  - B derives its expectations from that same convention (`native-checklist.md:17`).
  - SCALE-Sim is optional, and A says it may be unmatched (`delivery.md:187`).
- **Scenario.** For decode with m ≤ 32, roughly 510 fill/drain cycles plus 128 staging cycles
  dominate each tile. If real weight-stationary arrays overlap these, every decode row is
  biased, and the full grid would be built on that bias.
- **Assessment.** The verification design itself is correct: it is a verified convention
  that makes no accuracy claim. The concern is sequencing.
- **Correction.** PF-01's earlier silicon. Optionally, admit a prospective SCALE-Sim scope for
  the isolated pipeline law. Never tune toward it.
- **Human decision:** none beyond PF-01.

### PF-13 · Low-Medium · M — Several prompts mix phases or hold stale literals

- **U-P7 and U-P11b each carry both U4a and U4b.** U-P7 says its "full acceptance belongs to
  U4b" (`build-spec.md:2413-2417`), and its 13 acceptance tests are U4b's. A literal M-phase
  worker therefore has no M acceptance list; A's interface supplies one, but it is
  unaccepted. U-P11b says "All acceptance below is required for the full stage"
  (`:2889-2890`).
- **U-P11a reads an rk-sim vision document without naming a section.** It loads rk-sim's
  `docs/vision/elements_of_parallel_DES.md` (`:2763-2765`), but `CLAUDE.md` permits that only
  when a prompt names a section.
- **Correction.** Write phase-specific prompt blocks (U-P7a/b, U-P11b-bounded) when U0011 is
  accepted. Name the sections U-P11a may read.
- **Human decision:** none; these are routine prompt edits once the decisions exist.

### PF-14 · Low-Medium · W — U7 builds full tables where representative points serve

- **Evidence.**
  - U-P13d builds full 16×16 and 32×32 tables (`build-spec.md:3215-3216,3228`). The 32×32
    spec does not exist, per A (`delivery.md:160-162`).
  - The 32×32 table's only consumer is U9's single-point wall-clock trigger
    (`execution-plan.md:287`).
  - U-P14 builds a full table for each study variant (`build-spec.md:3257-3259`), although
    studies name their operating points.
- **Correction.** Use prospectively declared representative points for scale evidence and
  evaluate studies at suite points. Build full grids only for the table artifact that is
  consumed (demo or rk-sim).
- **Human decision:** none; this can be settled when U7's prompts are revised.

## 4. Deliverable, consumer and dependency matrix

Abbreviations:

- **R:** reusable implementation.
- **D:** disposable generated data, superseded by later engine versions.

| # | Deliverable (producer) | First consumer | Needed by | Risk retired | True prerequisites | R/D | If reduced, postponed or removed |
|---|---|---|---|---|---|---|---|
| 1 | Mapped carriers M, component and fixture scopes (A, human install) | K2 wiring; B corpus | Before K2 | Rust/Python drift; identity | U0011 and schema decision | R | K2/B blocked; K1 is not |
| 2 | Kernel K (A) | B models | Before B | Clock, order and determinism bugs | Toolchain pin (K2 also needs M) | R | Nothing downstream runs |
| 3 | Bounded models B (A) | Decoder coverage; U5 matrix/memory classes | G3a | DMA, DRAM-0 and interval mechanics | K; B corpus | R | — |
| 4 | Literal corpus, faults, two human L1 fixtures (B, humans) | K/B acceptance | With K/B | Self-confirming tests | Accepted E1–E4 conventions | R | Correctly blocks B |
| 5 | Analytic U-P6 remainder, C1–C5 (B) | U-C0 predictions in U5; roofline floor | U5 freeze | U-C0 baseline errors | None | R | Disclose not_run; does not block K/B |
| 6 | Decoder coverage: mapped v2 RoPE, fused paged attention, vector ops, kv_write, steady priming, head/tail (A) | U5 operator and end-to-end classes | U5 freeze | Workload completeness | B | R | U5 limited to microbenchmarks |
| 7 | TPU v5e reference and native admission, int8 if declared (B+A) | U5 | U5 freeze | Unknown count; representability | Sourcing; maybe a contract extension | R | U5 impossible (PF-03) |
| 8 | Attribution qualification (A/B) | G4 fail branch; U-P14 diffs | U5 freeze | Misattributed silicon error | B | R | Fail-branch target unreliable |
| 9 | `check_ordering`, prediction schema, ledger (B) | U5 | U5 freeze | Ordering and contamination | None | R | — |
| 10 | Table pipeline: grid/pool/interpolation/errors, contract 0.4, interpolation vectors (A) | rk-sim P18; U-P14; demo | Before the first consumed table | Interpolation and contract mismatch | U-C0 is enough to build and test it | R | Later integration risk; #16 mitigates |
| 11 | Full npu-l4 672-point C1 table and errors (A) | **G3 only** | None found | Scale and determinism (smaller runs also do this) | #6, #10, FP8/os-tiled/ragged decisions, hardware revision | **D** | No consumer loses anything |
| 12 | FP8 semantics, ragged extension, npu-l4 output-stationary/FP8 revision (humans) | npu-m256 fp8 rows; composition error; dataflow study | G3b / U7 | Semantic gaps | U0022 amendment; U0002 cycle | R | Safe to defer to the consumer |
| 13 | Diagnostics and traces (A) | U-P10 diagnostic fidelity; U-P14; reports | U7 (partly U5) | null→0 errors | B | R | Diagnostics stay null, which is honest |
| 14 | Host cost and regression gate (designated host) | U9 entry; CI regression | Before the U9 decision | Unbounded simulator cost | Host allocation; runner | R | U9 decision uninformed |
| 15 | Full npu-m256 C1/NoC-0 table (U6) | **G5 only** | None | Mesh admission, achievable at points | #10 | **D** | Replace with representative points |
| 16 | Consumer-conformance test against the vendored `IterationCost` (tests) | Contract 0.4; U10 | Now | Late integration surprises | Snapshot (exists) | R | Gaps found at U10 |
| 17 | NoC 1+ts, DRAM 1/2 with Ramulator, compute 2 (U7) | G6; U8 per-level predictions; U10 | U7 | Contention mechanisms | Core engine | R | Composite stays C1 |
| 18 | npu-m256 C2 table with measured errors (U7) | Demo; U10; studies | U7 / U10 | Product | #10, #12, #17 | Product data | No product |
| 19 | 32×32 full table (U7) | U9 single-point trigger | U7 | Scale | A 32×32 spec (absent) | D | Points suffice |
| 20 | U-P14 studies (B) | Architects; demo | U7 | Product use | #18 | R | — |
| 21 | Blackhole reference, admission and kit (A/B) | G7 | U8 | Mesh accuracy; whether detail helped | Purchase; admission | R | — |
| 22 | U9 parallel engine and sync experiment | Measured need, or the funded plan's G1 | Conditional | Speed; the sync bet | #14 or an ADR | R | Already conditional |
| 23 | P18/P19 in rk-sim | rk-sim users; demo | After rk-sim S12 | Integration | Boundary ADR; G6 | R | uarch stays standalone |
| 24 | Self-hosted runner and nightly | Performance evidence; long suites | G5 performance / U9 | Uncontrolled performance numbers | Host allocation | R | Performance stays pending |
| 25 | U0002 adoption cycles | Nominal-parity currentness | Every bound edit (today) | Oracle drift | Human time | Process | See PF-05 |

## 5. Proposed minimal revised sequence

| Stage | Action | Change | Reason |
|---|---|---|---|
| U3 | **Keep** | A's M → K → B scope, conventions and verification matrix; install only the admitted component and kernel-fixture scopes. Design the prepared-model scope but do not install it yet | Avoid speculative protected fields |
| U3 | **Move** | Analytic U-P6 completion moves out of G2, into G3a | PF-10 |
| U3 | **Add** | TPU v5e sourcing (B); representability note (A+B); decisions J1–J7 | PF-03 |
| U4a | **Change** | K1 (kernel internals) after the toolchain pin, on hosted CI; K2 after M; then B | PF-06, PF-07 |
| U4b | **Replace** | Full table → **G3a, silicon readiness** (contents below) | PF-01, PF-03, PF-08 |
| U4b | **Remove as a gate** | The 672-point npu-l4 FP8/BF16 × two-policy table, LOO, composition, frequency axis and os-tiled | PF-01, PF-02 |
| Any time | **Add** | Consumer-conformance test on U2 analytic tables | PF-11 |
| U5 | **Keep; re-gate** | G4 method and thresholds unchanged; depends on G3a plus hardware/budget authorization | — |
| U6 | **Reduce** | Delta qualification, diagnostics, designated-host cost and regression gate, mesh admission at points; no full C1 mesh table | PF-09 |
| U6/U7 | **Move** | Table pipeline, contract 0.4, interpolation vectors, FP8 and ragged decisions → **G3b, first consumed table** | PF-01, PF-02 |
| U7 | **Keep + G3b** | Depth (G6); full npu-m256 table at its earned composite with all measured errors and no silent drops | Its consumers are real |
| U7 | **Reduce** | 32×32 and per-variant study tables become representative or suite points | PF-14 |
| U8 | **Add** | Explicit Blackhole admission task before the U-P15 freeze | Same gap as PF-03 |
| U9, U11 | **Keep** | Unchanged | Entry conditions are justified |
| U10 | **Move dependency** | G6 plus G3b; P18 refuses non-C2 | PF-04 |

G3a contents:

- Decoder-layer coverage on npu-l4 BF16 and the accepted TPU v5e reference.
- Steady priming, with priming 1 vs 2 checked at benchmark points.
- Literal corpus, faults, applicable L0/L0m/L1, complete-work counts.
- Mapped replay and debug/release determinism.
- Attribution qualification.
- The U-C0 checks that U5 predictions rely on.
- Frozen-prediction infrastructure.
- Unsupported required benchmark work blocks G3a, exactly as G3 blocks today.

**Why not broader replanning.** A broad replan would mean, for example, integrating with rk-sim
first or turning every sprint into capability milestones. It would cost another full
human-install cycle and still leave the next 148–240 h (A's M + K + B range) unchanged.
The defects are concentrated in one gate definition, one stale dependency, U6's overlap, and
two operational rules, so the minimal amendment is sufficient. Revisit U7–U11 after U5
produces the first accuracy signal.

**What this costs.**

- **Pros:** The first accuracy signal comes before the largest investment.
- **Cons:**
  - FP8 and composition semantics are settled later, so the team learns about them later.
  - The table pipeline's first full-scale run moves to U7, so table-scale failures surface
    later. #16 and representative-point runs reduce, but do not remove, that risk.

## 6. Disposition of the intermediate-table and runner questions

**Intermediate tables.** First I checked the actual uses:

- U5 and U8 use benchmark predictions, not tables.
- U-P14 studies, the demo and U10 do use tables, but only from U7 onward.
- The method-error experiments inform simulation choices. Only steady priming matters for U5
  (benchmarks are steady); layer reuse does not apply to single-layer benchmarks.

Disposition:

- **Keep.** The table pipeline as reusable code, and every honesty rule: measured errors,
  refusing extrapolation, no silent drops.
- **Reduce.** Before silicon, use small, prospectively declared fixture sets for counts,
  replay and determinism. These are test fixtures, not product tables.
- **Remove as gates.** The full npu-l4 C1 table and the U6 full C1 mesh table. Both move to
  their first consumers (npu-m256 at U7/U10; npu-l4 for the U-P14 studies).
- **Coordinator's hypotheses.**
  - *Fixtures for infrastructure* and *direct engine results for early verification*: agree.
    A's B stage already is the second one.
  - *Earlier rk-sim integration with experimental tables*: not recommended. It needs rk-sim
    to replan and conflicts with rk-sim's §1.3. PF-11's test-only check retires most of the
    risk in rk-uarch alone.
  - *Broader generation only when needed*: agree. That is G3b.

**Runner.** Correctness work does not need controlled hardware. Performance claims, long runs
and U9 scaling do. Recommended amendment:

1. Native implementation and correctness run on hosted CI with a pinned toolchain. The
   `ci.yml` native job already exists.
2. Every performance claim needs the designated host with receipts (U0011/U0012, G5
   performance, U9). WSL is never a performance host.
3. The self-hosted nightly must exist before G5 and before any suite that exceeds hosted
   limits.
4. A standing cold-clone rule replaces the per-sprint exception ADRs.
5. The published requirement stays operative until Javid amends it.

## 7. Decisions for Javid, and routine choices

**Javid decides:**

- **J1.** Split G3 into G3a and G3b; or keep G3 and decide FP8 semantics, the ragged
  extension and the npu-l4 revision now (PF-01, PF-02).
- **J2.** The runner amendment (PF-06).
- **J3.** U0002 inventory: narrow the binding, switch to regenerate-and-compare, or budget
  adoption windows (PF-05).
- **J4.** With Reza for rk-sim: U10 depends on G6, and P18 checks the composite (PF-04).
- **J5.** Commission U5 readiness: TPU sourcing, native admission and any contract
  extension (PF-03). Also decide whether an early silicon pilot is allowed. I recommend
  against one: its results would be seen before the G4 freeze on the same chip, which
  undermines G4's independence.
- **J6.** Split K into K1/K2, amending U0005's stated order (PF-07).
- **J7.** U6 scope and where the mesh table goes (PF-09); G2 scope (PF-10).
- **A's open items 1–5.** Recommend acceptance. Item 2 (the interface) should install only
  the admitted scopes. T's estimate and budget rows should be redone under J1.

**Routine (lanes and coordinator):**

- Phase-split prompt text (PF-13).
- Choosing representative points, declared prospectively.
- Design of the conformance test.
- `check_ordering`.
- Which C1–C5 cases U-C0 predictions actually need.
- README and status updates after the decisions.

## 8. Next useful tasks under this recommendation

None of these is authorized by this report.

**A:**

1. An installable M patch limited to the component and kernel-fixture scopes.
2. A toolchain and licence pin manifest proposal (exact Rust release and checksums,
   `Cargo.lock`, transitive licences). This is K1's real prerequisite.
3. With B: a TPU v5e representability note (what HardwareSpec and native admission require).

**B:**

1. Freeze the K/B literal corpus and its faults, reconciled with A's E1–E4. Schedule the two
   human-worked L1 fixtures (latency-bound DMA, resident GEMM).
2. TPU v5e sourcing inventory: sourced claims, counted stubs, open unknowns. No measurement
   and no spend.
3. Design the consumer-conformance test (U2 table plus vendored `IterationCost`, test-only).
4. Pause the C1–C5 profile revisions pending J7; record what remains `not_run`.

## 9. Uncertainties, limits and checks performed

**Uncertainties and limits.**

- Effort figures are A's unaccepted ranges. I made no new estimates.
- Compute figures are A's ceilings, not observations.
- No actual hours exist (`execution-plan.md:87-88`). Process cost is evidenced only by
  artifacts: `docs/reviews` holds 852 files (21.6 MB), against 27,462 lines of src and
  contract Python and 17,940 lines of tests and validation.
- I did not trace the generator's import closure, and I did not check TPU v5e
  representability against vendor documents.
- The rk-sim remote may be ahead of the local checkout.
- I did not check hosted CI minutes or budget for the private repository.

**Checks I executed:**

- `git rev-parse`, `status`, `log`, a dry-run `fetch`, `blame` on `execution-plan.md:300`,
  and `show` of the pre-amendment text at `7fbb0f3`.
- `uv run --offline pytest -q tests/unit/test_prompt_sync.py`: 4 passed. `uv` rebuilt the
  editable rk-uarch install in the existing `.venv`; no dependencies changed.
- **Probe.** In a private `git archive` export of `afb3502` in session scratch space,
  `scripts/vendor_rk.py --check` passed. After adding an empty
  `src/rkuarch/mapping/probe_policy.py`, it failed with
  `vendor-rk: input support inventory changed`. The export was deleted afterwards.
- Counts:
  - TPU draft leaves: 46 stub, 4 sourced.
  - Review documentation: 852 files, 21.6 MB.
  - Python line totals as above.
  - Arithmetic: 672 × 60 s = 11.2 h; 168 × 60 s = 2.8 h.
- Read-only rk-sim checks: `CLAUDE.md`, the execution-plan STATUS, `compute.py`, and a diff
  since pin `1e5706e`. The local checkout shows no changes to `rk/engine/f0/compute.py` or
  `rk/schema/`.
- One primary-source fetch: the GitHub Actions job limits.

**Not run or not done:**

- The full suite, mypy or ruff.
- Native builds or containers.
- Any server, runner or oracle generation.
- Reading rk-sim `docs/vision/`.

Inherited receipts (such as 1,701 passed / 29 skipped) were not rerun.

## Handoff for the coordinator

```text
U3 post-fork plan review v1 — docs/reviews/U3-post-fork-plan-review-v1/README.md
Reviewed afb3502 (tree b3dd42e), clean. Recommendation only; nothing installed or accepted.
Verdict: sound architecture; schedule needs bounded amendments before U4b/U5 planning.
High: PF-01 full npu-l4 table gates U5 but U5 uses none of it -> split G3 into G3a
(silicon readiness) and G3b (first consumed table, U7/U10). PF-02 G3 unsatisfiable on
accepted npu-l4 (WS/BF16 only) and U0022 (no FP8/ragged). PF-03 U5 prerequisites
unscheduled: no usable TPU v5e reference, no native admission, U-P9 forbids engine change.
PF-04 U10 "G3 at minimum" feeds a C1 table to a C2-only reader that never checks composite
-> depend on G6 + P18 refusal. PF-05 U0002 support inventory binds every src/contract/
scripts .py (probe: new empty module fails vendor --check in hosted CI) -> narrow or
regenerate-and-compare. Medium: PF-06 runner gates only performance/long runs, not
correctness; PF-07 split K1/K2; PF-08 qualify attribution before U5; PF-09 shrink U6;
PF-10 move analytic U-P6 out of G2; PF-11 test-only rk-sim conformance check now;
PF-12 interval law needs earlier silicon. Javid decisions J1–J7 in §7; next A/B tasks §8.
```
