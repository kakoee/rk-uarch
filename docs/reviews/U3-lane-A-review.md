# U3 Lane A — independent adversarial review

## Stage 1 review — 2026-10-12 — target `184d2c2b08c28a01673be143b086ef223ba6706a`

Tree `6f74542bf5fc85997e044a135293db95297e3e20` (verified with `git rev-parse`). Later
coordinator review-only commits (`606d247`, `d7b00b8`) do not change this target.
Evidence: [U3-independent-review-A-v1/](U3-independent-review-A-v1/README.md); exact
outputs are in its `run_all.log` (timestamps there are UTC, 2026-10-13T04:52Z).

This is a bounded Stage 1 design/readiness/prototype review under U-REVIEW. It is not a
sprint exit, G2 acceptance, implementation release, human approval or Stage 3
adjudication. Findings are evidence for author response; Javid makes the decisions.

### Reviewer independence

This session wrote none of the reviewed files and has no memory of earlier sessions.
Git attributes the reviewed commits to `jjaffari`; the authoring sessions cannot be
identified from Git. The reviewer is a Claude model. If the author sessions were also
Claude-based, that is shared model lineage, not authorship by this session. This session
is not the Lane B reviewer and did not open the other reviewer's untracked
`docs/reviews/U3-independent-review-B-v1/`. No subagents were used.

### Scope read

- Current `CLAUDE.md`; accepted U0005, U0006, U0019, U0022, U0023; execution-plan STATUS,
  U3–U10 and G2/G3a/G3b/G4/G5/G6; build-spec §2.4–§2.8; U-P5, U-P7, U-P8, U-P11a, U-P11b,
  U-P11c, U-P12 and U-REVIEW in full; U-P6 lines 14-80 (phasing, L0/L0m lists, native
  application).
- At the target: all eight files of `U3-native-stage-design-v2/`; B's
  `U3-B-verification-readiness-v1/` (README integration section, checklist, worked
  examples), `U3-B-readiness-supplement-v1/` (both files), `U3-B-artifact-dependency-audit-v1/`
  (README, migration, support delta; `repair.patch` identity and data globs only),
  `U3-B-dependency-audit-correction-v1/README.md`, and
  `U3-design-audit-reconciliation-v1/README.md` as claims to verify.
- Existing code relevant to the M note: `scripts/u2_inputs.py`, `src/rkuarch/hw/{export,derive}.py`,
  `src/rkuarch/engines/protocol.py`, all four initializers, `contract/uarch_contract/{__init__,hashing,
  operators,prepared,rotary_v2,table,common,hardware,precision}.py`, `hw/designs/npu-l4.yaml`,
  `native/`, `third_party/LICENSES.md`, `.github/workflows/ci.yml`.

### Summary

The package is well bounded and matches the accepted direction. It keeps one Rust engine
and the analytic baseline, adds no full fork, second Python engine or early full-grid
gate, keeps full tables in U7 and leaves U10 as integration. Every literal number in E1–E5
that I re-derived matches. The claimed npu-l4 identity matches. The literal C1 OpSpec and
PreparedOp validate against the live carriers. The proposed-M dependency note agrees with
the real import chain, the initializers and B's audited support sets. The A-C1 correction
appears in every affected attachment and summary, and I found no dependency cycle.

Two items block exact acceptance of specific clauses: the admission semantics for the
synthetic test profile (A-F1) and the time conversions in the E4 law (A-F2). Eight
non-blocking findings concern under-specified fixtures, carrier semantics, a delivery
inconsistency, estimates, a U9 pointer and observation volume.

## Findings

Severity means: **BLOCKING** = must be corrected before Javid can accept the named
clause exactly as part of this proposal decision. **NON-BLOCKING** = a correction or
clarification that can be resolved in the author response or at the explicitly
deferred exit named in the finding.

### A-F1 — BLOCKING — Test-profile/fixture admission is undefined; several required B checks have no admissible public path

**Where.** `proposed-U0011.md:43-46` (B admits only the npu-l4 hash at frequency ratio 1);
`interface.md:26` (B admits `component` only; K2 admits `kernel_fixture` only, which carries
fixed delays only), `:28` (`fixture_resident` "only with test admission"), `:45-46`
(`--fixture-mode` "and scope binding"), `:286-288` (R17/R18 refuse other fidelity and any
other production hardware hash), `:293-294` ("Synthetic clock/credit/capacity cases use an
explicit test profile with sourced synthetic assumptions"); `verification.md:91-92`,
`:134-140`, `:143-146`, `:197` (V08), `:202` (V13), `:206` (V17), `:252` ("caps 1/2/32"),
`:293` (native clock relation "under its explicit synthetic test profile"). The governing
prompts require the same: U-P6:56-58 and :74-76 (L0m as property tests over generated
HardwareSpecs, run through the native public protocol at U4a), and U-P11b:64-65.

**Defect.** Required B checks execute compute/DMA jobs on parameters other than
npu-l4's at ratio 1:

- the one-outstanding-credit variant (120000 ps) and caps 1/2 (V08);
- U-P11b acceptance 4, which lowers `max_outstanding`;
- the two-credit, large-latency stream (V13);
- the BW/latency/credit monotonicity relations (V17);
- the half-size-accumulator refusal (E3);
- the isolated E3 clock relation, which needs a different `freq_hz` or ratio.

As written, B refuses all of these. R17/R18 and the npu-l4-only admission reject them,
and `kernel_fixture` cannot carry compute/DMA work (K2 "refuses subsystem compute/DMA
jobs"). The only enabling text is a phrase about an "explicit test profile", a CLI flag
and a note that variants are "proposed under B-owned hw/designs/ … and refuse under B's
production hardware hash". None of it defines:

- which invocation modes and scopes admit which hardware, initial states or frequency
  ratios;
- how a variant is marked test-only in job/result identity. A `component` result on
  synthetic hardware is distinguishable only by its hash;
- whether `kernel_fixture` stays admitted as a regression after K2;
- how variants placed in `hw/designs/` (where invariant 2 puts every stipulation, as
  `design_status: proposed`) are kept out of `prepare`/`table` as if they were
  candidate designs.

"Sourced synthetic assumptions" also conflicts with invariant 2: invented values are
stipulations with rationales, not sourced claims.

**Consequence.** Accepting R17/R18 together with V08/V13/V17 is either contradictory or
leaves the admission path to implementers. M cannot construct the fixtures or admission
tests for these cases. Without a defined path the B checks reduce to not_run and block
B acceptance. An ad hoc path could quietly widen production admission.

**Evidence.** Cited text. `run_all.log` (`HW-FIELDS`): npu-l4 has 1 GHz in every domain
and `max_outstanding=32`. `hw/designs/` holds only npu-l4 and npu-m256; none of the
required variants exists.

**Minimal correction.** Add one admission matrix to `interface.md`/U0011:
checkpoint × invocation mode × scope × initial_state × hardware identity × frequency
ratio. Define the test-profile binding: an explicit list of admitted variant hashes
(each a `design_status: proposed` spec with stipulation rationales and an owner), a
result/scope marker that makes such results ineligible for tables and reports, and
refusal of variants by `prepare`/`table`. State whether `kernel_fixture` remains admitted
after B. **Owner:** A for the admission and carrier semantics; B for the variant specs and
the list of checks that need them (shared boundary). **Blocks:** acceptance of the
schema plan, the refusal catalogue and the B verification matrix (G2 "human-approved
mapped schema plan", decisions 1–2). It does not block K1.

### A-F2 — BLOCKING — The E4 law's time conversions and rounding are not exact; the worked example converts cycles to ps outside `next_edge`

**Where.** `verification.md:113-114` ("round each completion edge up once"), `:118-121`
(read lifecycle), `:129-131` ("response arrives 58250; core edge=59000"), `:151`;
`proposed-U0011.md:58-60`, `:101-102` ("next_edge is the sole cycle conversion");
observation semantics `interface.md:252-256`.

**Defect.** The worked read adds the two-hop response delay (4 NoC cycles) as a fixed
4000 ps starting at the non-edge time 54250, giving 58250, and only then aligns to a core
edge. Build-spec §2.8 (`docs/build-spec.md:688-690`) and invariant 3 make `next_edge` the
only time↔cycle conversion. A 4-cycle NoC delay starting at 54250 is
`next_edge(noc, 54250, 4) = 59000`. The request leg starts at t=0, which hides the
difference. The text also leaves open whether the channel completion is ceil-to-ps (54250)
or aligned to a DRAM edge (55000). No critical-path category is defined for
edge-alignment waits.

**Consequence.** At 1 GHz the three readings agree on the final 60000/62000 ps but record
different timestamps in the mandatory observations:

- channel-service `leave_ps` is 54250 or 55000;
- the core-port waiting interval [58250, 59000) exists in one reading and not the other;
- the critical-path partition differs.

Under a synthetic NoC clock (1.2 GHz, E2's own frequency) the final completion differs:
59000 versus 60000. So B cannot write exact independent expectations for V14, V21 and
V23–V24, the required human latency-bound hand fixture cannot be worked exactly, and two
conforming implementations would emit different canonical bytes.

**Evidence.** `run_all.log`: `E4-READ-1GHZ` (three readings), `E4-READ-NOC1.2GHZ`.

**Minimal correction.** State each lifecycle leg as a named-domain `next_edge`, for
example hop arrival = `next_edge(noc, t, 2h)`. If a fixed-ps hop is intended instead,
justify it as an explicit exception for human decision. Fix the rounding of channel
completion and the critical-path category of alignment waits. Publish the full
timestamp/observation table for the two-hop read, the two-read case and one write.
**Owner:** A for the law; B for the independent expectations. **Blocks:** acceptance of the
E4 law (decision 1) and the human latency-bound fixture. It does not block K1.

### A-F3 — NON-BLOCKING — E4 fixtures rely on unstated assumptions and some stated faults are masked

**Where.** `verification.md:108-116`, `:124`, `:132-138`, `:202` (V13);
`hw/designs/npu-l4.yaml:61-62`.

1. **Request issue rate.** Two reads "issued at 0" from one engine, and reads using no
   core port at issue, imply unlimited request issue per DMA engine per cycle. The 62000 ps
   answer and the latency-bound bound depend on this; state it as a law.
2. **33-request fixture placement.** "Request 33 cannot issue before the first completion
   at 60000 ps" holds only if every request targets channel 6 or 7 from core 0. Under the
   same law, channels 0–1 complete first at 52000 and channels 2–5 at 56000
   (`E4-FIRST-COMPLETION-BY-CHANNEL`). Specify the core and addresses.
3. **Refresh-omission fault is masked.** Omitting refresh derating leaves the 60000/62000
   fixtures unchanged. The first same-channel request that discriminates is the 5th
   (69000 vs 68000; `FAULT-E4-NO-REFRESH-*`). V13's frozen fixture needs at least 5
   same-channel requests or channel-level timestamp assertions.
4. **Job overhead on DMA/NoC/barrier jobs.** Whether these pay `job_overhead_cycles`
   (spec rationale: "core-domain job issue overhead") is unstated; E3 charges it only to
   compute.

**Owner:** A for the laws, B for the fixture freeze. **Deferred to:** the B corpus freeze.

### A-F4 — NON-BLOCKING — The zero-delay convention does not state owner arbitration for owned zero-duration jobs

**Where.** `interface.md:80-81` (`fixed_delay` carries owner/resource), `:85-91`,
`:276-282`; `proposed-U0011.md:109-112`; `verification.md:269-270` (V26).

**Defect.** Zero-duration milestones complete "inline … during readiness processing" with
"no exclusive service interval". The text does not say whether a zero-duration job whose
owner is busy bypasses the owner's FIFO grant. Example: owner0 is busy over [0, 3000);
z (0 ps, owner0) becomes ready at 1000 after p (1000 ps, owner1); c (2000 ps, owner1)
follows z. The makespan is 3000 if z completes inline and 5000 if it waits for owner0
(`ZERO-DELAY-OWNED`). V26's literal (two milestones, then 3000 ps) does not distinguish
these. The text also does not say whether a same-core zero-hop `noc_transfer` (0 ps, no
bandwidth) is admitted.

**Correction.** Add one sentence plus this discriminating literal and its fault. Settle it
inside the K1 semantics decision. **Owner:** A.

### A-F5 — NON-BLOCKING — Count, operator-version and validation-order semantics that M's schema needs

**Where.** `interface.md:26`, `:31`, `:147-155`, `:169-171`, `:178`; `verification.md:79-80`.

1. **Operator version.** The PreparedOp version for `component` scope (v1 or
   `PreparedOpV2`) is unstated. Under v1, R06's `rotary_embedding` mutation is a pydantic
   schema refusal, not `UnsupportedOperator` (`R06-ROTARY-V1 schema-refusal`).
2. **Count carriers.** The resident projection puts `issued_matrix_ops` in `ext_counts`.
   The existing `ExtCounts` (`extra="forbid"`) refuses it and also requires
   `noc_flit_hop_count` (`PROJECTION ext_counts refused`). The proposal does not say
   whether native reuses `Counts`/`ExtCounts` or adds new carriers. It also does not say
   whether `counts.memory_read/write_bytes` carry payload or transaction bytes (C2:
   100/42 vs 512/256). That choice affects same-work floor joins and any later rows.
3. **Validation order.** R13's coefficients-hash tamper can only be built on a v2 model,
   which R02/R03 refuse unless closure checks run before scope admission. State the order.

**Owner:** A, with the human carrier owners. **Deferred to:** the exact M patch, but decide
these in the schema plan.

### A-F6 — NON-BLOCKING — Hardware ledger and identity-relevant enumerations are incomplete

**Where.** `interface.md:33-39`, `:48-58`, `:85-89`, `:110-124`.

1. **Unclassified leaves.** 4 of 59 npu-l4 SourcedValue leaves are neither used by a
   stated law nor listed as unrepresented: `matrix_engine.macs_per_cycle.bf16`,
   `operand_buffer_bytes`, `memory.dram.capacity_bytes` and
   `formats.bf16.block_scale_bytes` (`UNCLASSIFIED`). The exact `unrepresented` list is
   therefore not derivable. For example, operand-buffer capacity is neither validated nor
   declared unrepresented.
2. **Bank rule.** "Banks are validated coordinates" has no rule: is bank = offset ÷ bank
   size, and may a buffer span banks? C1 puts every buffer, including slot 1, in bank 0.
3. **Owner enumeration.** "Owner IDs are a canonical resource enumeration" is undefined,
   yet the `events` section, which is part of result identity, orders by target.

**Correction.** Classify every leaf, define the bank rule and define the owner
enumeration. **Owner:** A.

### A-F7 — NON-BLOCKING — K2's prerequisites disagree between delivery and U0011

**Where.** `delivery.md:9` (K2 requires "M fixtures/mapper/import") against
`proposed-U0011.md:25-26`, U-P11a K2 (lines 24-25) and U0023 item 2 (installed carriers
and M fixtures). K2 admits only `kernel_fixture` (`interface.md:26`), so the component
mapper/import is first consumed by B, not K2. The extra prerequisite serializes K2 behind
the mapper, or leaves the gate ambiguous. **Correction.** Align the delivery table.
**Owner:** A.

### A-F8 — NON-BLOCKING — TPU-independent decoder/complete-work expansion has no estimate

**Where.** `delivery.md:12`, `:14-17`, `:100-108`; U-P7 lines 37-40 ("TPU-specific R
completion is neither sufficient nor required for this product scope").

T estimates "only product-specific remaining expansion, never rebuilt kernel/shared
operators", while RoPE/casts/KV/fused-attention/full-layer support is costed only inside
R (120–200 h). If TPU sourcing stalls R, U-P7 T must build that support itself, and no
recorded estimate covers it. The U6 "representative input scope" is likewise unstated.
**Correction.** Give a conditional T estimate for the case where R has not delivered, or a
separate TPU-independent shared-operator package with owner and estimate. Name the U6
representative inputs. **Owner:** A, with the coordinator.

### A-F9 — NON-BLOCKING — The U9 entry trigger points at a budget the proposal withdraws

**Where.** `docs/execution-plan.md:292` (U9 needs "ADR U0011's single-point wall-clock budget
(measured in U-P11c and U-P13d)") and U-P11c:32-34 ("the prospectively declared U0011
workload … feeds the existing U9 admission decision"), against `proposed-U0011.md:167-173`
and `delivery.md:182-185`. The proposed U0011 keeps only the K2/B envelope, withdraws the
later budgets and never names the decision that will supply U9's trigger.
**Correction.** State that the U6/U7 budget decision supplies the trigger, or propose the
plan-pointer change through the normal process. **Owner:** A.

### A-F10 — NON-BLOCKING — Mandatory observation volume is not reconciled with the 5 s / 512 MiB envelope

**Where.** `interface.md:240-256`; `proposed-U0011.md:81-90`, `:167-170`; `delivery.md:168-176`.

At B's largest admitted input (16 ops, M=1024, K=N=256, 4 cores) there are at least
98,304 DMA requests. Counting only one `dma`, one `transfers` and two `queue_membership`
records per request gives at least 393,216 records, about 80 MiB of canonical JSON. That
excludes events, jobs, allocations, intervals and the critical path (`probe_volume`). The
records are part of result identity, and the envelope's all-in invocation includes
parsing and validation. The envelope may therefore be infeasible by construction. This is
a reviewer estimate, not a measurement, and not a WSL performance claim.
**Correction.** State observation volume bounds and either size the B envelope from them,
narrow the envelope to declared fixture sizes, or define a separately hashed observation
artifact. **Owner:** A, with B as performance-gate owner.

## Primary checks

### 1. Scope, prerequisites, first consumers, cycles

- **Consistent with the authorities.** Scope and refusals match U0023 and U-P5:
  compute 1 / NoC 0 / DRAM 0, exact sync, C1 at most; a GEMM-only stage is not a decoder
  claim; R serves the actual U5 suite; T is the first full table in U7; U10 needs G6, G3b
  and the rk-sim boundary.
- **No dependency cycle.** I checked `M ∥ K1 → K2 → B → R → G3a → U-P9 → U-P10` and
  `B → U6 (G5-correctness) → U7 (G6 + T/G3b) → U10` against execution-plan U4–U10
  "Depends on". U6 does not need R or G4. T needs neither R, G4/G7 nor G5-performance or
  automation. U5 has no dependency on U6.
- **Ownership.** Every task names a first consumer and an owner, with the gaps noted in
  A-F1 (test-variant semantics), A-F7 (K2 versus mapper) and A-F8 (TPU-independent
  operators). The two human L1 fixtures remain an assignment to be made (decision 5).
- **No unsupported claims.** The npu-l4 identity is verified (`NPU-L4-HASH … MATCH`).
  `hw/references/tpu-v5e.yaml` is absent, as `delivery.md:23` says. G2 stays pending
  throughout.

### 2. Independent re-derivations (laws treated as proposed assumptions)

All of these match A's text (`run_all.log`, `probe_arithmetic`):

- **E1.** Tie order is seq 7,8,9,2. Makespan is 7000; serialized on one owner 10000;
  without the dependency 5000.
- **E2.** Edges 0/834/1667/2500/3334. `next_edge` cases 2500/834/1667/2500/833333333334.
  The rounded-period error is 333333334. The E2 integer first-edge formula agrees with the
  search definition on 200,000 random cases plus 15,000 boundary cases (0 mismatches). The
  V04 invariant holds. Fault controls: a rounded period and a floored edge are both detected.
- **E3.** C1: 702 cycles (136+526+8+32), 2,097,152 ops, 139264/8192 SRAM bytes,
  544/32 cold requests, slots 147456/294912.
- **E3, C2 and C3.** C2: 547 cycles, 210 useful versus 393216 issued, 100/42 bytes.
  C3: 1182/673 cycles, makespan 1,182,000 ps, 1,855,000 ps on one core;
  33,685,504 ops; 393728/131584 bytes. Fault controls: dropping the overhead and counting
  padded lanes as useful are both detected.
- **E4.** Channel cap 4437500000000/39 B/s and service 159744/71 ps; the chip cap equals
  10^12·71/78. Final completions 60000/62000/120000 and barrier 94000 also match. The
  intermediate timestamps depend on the reading (A-F2), and the refresh fault is masked
  (A-F3).
- **E5 and B's example.** U0022's 3E+casts arithmetic gives 60/56/24, R2 30/40/24,
  FP32 36/80/48 and prefill 360/336/144. B's partial-tail example gives 960/960/576, with
  576 when casts are omitted. KV 272/512/16; fused attention 272+272. Pairings give
  [-2,1,3,4] and [-3,2,1,4].
- **Mechanism review.** Phase ordering (completion before readiness before issue) and
  canonical-ID FIFO are deterministic. Credits until commit/ack, read/write sharing the
  channel cap, and the shared core port all respect F1. Useful and issued work, and
  payload and transaction bytes, are kept distinct. Occupancy is the union of
  allocations. Attribution is a causal partition. Gaps are recorded in A-F2–A-F4.

### 3. Carriers, identity, legacy, fixture/production separation, replay

- **Identity graph is acyclic.** Graph → point → bundle → job → result. The request
  references the bundle; component `request_hash` is null and components never become
  table rows. Additive roots keep old roots strict, R01 refuses `uarch-engine/1` and `/2`,
  and full legacy replay stays analytic.
- **Replay and determinism.** Saved replay disables all producers. Three fresh processes,
  debug/release identity and trace-on/off numeric projections are specified.
- **No version-name collisions.** None of the proposed names (`uarch-prepared/3`,
  `uarch-taskgraph/1`, `uarch-engine/3`, `uarch-native-observations/1`, `native-stage/1`)
  appears anywhere in `src/`, `contract/`, `scripts/` or `tests/`. `/2` names exist for
  RoPE v2, as expected.
- **Literal C1 validates.** The C1 OpSpec and PreparedOp validate against the live v1
  carriers (`C1-PREPAREDOP-V1 valid`).
- **Missing construction semantics.** A-F1, A-F5 and A-F6. A missing installed schema is
  expected and is not a finding.

### 4. Discriminating expectations and future public-boundary faults

- **Matrix design.** V01–V28 separate admission refusals (V01/V05) from numerical
  mutants, require restored controls and keep crashes or setup errors from counting as
  kills. That is consistent with U0006.
- **Feasibility gaps.** V08, V13 and V17 have no admissible path (A-F1). The refusal
  fault in V13 needs at least 5 same-channel requests (A-F3). V26 does not discriminate
  owner arbitration (A-F4).
- **Clock scopes are separate.** Historical aggregate-only 22/24
  (`analytic.aggregate_clock/1:aggregate:d4-bf16-v1`, present in the SR-C1 plan/corpus),
  native component-clock checks and a future true-premise per_op domain are three
  distinct rows (`verification.md:292-294`). Historical outcomes (14/14, 9/13/5, 22/24)
  are preserved.
- **Analytic unobservability.** It is never used as native evidence (row C4).

### 5. Prerequisites, and ready versus unexecuted work

- **Toolchain/licences.** Unresolved and declared as a K1 blocker; correct. The
  allow-list (`third_party/LICENSES.md:3`) excludes Unicode-3.0, which U-P11a:45-46 says
  serde_derive's `unicode-ident` carries. The pin-only proposal should therefore list that
  ADR as a known item, not a hypothetical one (observation; not verified offline).
  `native/` is an empty workspace, and the CI native job installs cargo-deny unpinned,
  matching A's "no no-op readiness" statement.
- **Human L1 fixtures.** Two are required and not yet assigned. The latency-bound one
  depends on A-F2.
- **Reference readiness.** Scheduled before R/G3a, with no TPU file, spend or pilot.
- **Budgets.** Only the K2/B envelope is proposed (A-F10); later budgets are withdrawn
  (A-F9).
- **Product scope.** T preserves npu-m256/70B/FP8/tp8; the FP8/ragged decisions are
  explicit.
- **No false G2 completion.** Nothing claims G2 is complete.

## Coordinator reconciliation claims at the target

| Claim (`U3-design-audit-reconciliation-v1/README.md`) | Result |
| --- | --- |
| A v2 implements U3 → M/K1/K2/B → R → U7 T; no U3/U4 full table | Verified (check 1) |
| B inventory 97 → 52 (39 retained, 58 removed, 13 added) | Verified in `support-delta.json` |
| A-C1: the pre-correction C1 row said "both modes" and was ambiguous | Verified at `3ebe76b` |
| A-C1 corrected at target | Verified in `verification.md`, U0011, `decisions.md`, README; the interface diff since `3ebe76b` is additions only; scope/E1–E5 unchanged |
| A supplies the M import/initializer/data note | Present, `interface.md:308-388` (see below) |
| A checker "8 files, 25 links" at `1ad61f6` | Now 8 files, **36** links, 2 projections, PASS at target; consistent with A's follow-up |
| CI-form mypy 79/31 files (patched export) | Unpatched target: 78/31, consistent (the patch adds `scripts/u2_support.py`) |
| B-C1/B-C2 corrected | **Not rerun by Lane A** (B lane). Patch SHA256 `97d0ec30…` matches B's correction |

**M note against real code (all confirmed).**

- `scripts/u2_inputs.py` imports `uarch_contract.exports` and `rkuarch.hw.export`, then
  `hw.derive`, then `rkuarch.engines.protocol.ResolvedHardware`.
- The `rkuarch`, `hw`, `engines` and `scripts` initializers hold only docstrings, plus
  `ENGINE_VERSION` in `rkuarch`.
- `uarch_contract/__init__.py` re-exports the stated carrier families.
- Every file A lists as retained appears in B's retained set; `rotary_v2.py` and the
  native/mapping/workload modules appear in B's removed set.
- Live `support_files()` enumerates all `*.py` under `src/rkuarch`,
  `contract/uarch_contract` and `scripts`.
- B's data globs (`a2-export/{*.json,*.yaml,PIN}`, `contract/fixtures/model_shapes/*.json`)
  are non-recursive, so a proposed `contract/fixtures/mapped/` sits outside them, as A says.

The note is accurate. As A and B both state, it is design consultation, not an audit of
unimplemented code.

## Shared-boundary observations for the coordinator

| Observation | Suggested owner |
| --- | --- |
| Test-profile hardware variants (A-F1): admission semantics and result marker; variant specs/rationales in `hw/designs/`; any reached reader of those YAMLs needs reviewed data-family binding under either U0002 policy | A semantics; B variants and support classification |
| E4 conventions fix B's independent queue/conservation/attribution expectations and the human latency-bound fixture (A-F2, A-F3) | A law; B expectations; coordinator/Javid fixture assignment |
| U-P6's "DMA in = compute consumed + written back" shorthand is replaced by per-boundary inventory, which needs explicit B/coordinator acceptance and a prompt-amendment route, not a silent edit | B / coordinator |
| Exact M patch closure: A supplies every import, initializer, data and environment edge; B recomputes and adds public-loader controls | A inventory; B closure |
| Observation volume against the performance envelope (A-F10) | A; B as G5-performance owner |
| B's supplement places native conservation/causality/capacity controls before K2/B acceptance; A's mandatory observations match that schedule | Consistent; no action |

## Checks run, not run, environment

**Run** (all against a private `git archive` export of the target; outputs in `run_all.log`):

- Target tree verification, and assertion that runtime imports resolve to the export.
- A's `checks.md` block, extracted verbatim (SHA256 `1f5949a3…`): PASS.
- `probe_contract` (identity, literal carriers, R06, fault/restored controls).
- `probe_ledger`, `probe_arithmetic` (re-derivations, alternative readings, fault/restored
  controls) and `probe_volume`.
- CI-form `ruff check .` (pass), `mypy src contract/uarch_contract scripts` (78 files, no
  issues) and `mypy --no-explicit-package-bases contract/tests` (31 files, no issues).
- `pytest tests/unit/test_prompt_sync.py`: 4 passed.
- Diffs `3ebe76b..184d2c2` of the design package and of the target commits.

**Fault/restored controls:**

- Perturbing a hardware value changes the hash; restoring it matches.
- An undefined reduction axis is refused; restoring the original validates.
- The E2 rounded-period and floored-edge mutants differ from the restored values.
- The E3 no-overhead and padded-useful mutants differ.
- The E4 per-channel ×8 mutant differs. The refresh-omission mutant is not detected by
  the 1- and 2-request fixtures; it is detected from the 5th request (A-F3).

**Not run:**

- B's repair suite and its loader faults (B's lane).
- `lint-imports`: it would resolve the venv's editable live roots, and the target changes
  no Python.
- The full pytest suite, any native build/run, hosted CI, fresh clones, any controlled
  host or performance measurement, generation/adoption, corpus execution, or any change
  to a live author or protected file.

**Environment:**

- WSL2 (Linux 6.6.87.2), so no timing is a performance observation.
- Existing `.venv` (Python 3.12.14, ruff 0.16.9, mypy 2.3.1) used without `uv sync`.
  Its editable `.pth` points to the live clone; this is countered by running `-I` with
  the export paths prepended and asserting `__file__`.
- Standard-library probes ran on system Python 3.12.3.
- Ambient `PYTHONPATH`/`MYPYPATH` were empty and are unset in the runner.
- No dependency was installed and no host was contacted.

## Ready decisions versus later work (Lane A readiness recommendation)

**Ready for Javid's decision once the author answers the non-blocking findings:**

- the bounded B scope and refusal list, apart from the test-profile path;
- the M/K1/K2/B/R/T structure, with A-F7's alignment;
- the E1/E2/E3 conventions;
- the zero-delay convention, once A-F4 is clarified;
- the correctness/performance/nightly separation;
- U7 full tables and U10 integration placement;
- the reference-readiness schedule;
- the clock-scope separation (A-C1).

**Not ready for exact acceptance until corrected:**

- the mapped schema plan, refusal catalogue and B verification matrix (A-F1);
- the E4 DRAM/NoC/DMA law and the human latency-bound fixture that depends on it (A-F2).

**Remain unexecuted or unapproved later work, by the package's own statement:**

- exact Rust/tool/licence pins (blocks K1);
- installed mapped carriers (blocks K2);
- the U0002 policy/migration decision, or explicit retention (before M install);
- two human L1 fixtures;
- B's frozen corpus and analytic first-use selections;
- TPU sourcing and the suite;
- performance budgets and host;
- product semantics.

This recommendation is for Lane A only. It is not Stage 3 ACCEPTED, G2 closure or
authority to implement. Authors answer every numbered finding in their own Stage 2
response. This reviewer returns for Lane A's Stage 3 adjudication.


---

## Stage 3 adjudication — 2026-10-13 — target `a7f4acb12d4bd4adf29668a9707440738aa44f09`

Tree `13252ba86aca34487f650460a6291eab1b98f502` (verified). Stage 1 target `184d2c2`.
Lane A corrections: `98640e22173ab334d4f98e2306d7286d07c96e64` and
`43ab3e0809b58f7691396161c591c83726bb778d`. The response under review is
`docs/reviews/U3-lane-A-response.md` at the target. Evidence:
[U3-independent-review-A-stage3-v1/](U3-independent-review-A-stage3-v1/README.md); exact
outputs are in its `run_stage3.log` (UTC timestamps).

**Same reviewer.** This is the session that wrote the Stage 1 section above, which was
read back and not altered.

**Prefix preservation.** Bytes 1–30574 of this file are the Stage 1 report, SHA256
`b69965a70dc4262141c2d52b877cb9ce253566c1aba3bbf5d64e8e198e774233`. Verify with
`head -c 30574 docs/reviews/U3-lane-A-review.md | sha256sum`. The Stage 1 evidence files
in `U3-independent-review-A-v1/` are unchanged (hashes in the log).

**Pin.** Live HEAD advanced during this session to `40fab28`, a later Lane B-only commit
touching only B documents. It is outside the pin and not part of this adjudication.

**Scope.** U-REVIEW Stage 3 checks (a), (b) and (c) only. There are no new findings. B's
repair is not adjudicated here. All checks are proposal-text, carrier and arithmetic
checks, not native regressions.

### (a) Every numbered finding has a row

| Finding | Stage 1 severity | Response row | Disposition |
| --- | --- | --- | --- |
| A-F1 | BLOCKING | `U3-lane-A-response.md:44` | APPLIED |
| A-F2 | BLOCKING | `:45` | APPLIED |
| A-F3 | NON-BLOCKING | `:46` | APPLIED |
| A-F4 | NON-BLOCKING | `:47` | APPLIED |
| A-F5 | NON-BLOCKING | `:48` | APPLIED |
| A-F6 | NON-BLOCKING | `:49` | APPLIED |
| A-F7 | NON-BLOCKING | `:50` | APPLIED |
| A-F8 | NON-BLOCKING | `:51` | APPLIED |
| A-F9 | NON-BLOCKING | `:52` | APPLIED |
| A-F10 | NON-BLOCKING | `:53` | APPLIED |

Both blocking rows are stated at the top of the response, as U-REVIEW requires.

### (b) Rejected reasons address their findings

No row is REJECTED or DEFERRED, so (b) holds vacuously. Several rows name later human
or B work: B derivations, catalogue freeze, exact human acceptance. These are the gates
listed below, not deferrals of the corrections themselves.

### (c) Each applied change has a check that fails without it

Author checks f1–f10 come from `U3-A-stage2-proposal-checks.md`, extracted verbatim
(SHA256 `0a9c35a2…`).

- **Target:** 10 PASS, plus the shared DMA/clock/first-use checks PASS.
- **Fresh Stage 1 export:** 10 FAIL. This is equivalent to `U3A_DOC_REF=184d2c2`; the
  export has no `.git`. f5 there raises the real two-error `ExtCounts` `ValidationError`.
- **Package checker:** 8 Markdown files, 39 links, 2 JSON projections, PASS.

I also wrote `stage3_independent.py`, which re-derives each correction without the
author's helpers. It uses E2's integer edge formula rather than the author's Fraction
search, models port queuing, and parses tables instead of asserting constants. It gives
10 PASS on the target and 10 FAIL on the Stage 1 export.

My judgment of each check's sufficiency:

| Finding | Author check, by kind | Reviewer-independent confirmation | Sufficiency |
| --- | --- | --- | --- |
| A-F1 | Structural: six matrix rows, refusal codes, profile markers. Its symbolic `admits` set is defined inside the check, so discrimination comes from the document assertions | Production row unchanged (npu-l4, ratio 1, component/cold). B test rows exist for component/fixture_resident, transport_fixture and kernel_fixture. Every Stage 1 casualty has a variant family: credits 1/2, accumulator 131072, ratios {1,2}, latency ×2, rates ×2, unused column. Five test-admission refusals. Variants are stipulations, not sourced claims | Sufficient for a proposal |
| A-F2 | Numeric: all seven E4 timeline rows recomputed; old 58250 and 1.2 GHz 59000 discriminators | All seven rows equal my integer-edge lifecycle (port queue modeled); attribution partition present; DRAM-edge rule present | Strong |
| A-F3 | Numeric: five-read lists ending 69000 vs 68000; 33 addresses map to channel 6; issue-rate and overhead text | Same lists with port contention; channel end 54250 vs 54048; V13 row updated | Strong |
| A-F4 | The 5000-vs-3000 arithmetic is self-contained; discrimination comes from the rule text markers | Owner-grant rule, the "bypass must fail" sentence and the zero-hop admission text present | Adequate (the rule is prose) |
| A-F5 | Live strict `PreparedOp`/`Counts`/`ExtCounts` validate the revised projection; the two old `ExtCounts` errors still refuse | MAC×2 = matrix_ops; C2 105/100/42/512/256 derived; payload rule and validation order checked by position | Strong; strict roots not weakened |
| A-F6 | Exact equality between the 59 listed leaves and the live `HardwareSpec`; bank and owner ordering | Independent parse: 59 unique leaves, set-equal; bank region 524288 → bank 1; InvalidBank; `native-owners/1` | Strong |
| A-F7 | Text of the K2 and B rows | K2 row has no mapper prerequisite; B row requires the component mapper; U0011 aligned | Adequate |
| A-F8 | Asserts totals from constants plus document phrases; does not parse the table cells | Parses the W, R-specific and T rows: 76–124, 44–76, sum 120–200, W+T 184–312 (A 100–168, B 64–112, review 20–32); Q6-C/D/W rows exist | Adequate when combined; the author check alone would miss an edited cell under an unchanged total phrase (an observation, not a new finding) |
| A-F9 | Phrase presence in delivery and U0011 | The quoted U9 phrase matches the live execution-plan text exactly. The random revert below shows the check discriminates | Adequate for a prose pointer |
| A-F10 | Arithmetic plus phrases | 98304 maximum and 576-request derivations; no-dropping and unchanged-maximum-scope text; U0011 small-fixture text | Adequate |

### Random bounded revert and restore

**Selection.** `random.SystemRandom().randint(1,10)` drew **9**, so **A-F9**, at
2026-10-13T23:01:34Z, before the run (`random_selection.txt`).

**Reverted scope, scratch copy of the target only** (`revert_af9.py`; full diff in the log):

| File | Removed |
| --- | --- |
| `delivery.md` | Lines 240–259: the whole "Stage 2 prospective U9 budget record (A-F9)" section (20 lines) |
| `proposed-U0011.md` | Lines 187–188: the sentence "The later prospective U0011-Q addendum … the small fixture ceiling does not." A-F10's edits in the same paragraph were left intact |
| `README.md:105` | The fragment `/U0011-Q` |
| `decisions.md:86` | The fragment `(A-F9) later U0011-Q budget record; ` |

**Result.**
- Author checks: only A-F9 FAILS; the other nine PASS, so the revert is bounded. All four
  f9 assertions fail for the stated reason: `U0011-Q` is missing from delivery and from
  U0011, and the trigger and "G6 and full G5" sentences are gone.
- My independent probe also fails only A-F9.

**Each half is guarded.**
- Removing only the delivery section fails the three delivery assertions; the U0011
  assertion still holds.
- Removing only the U0011 sentence fails the U0011 assertion alone.

**Restore.** A fresh copy is identical to the target export (`diff -r` empty). The author
checks give 10 PASS and all four f9 assertions hold.

### Shared dependencies (recorded, not adjudicated)

B's response is published at the target. It aligns the B-F2/F3/F5/F6/F7 text with A, and
B-F3/F5/F6 remain B's DEFERRED rows for coordinator disposition. B has not yet derived
independent expectations for A's revised E4, variant catalogue and observation/record
accounting, nor supplied performance-gate input against this revision. Neither f1–f10
nor this reviewer's probes are those derivations.

### Checks run, not run, environment

**Run:**
- the full `run_stage3.sh` (see the log);
- bounded `pytest -c pyproject.toml --rootdir . tests/unit/test_prompt_sync.py` on the
  target export: 4 passed.

**Not rerun:** ruff and mypy. No paths outside `docs/` changed between `184d2c2` and
`a7f4acb` (log: 0), so the Stage 1 static results cover identical Python bytes.

**Not run:** B's repair suite, any native build or run, the full suite, hosted CI, any
host contact, measurements, generation or adoption.

**Environment:** WSL2. The existing `.venv` (Python 3.12.14) ran with `-I -B` and the
export paths prepended, with import origin asserted. System `python3` ran the stdlib-only
revert/reason scripts. `PYTHONPATH`/`MYPYPATH` were unset.

### Verdict

**ACCEPTED** — the Lane A Stage 2 response at `a7f4acb` (tree `13252ba…`). No rows are at
fault: every finding has a row (a), nothing was rejected (b), and every applied correction
has a check that fails without it (c). For (c) the evidence is the whole-document Stage 1
failure, the reviewer-independent re-derivation and the random bounded A-F9 revert and
restore.

Acceptance covers the author response only. It does not accept or install the proposed
U0011, the admission/test-profile registry, the carrier/schema semantics, the revised E4
law, the H-DMA/H-CLOCK text, U0011-Q or other budgets, or the W/Q6 allocations. It does
not approve B's policy or repair, release native implementation, or close G2/U3.

### Remaining human and implementation gates

1. **Javid, exact U0011 clauses.** Admission matrix and test-profile/spec registry;
   revised E4 law and wait attribution; zero-duration owner-grant rule; count roots and
   validation order; hardware ledger and bank/owner enumeration; then the M
   carriers/schema/fixtures before protected installation.
2. **U0002.** B's repair/migration decision, or explicit retained enforcement with
   budgeted M/K2/B lifecycle cycles, before M installation. Current enforcement remains.
3. **K1 prerequisites.** A pin-only toolchain/licence decision before K1, including the
   Unicode-3.0 (`unicode-ident`) allow-list ADR. B's CI pins and real Linux CI before K1
   evidence is credited (S-CI assignment).
4. **B's independent work.** Derive the revised E4 expectations; freeze the variant
   catalogue, profile and corpus; accept observation-record accounting.
5. **Human L1 fixtures.** The two human-worked fixtures are still unassigned; the
   latency-bound one must use the accepted E4.
6. **Prompt and shared decisions.** H-DMA/H-CLOCK prompt and build-spec wording;
   S-COMPONENT and S-QUEUE.
7. **Inputs and budgets.**
   - Freeze the W/Q6 manifest and the U6 representative inputs.
   - Settle U0011-Q budgets before U-P11c/U-P13d measurements.
   - Accept small and full-size performance budgets with a host allocation.
   - Execute the self-hosted nightly for full G5.
8. **Later scopes.** R sourcing and the signed suite; T product semantics (FP8, ragged,
   RoPE).
