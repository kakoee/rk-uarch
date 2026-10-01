# rk-uarch Rev 2 — book coverage and plan soundness (review)

Reviewed at `1876a8f` (HEAD; includes the review prompt). Rev 2 diff read as
`git diff 0868dd3 HEAD -- docs CLAUDE.md rk-sim-side '*.md'`. `[R path:line]` = fact from the
repo; `[judgement]` = reviewer's computer-architecture judgement. Line numbers refer to HEAD.

## 1. Verdict

**Fit: yes, as a cycle-*approximate*, tile-level simulator with an unusually strong evidence
discipline. Ready for U-P1: no**, because the contract that G1 freezes contradicts its own
acceptance tests, leaves out the tensor-parallel shard, and lacks six decisions that ADR
U0001 must make (Findings 1, 3, 4). Stopping at cycle-approximate (tile-job events, a reservation NoC, Ramulator DRAM, RTL only as
an optional reference [R docs/build-spec.md:344-350], [R docs/build-spec.md:2069-2070]) is the
right call for a per-iteration LLM cost table [judgement]. No document claims "cycle-accurate";
that phrase is the founders' overclaim, not the plan's, though U4's "C2" label is asserted
rather than derived (Finding 5). Book coverage is good (42 of 61 applicable parts Covered, 14
Partial), but the plan has soundness gaps the book does not name: U2's gate has no oracle,
nothing says where attention intermediates live, memory-controller back-pressure is missing,
and no planned silicon evidence reaches the demo's own request (Findings 2, 6, 7, 8).

## 2. Findings

All `[R …]` without a path are `docs/build-spec.md`.

**1. BLOCKING — The tensor-parallel shard is never built or checked.** The request carries
`tp` [R 241], but the workload graph takes no tp [R 1434-1436], every planned table is tp=1
[R 1785], the table schema has no tp [R 262-292], and none of the eight rules compares the
table's tp with the plan's [R 1095-1108], so U-P19's divisor of 1 [R 2602-2603] silently
charges each chip in an 8-way-TP rack the whole model's cost. Rule 6 likewise checks a spec
hash, not the params [R 2576-2577], and a whole 70B model on one chip makes
`ResidencyExceedsCapacity` on weights [R 1782-1783] likely for the demo's npu-m256 and for
G3's bf16 npu-l4 table [judgement]. Fix: U-P1 adds `tp` to `UarchCostTable`, a ninth rule and
a `TpMismatch` row (§7.2, §7.4, U-P1 item 10); U-P2 adds parity fixtures at tp > 1; U-P3
shards the graph by tp (heads, KV heads, FFN columns); U-P19 tests table tp == plan tp.

**2. BLOCKING — U2's ±0.1% gate has no oracle.** U-P3 acceptance 1 and the U2 exit criterion
compare U-C0, fed `derive_rk_params(spec)`, with "the parity fixtures' rk-sim durations"
[R 1469-1471], [R docs/execution-plan.md:115], but U-P2's fixtures record only counts and the
query, for no component [R 1355-1357], and the specs whose params are needed do not exist
until U-P3 [R 1410-1415]. An agent can pass only by re-deriving rk-sim's duration formula,
which U-P2 itself calls "a mirror, not an oracle" [R 1358-1359]. Fix: U-P2's `vendor_rk.py`
also records rk-sim's `decode_s`/`prefill_s` for named component param files (rk-sim's own
library entries, plus `uarch rk-component` output a human feeds it in U2), U-P3 acceptance 1
feeds U-C0 those same params, and U-P2's query set is pinned to include G2(c)'s points
[R 1640-1641].

**3. BLOCKING — U-P1's acceptance tests contradict the contract it is told to copy.**
Acceptance 6 fails any float without an allowed suffix [R 1302-1303], [R 1038-1040], yet
§2.3.3 names `median_rel`, `max_rel`, `rel`, `noc_flit_hops` and unsuffixed inner keys of
`attribution_s` and `peak_resident_bytes` [R 271-274], [R 284-288]; acceptance 10 refuses a
spec that "names a preset" [R 1310-1311], but no field names a preset, only free-text
`source` strings [R 220-222]; and banks, DMA engines, virtual channels, DRAM channels and the
array are drawn as plain ints [R 189-193], [R 201], [R 205], which a reference cannot mark
stub, although "every numeric leaf is a SourcedValue" [R 1236-1240]. The agent must stop or
silently redesign the contract that G1 freezes. Fix: in build-spec §2.3.2–§2.3.3, §6.1 and
U-P1, allow `_rel` (or rename to `_ratio`), suffix or dict-type the inner keys, add
`memory.dram.timing_preset: {file, sha} | null` and test `UnnamedPreset` against it, and
list exactly which integers are plain composition and which are SourcedValues.

**4. BLOCKING — ADR U0001's decision list is incomplete, and U-P1's authority is ambiguous.**
U-P1 lists five Rev-2 decisions with defaults [R 1329-1332] but omits six: the tp semantics
(Finding 1); applicability granularity (shape regime is per operator [R 424-426], a badge is
per row or metric [R 1509]); the clock domain of each `*_cycles` leaf (only DRAM timing
names one [R 208]) and which domains scale with `frequency_ratio`, which U-P7 reads from a
spec field that does not exist [R 1779-1780]; the legal values of
`uarch_fidelity`/`fidelity_detail` (the request asks `noc: 1`, the table answers `"1+ts"`
[R 251], [R 267]); the prefill row's key fields (only a decode row is drawn [R 269], yet the
toy table needs a prefill row [R 1308-1309]); and whether the table embeds the card's badge or
only its hash (§3.6). CLAUDE.md, loaded first, also tells agents to "propose and stop on
contract/" [R CLAUDE.md:63], which a fresh agent can read as forbidding the very files U-P1
asks for. Fix: U-P1's ADR paragraph lists the six with defaults (proposal: a row's
applicability needs every op's regime covered; each `*_cycles` leaf is in its owning block's
domain; only `clock_domains.core` scales unless a domain opts in), and U-P1 states that
writing `contract/` and U0001 uncommitted is the authorised proposal.

**5. BLOCKING — The fidelity ladder cannot label a table yet, so U4's "C2" is asserted.** No
prompt places the fork's sub-models on the §2.4 ladder (U-P5's parser emits duration, busy
time, counts, diagnostics and attribution only [R 1621-1625]), yet U-P7 builds "the first C2
table" from the fork and G3 is "A C2 table exists" [R 1739-1740],
[R docs/execution-plan.md:255]; the C2 rule needs "SRAM banks" at 2 or 1+ts with no
`fidelity_detail` key for them [R 361-363], [R 267], U-P13 accepts `dram: 1+ts`, a level the
DRAM row never defines [R 348], [R 2222], and nothing says what compute needs. Because the
image carries BookSim 2 and Ramulator 2 as the fork's own submodules [R 1598-1599], G3's NoC
L2 bound may compare BookSim with itself, and G5's "matched levels" [R 2094-2096] is undefined
for the fork. Fix: §2.4 and U-P1 fix the `fidelity_detail` keys and legal values (define DRAM
1+ts or drop it; state compute's requirement); U-P5 records each fork sub-model's level per
configuration in ADR U0005 and lets the rule compute the composite (C1 if the fork models no
bank conflicts); U-P8 refuses an L2 comparison of a reference with itself; U-P15 drops
"detail 0/0/0" [R 2348] or U-P11 builds native compute level 0.

**6. BLOCKING — Nothing says where attention intermediates live, so long-context prefill rows
will be wrong.** The vocabulary splits attention into QK score, softmax and AV [R 335-336],
the graph is op by op [R 1434-1436], no policy fuses ops or keeps scores on chip, and a tile
that does not fit is refused, never spilled [R 806]; at the grid's L = 32768 [R 248] one
head's score matrix holds about 1.07e9 elements, so a prefill row is either refused or
charged L²-sized DRAM traffic that real kernels avoid by fusing attention [judgement]. The
same unstated choice sets the graph's `memory_read_bytes`, which U-P2's harness checks at
0.5% [R 1369-1373]. Fix: U-P1 adds a fused-attention operator (QK → softmax → AV over KV
tiles, scores on chip) as "what tiling needs", FLOPs unchanged; U-P3 counts only Q, K, V and
O bytes for it; U-P7 and U-P13 policies tile it under SRAM capacity; U0001 records the choice.

**7. MAJOR — The planned silicon evidence cannot reach the demo's own request.** The demo
table is npu-m256 × Llama-3.1-70B × fp8 [R 78]: TPU v5e evidence is the wrong family
[R 2000-2001]; Blackhole's low-precision evidence is BLOCKFP8, which U0001's proposed default
says does not cover fp8 [R 429-430], [R 2341-2342]; and the Blackhole suite has no end-to-end
class (its largest unit is "one decoder-layer operator set at a decode shape" [R 2333-2334])
while only end-to-end entries may validate whole-iteration rows [R 1998-1999]. So every demo
row is stub by construction, "detail is not accuracy" is tested only at U8 on microbenchmarks,
and G4's fail branch ("one subsystem explains ≥70% of the error") and G7's "closer than
level 1" have no defined computation [R docs/execution-plan.md:271-272],
[R docs/execution-plan.md:292-294]. Fix: U-P15 adds an end-to-end class (a full decoder layer
at decode and prefill shapes across ≥64 cores) and measures the demo's precision, or §1.2
switches to a precision Blackhole measures; execution-plan §4 defines G4's attribution and
G7's metric before U5.

**8. MAJOR — The core and memory models lack state that a cycle-level accelerator model
needs.** HardwareSpec has no accumulator or operand-buffer capacity and no in-core
operand-move bandwidth [R 186-195], so output-tile limits and partial-sum spills on a
weight-stationary array are invisible [judgement], and issue, descriptor and semaphore cost
is one constant per tile job [R 195]. Memory controllers have no queue depth or credit count
[R 204], yet U-P18 pre-registers its experiment at a "memory-controller partition with
closed-loop credit backpressure" [R 2496-2497], and Ramulator's queue sizes would come from a
preset the spec does not name (the no-preset rule covers timing only [R 220-222]). Fix:
§2.3.2 and U-P1 add accumulator bytes, operand-buffer bytes and bandwidth per core,
controller read/write queue depths and NoC-to-controller credits as SourcedValues; U-P11 and
U-P13 model them from level 1; extend the no-preset rule to all Ramulator configuration.

**9. MAJOR — Design studies cannot vary the structure of a chip.** Variants may change only
stipulations [R 2257-2260], but the array, core grid, banks, DMA engines and DRAM channels are
plain ints and `dataflows` a plain enum [R 189], [R 217-219], [R 1239-1240], so array-size or
core-count studies are refused, and the plan's own `npu-l4-dataflow.yaml` (WS vs OS)
[R 2280-2281] both varies a non-stipulation and needs an output-stationary policy no prompt
builds [R 1745-1750], [R 2200-2204]. Fix: U-P14 admits structural paths of a proposed design
as stipulated variants (recorded in `conditional_on`, mapping re-run per variant); U-P7 adds
an output-stationary policy, or U-P14 drops the dataflow study.

**10. MAJOR — The native-engine prompts are not one-session tasks.** U-P11 (180 h
realistic), U-P13 (156 h) and U-P17 (120 h) [R docs/execution-plan.md:400-406] each run as
"one prompt, one session" that must "stop after this prompt" [R docs/execution-plan.md:35],
[R docs/prompts/TEMPLATE-implementation-session.md:21], and U-P11 alone asks for the kernel,
three subsystem models, a TaskGraph executor with steady-state priming, the Python adapter,
attribution, traces, full L0–L1 passes and G5 [R 2039-2101]; an agent will stop with a
partial engine and no defined handoff point, or quietly thin the tests [judgement]. Fix:
split U-P11 into P11a (time base, events, wheel, arena, ownership, doctest), P11b (models and
TaskGraph executor, L0–L1) and P11c (Python side, attribution, G5), and split U-P13 into NoC /
DRAM and Ramulator / compute level 2 and shared SRAM / mesh policies and composite, each with
its own acceptance subset in build-spec §8 and execution-plan §3.

**11. MINOR — The execution plan's calendar and status are wrong.** Lane A is not the
critical path: sprints close only when both lanes integrate, Lane B is longer in U5, U8 and
U10, and Σ max(A, B) per sprint is 906 h realistic (≈45 weeks) and 468.5 h best (≈23 weeks),
not 42 and 22 [R docs/execution-plan.md:445-450] (§3.5); STATUS says "U0 in progress" and
lists files to add, although `a5a4cc4` added them and is tagged `u00-end` (git)
[R docs/execution-plan.md:23], and U7's exit says "two example studies" against U-P14's three
[R docs/execution-plan.md:175]. Fix: execution-plan §7.4 (Σ max per sprint,
plus U5/U8's freeze → measure serialisation), STATUS and U7's exit row; add the missing CI
jobs (§3.6) to `.github/workflows/ci.yml` and make `tests/unit/test_prompt_sync.py` compare
per heading in both directions (§3.1).

**12. MINOR — Scope: some planned work the question does not need, and two book concepts it
does.** The stated question is already parallel across grid points from U4 [R 100], yet U9's
in-simulation parallelism (186 h realistic [R docs/execution-plan.md:427]) is not tied to any
measured single-point wall-clock need; F9's shared SRAM is validated by no reference chip and
varied by no study [R 197-198], [R 2278-2281], and F11's Accelergy rung covers SRAM pJ only
[R 1854-1857] yet, once cited, makes `energy_verification` non-null so energy stops rendering
"unverified" [R 1527-1528] with three of four coefficient families unchecked. Meanwhile
warm-up length (book 6.3.3) is never checked, because `steady` is one priming iteration
[R 319], and no L3 kit compares the architect diagnostics shown in the demo
[R 79] with silicon counters (L3 checks durations and FLOPs/bytes only [R 448]). Fix:
execution-plan §3 gates U9 on a pre-registered single-point wall-clock budget breached after
U7, and defers shared SRAM and the Accelergy rung until after U8; U-P7 adds a
one-vs-two-priming-iterations check to `cold_vs_steady`; U-P10 and U-P16 record whatever
device counters each chip exposes as diagnostic ledger entries.

## 3. Mechanical checks

### 3.1 `uv run pytest -q` — PASS, but the sync test proves less than claimed

```
$ uv run pytest -q
...                                                                      [100%]
3 passed in 0.08s
$ uv run python --version          → Python 3.12.14
$ uv run ruff check                → All checks passed!
$ uv run mypy src contract         → Success: no issues found in 27 source files
$ uv run lint-imports              → Contracts: 2 kept, 0 broken.
```

`test_prompt_sync.py` only asserts that each prompt file's text block is a *substring* of §8
[R tests/unit/test_prompt_sync.py:16-20]. It would pass if a prompt file held a truncated
block, or if a §8 prompt had no file at all. It does not prove the claim in U-P0 item 4
("equals the text block in the matching docs/prompts/ file") [R docs/build-spec.md:1180-1181].
Independent check (scratchpad script, not committed): split §8 at each `### ` heading, matched
every `docs/prompts/*.md` by its title line, and compared block lists for equality. **24/24 §8
sections have a file whose blocks are equal; no §8 section lacks a file** (TEMPLATE has no §8
section, as expected). PASS on content.

### 3.2 Every README and `CLAUDE.md` equals its §4 block — PASS

Extracted all 24 ` ```markdown ` blocks under `### 4.N · \`/path\`` and compared byte for byte:
CLAUDE.md, README.md, and all 22 other READMEs are EQUAL. No README exists outside §4's list
(excluding `.venv/` and `.pytest_cache/`). 23 READMEs + CLAUDE.md matches §0's "23 READMEs"
[R docs/build-spec.md:41].

### 3.3 rk-sim-side prompts carry U-P19 / U-P20's text — PASS

`rk-sim-side/prompts/P18-characterized-c2-cost.md` and `P19-stipulations-and-chip-views.md`:
one text block each, equal to the block in U-P19 and U-P20 respectively.

### 3.4 Numbers repeated across documents

| Check | Result | Evidence |
|---|---|---|
| "eight rules" | PASS | §7.2 lists 1–8 [R docs/build-spec.md:1089-1108]; U-P1 ADR "eight semantic rules" [R docs/build-spec.md:1326]; U-P7 [R docs/build-spec.md:1734]; U-P19 a–h [R docs/build-spec.md:2562-2581]; U10 [R docs/execution-plan.md:210]; draft ADR 1–8 [R rk-sim-side/decisions/DRAFT-admit-characterized-c2-tables.md:62-73]. `grep` finds no "six rules" outside the earlier review and the review prompt |
| U-P9 vs G4 | PASS on numbers, gap in content | "at least 24 benchmarks across at least 5 classes" [R docs/build-spec.md:1904-1905] = "≥24 … ≥5 classes" [R docs/execution-plan.md:265]. U-P9 enumerates **six** classes [R docs/build-spec.md:1906-1915], so both Rev-2 classes (DRAM gather, launch overhead) can be dropped and every check still passes |
| U-P15 vs G7 | PASS | "at least 32 … at least 7" with seven listed [R docs/build-spec.md:2328-2339] = G7 [R docs/execution-plan.md:288-289] = U-P16 acceptance 3 [R docs/build-spec.md:2413] |
| Measured errors in §2.3.3, U-P1, U-P7, table README | PASS | All four list interpolation_loo (+weighted), composition_reduction, layer_reuse, cold_vs_steady: [R docs/build-spec.md:284-287], [R docs/build-spec.md:1271-1273], [R docs/build-spec.md:1764-1778], [R src/rkuarch/table/README.md:5-7] |
| Measured errors elsewhere | FAIL (subsets) | §1.2 demo prints three, omitting cold-vs-steady [R docs/build-spec.md:78]; §7.2 rule 2 and U-P19 rule b surface only composition and layer reuse in rk-sim, never interpolation LOO [R docs/build-spec.md:1097-1098], [R docs/build-spec.md:2567-2568]; U-P20 chip panel lists three [R docs/build-spec.md:2651-2652]; draft ADR context lists two [R rk-sim-side/decisions/DRAFT-admit-characterized-c2-tables.md:17] |
| Composite C2 rule (§2.4, U-P13, CLAUDE.md 9, G6) | FAIL | The four statements agree in wording [R docs/build-spec.md:361-365], [R CLAUDE.md:34-35], [R docs/execution-plan.md:284-285], [R docs/build-spec.md:2207-2212]. But U-P13 acceptance 2 accepts `dram: 2 or 1+ts` while the DRAM row defines no 1+ts [R docs/build-spec.md:348], [R docs/build-spec.md:2221-2223]; U-P13 refuses C2 for "any subsystem at level 0" [R docs/build-spec.md:2222-2223], [R docs/build-spec.md:2233], stricter than §2.4, which names shared resources only and never says what compute must be; "SRAM banks" is a shared resource in the rule with no key in `fidelity_detail` [R docs/build-spec.md:267] |
| Error classes, §7.4 vs U-P1 item 10 | PARTIAL | Every raising row of §7.4 maps to a U-P1 name [R docs/build-spec.md:1126-1137], [R docs/build-spec.md:1285-1290]; §7.4's residency row has no class name (U-P1: `ResidencyExceedsCapacity`); the "C2 not built" row is UI-only. U-P1 says "one exception class per row" yet adds four with no §7.4 row (`StipulationOnReference`, `ClaimWithoutSource`, `SramCapacityExceeded`, `UnnamedPreset`), and defines `UnnamedPreset` two different ways [R docs/build-spec.md:1289-1290] vs [R docs/build-spec.md:1310-1311] |

### 3.5 `docs/execution-plan.md` §7 arithmetic — PASS on arithmetic, FAIL on the critical-path premise

Recomputed from §7.1 [R docs/execution-plan.md:387-412] with 2.5 h best / 5 h realistic of
review per lane from U1, the schema PR (6/12) split 3/6 per lane in U10, U-P21 (16/30) split
8/15 per lane in U11, and no review in U0:

| Sprint | A best | A real | B best | B real | Sprint real | Cum. real | max(A,B) real |
|---|---|---|---|---|---|---|---|
| U0 | 4 | 8 | — | — | 8 | 8 | 8 |
| U1 | 18.5 | 35 | 10.5 | 21 | 56 | 64 | 35 |
| U2 | 25.5 | 47 | 20.5 | 39 | 86 | 150 | 47 |
| U3 | 28.5 | 57 | 16.5 | 31 | 88 | 238 | 57 |
| U4 | 36.5 | 69 | 29.5 | 57 | 126 | 364 | 69 |
| U5 | 20.5 | 39 | 32.5 | 61 | 100 | 464 | **61 (B)** |
| U6 | 97.5 | 185 | 26.5 | 49 | 234 | 698 | 185 |
| U7 | 80.5 | 161 | 29.5 | 55 | 216 | 914 | 161 |
| U8 | 24.5 | 45 | 41.5 | 81 | 126 | 1,040 | **81 (B)** |
| U9 | 62.5 | 125 | 32.5 | 61 | 186 | 1,226 | 125 |
| U10 | 24.5 | 45 | 30.5 | 57 | 102 | 1,328 | **57 (B)** |
| U11 | 10.5 | 20 | 10.5 | 20 | 40 | 1,368 | 20 |
| Total | 433.5 | 836 | 280.5 | 532 | 1,368 | | **906** |

- Every cell of §7.2 [R docs/execution-plan.md:416-430] matches; totals ~434 / 836 / ~281 /
  532 / 1,368 match; best grand total 714 matches. Milestones 190/364 (U4), 243/464 (U5),
  477/914 (U7), 543/1,040 (U8), 638/1,226 (U9), 714/1,368 (U11) match
  [R docs/execution-plan.md:436-441]. The "about 94 h" Rev 2 delta matches both
  1,368 − 1,274 and the sum of per-prompt deltas (+4, +6, +4, +4, +4, +8, +10, +4, +4, +10,
  +16, +6, +4, +6, +2, +2) [R docs/execution-plan.md:384-385].
- Weeks: 433.5 / 20 = 21.7 ≈ 22 and 836 / 20 = 41.8 ≈ 42, as stated
  [R docs/execution-plan.md:448-450].
- **FAIL:** "Lane A is the critical path" [R docs/execution-plan.md:445-446] is false under the
  plan's own rule that a sprint ends only when both lanes integrate
  [R docs/execution-plan.md:13-14], [R docs/execution-plan.md:41-42]. Lane B is longer in U5,
  U8 and U10. Σ max(A,B) per sprint = **906 h realistic ≈ 45 weeks** and **468.5 h best ≈ 23
  weeks**, before counting U5/U8's serial freeze → measure step
  [R docs/execution-plan.md:71-72].

### 3.6 Rev 1 leftovers and fields one document has and another omits — FAIL

- "the two example studies render" [R docs/execution-plan.md:175] vs "three example studies"
  [R docs/build-spec.md:2278].
- STATUS says "U0 in progress" with `Makefile`, `.pre-commit-config.yaml` and `.github/` still
  to be added by hand [R docs/execution-plan.md:23]; commit `a5a4cc4` added them
  (`git log --stat`), `git tag -l` shows `u00-end` at `a5a4cc4`, and `origin/main` equals
  HEAD. The handoff carries the same stale list and "not tagged"
  [R docs/reviews/U0-U-P0-bootstrap-handoff.md:18-27]. Whether CI ran green on GitHub is not
  visible in the repo.
- CI jobs: §6.7 names lint, types, import-linter, tests, golden, determinism, licences, patches,
  native, ordering, perf [R docs/build-spec.md:1057-1064]. `ci.yml` has python
  (lint/typecheck/imports/tests), golden, determinism, `licences-and-patches` (runs only the
  licence test) and ordering [R .github/workflows/ci.yml:7-60]: no native, perf or
  patch-apply job. U1's exit criterion names a `contract` CI job that does not exist
  [R docs/execution-plan.md:101]. U-P0 acceptance 3 ("Every CI job exists")
  [R docs/build-spec.md:1187] is not met.
- Model card inside the table: §2.3.3 embeds `{hash, badge, evidence, validated_error_band,
  energy_verification}` [R docs/build-spec.md:289-290]; U-P1 item 7 lists "model_card hash"
  only [R docs/build-spec.md:1274-1275]; U-P19 reads "the table's model_card badge"
  [R docs/build-spec.md:2588-2589].
- `design_status`: uarch `proposed | reference` [R docs/build-spec.md:181]; the rk-sim draft
  ADR `shipping | proposed` [R rk-sim-side/decisions/DRAFT-admit-characterized-c2-tables.md:47].
  No document maps one onto the other.
- U-P15 asks for native predictions at "detail 0/0/0" [R docs/build-spec.md:2348]; no prompt
  builds native compute level 0 (U-P11 builds compute 1 [R docs/build-spec.md:2066-2077];
  U-P13 adds 2).
- No "six rules" or "two errors" text remains (grep over docs/, CLAUDE.md, rk-sim-side/, READMEs).

## 4. Coverage table

Formed before reading the earlier review. Counting rule: a split section counts once per part;
a row listing several sections counts once per section. Summaries, review questions and
exercises name no concept and are not rows. All `[R …]` below are `docs/build-spec.md` unless
another path is given. "Covered" = a prompt builds it and an acceptance test or a committed
output shows it.

**Counts (97 section-parts):** Covered **42** · Partial **14** · Gap **2** · Out of scope **3** ·
N/A **36**. Of the 61 parts that apply to a scratchpad NPU, 42 are Covered (69%), 14 Partial,
2 Gap and 3 excluded on purpose. Answer to question 1: **yes**, most of the book's applicable
concepts are covered.

| TOC | Status | Strongest evidence / note |
|---|---|---|
| 1.1 Role of performance modeling | Covered | The design study is the use case, with tests [R 2249-2250], [R 2286-2297] |
| 1.2.1–1.2.2 Analytical, TLM | Covered | Ladder [R 344-350]; U-C0 [R 1449-1457]; reservation calendars [R 2181-2186]; lax mode is a TLM-2.0 quantum [R 2453-2455] |
| 1.2.3 Cycle-accurate simulation | Partial | Top native level is cycle-approximate at tile granularity, O(1–10) events per job [R 2069-2070]; cycle-exact only as optional Gemmini RTL at L2 [R 1850-1851] |
| 1.3 Accuracy, speed, flexibility | Covered | Per-level error vs silicon [R 2400-2404], acceptance [R 2413]; speed factor pre-registered [R 2039-2040], [R 2094-2096] |
| 1.4.1, 1.4.5, 1.4.6 Toolkit, SCALE-Sim, supporting tools | Covered | SCALE-Sim v3 per dataflow at L2 [R 1848-1849]; BookSim 2, Ramulator 2 [R 1843-1847] |
| 1.4.2–1.4.4 ChampSim, gem5, Accel-Sim | N/A | CPU/GPU simulators |
| 2.1 Compute–memory balance | Covered | U-C0 aggregate and per-op [R 1449-1457]; `uarch characterize` OI per op [R 1463-1466], acceptance [R 1482-1483]; per-op roofline SVG [R 1546-1547] |
| 2.2 Bandwidth and latency | Covered | MLP bound at every level [R 352-356]; L1 latency-bound stream ±5% [R 1829-1831], mutant [R 1877-1878] |
| 2.3.1 ILP | Partial | Engines are separate owners and overlap at tile level [R 2057-2059], [R 2068-2069]; no instruction issue or VLIW model, issue is one constant per job [R 195] |
| 2.3.2–2.3.4 TLP, DLP, platform comparison | Covered | Multi-core policies [R 2200-2206], contention test [R 2225-2227]; array pipeline formula [R 1832-1833]; two reference classes [R 66-67] |
| 3.1 Generalization problem | Covered | Applicability vector [R 421-430]; scoped promotion tests [R 2008-2015] |
| 3.2.1, 3.2.3 Characterization, operational intensity | Covered | [R 1463-1466], [R 1482-1483] |
| 3.2.2, 3.2.4 HW counters, access patterns | Partial | Compiler-reported FLOPs/bytes and profiler zones stand in for counters [R 1985-1988], [R 2344-2347]; access patterns only as KV page gathers [R 324-326] and L2 traces [R 1847], not per op in `characterize` |
| 3.2.5 Clustering and visualization | Gap | Nothing; low value for a ~170-point grid [judgement] |
| 3.3.1 CPU benchmarks | N/A | |
| 3.3.2–3.3.4 Accelerator/cloud suites, limitations | Partial | A self-chosen versioned LLM suite [R 2282-2284]; no standard suite is named; workloads are dense decoders by scope [R 93] |
| 3.4 Practical workload selection | Covered | L3 shapes from `characterize` with coverage recorded [R 1916-1918]; suite with a reason per entry [R 2282-2284] |
| 4.1 From trace to statistics | Covered | Pipeline [R src/rkuarch/README.md:3-6]; end-to-end table test [R 1476-1478] |
| 4.2 Path of a memory access | Covered | DMA→NoC→MEM event kinds [R 466-467]; interleave test [R 2229-2230] |
| 5.1 What traces capture | Covered | Op graph / TaskGraph is the trace analogue [R 382-389]; graph-level `omissions` [R 1439-1443], tested [R 1480-1481] |
| 5.2 Choosing a collection approach | Covered | Generated from ModelSpec + ModelShape, never ONNX [R 1614-1618]; fidelity checked against compiler counts [R 1985-1988] |
| 5.3 Pin | N/A | |
| 5.4 ChampSim traces | N/A | |
| 5.5 Trace validation | Covered | FLOP parity from rk-sim's own code [R 1352-1358], [R 1369-1373], [R 1473]; workload-fidelity entries [R 2013] |
| 5.6 Trace organization | Covered | Canonical hashing [R 1050-1051]; vendor tamper test [R 1381-1382]; cache by request hash [R 2287] |
| 5.7.1 User–kernel gap | Covered | Analogue: host/runtime omitted [R 110-111]; device-side timing only [R 1924-1925] |
| 5.7.2 Wrong-path execution | N/A | No speculation |
| 6.1 Why sampling matters | Covered | Layer reuse and initial state [R 311-322]; errors tested [R 1798] |
| 6.2.1 Basic block vectors | N/A | |
| 6.2.2–6.2.6 Representative intervals, weights | Covered | One layer × n_layers as a weighted interval with measured error [R 311-316], [R 1773-1774]; visit-weighted LOO [R 1776-1778], [R 1801] |
| 6.3 Warm-up strategies | Partial | One priming iteration; cold-vs-steady measured [R 318-322], [R 1775]; warming length (6.3.3) is never checked — nothing compares one priming iteration with two |
| 6.4 Common pitfalls | Partial | Unweighted averaging and low-weight points handled [R 2293-2294], [R 1776-1778]; insufficient warming unchecked (6.3) |
| 7.1 Output structure | Covered | Report contents and tests [R 1535-1567] |
| 7.2 Throughput metrics, stall budget | Covered | Analogue: critical-path attribution sums to duration [R 398-400], L0 [R 1682]; utilisation diagnostics [R 275-277] |
| 7.3 Cache metrics | N/A | No caches; SRAM counters are the analogue [R 273] |
| 7.4 Branch predictor metrics | N/A | |
| 7.5 DRAM metrics | Covered | `dram_bw_util_ratio`, `dram_row_hit_ratio` [R 277]; interleave test [R 2229-2230] |
| 7.6 Comparative analysis | Covered | Normalised speedup and geomean [R 2264-2265], test [R 2293-2294] |
| 7.7 Sanity checks | Covered | L0 [R 1672-1686], mutants [R 1705-1710], L1 [R 1823-1841] |
| 8.1 Cache architecture | N/A | |
| 8.2 DRAM architecture | Covered | Organisation and timing as SourcedValues [R 205-208]; refresh-derated L1 check [R 1826-1828] |
| 8.3 Memory controller | Covered | Interleave, scheduler, page policy [R 203-204]; DRAM levels 1–2 [R 2187-2193]; test [R 2229-2230] |
| 8.4 Address translation | Out of scope | Declared omission [R 112] |
| 9.1–9.4 Cache/prefetcher sim (config, design, replacement, prefetchers) | N/A | Hardware caches and prefetchers; software prefetch by DMA is assessed at 16.4; the experimental-design template at 10.2 and 17.2 |
| 10.1 DRAM sim configuration | Covered | Ramulator 2 from the spec, never an unnamed preset [R 2187-2190]; fork test [R 1646-1647] |
| 10.2 Experimental design (template) | Covered | StudySpec [R 2252-2256]; thresholds written before experiments [R docs/execution-plan.md:231-232] |
| 10.3 DRAM timing | Covered | [R 1826-1828]; L0m latency monotonicity [R 1696] |
| 10.4 Row buffer management | Partial | Page policy in DRAM level 1 [R 2191-2192], row-hit diagnostic [R 277]; no test or study varies the page policy |
| 10.5 Adaptive row buffer management | Gap | Only `open` appears [R 204]; low value for streaming NPU traffic [judgement] |
| 11.1 Pipeline fundamentals | N/A | Array fill/drain is assessed at 16.2 |
| 11.2.1 Fetch and decode | Partial | Analogue: command issue on the control core = one constant `job_overhead_cycles` per tile job [R 195], measured by a launch-overhead class [R 1914-1915]; no issue queue or control-core contention |
| 11.2.2 Branch prediction | N/A | |
| 11.3 Out-of-order back end | N/A | |
| 11.4.2 MSHRs and MLP | Covered | [R 352-356], [R 1829-1831], [R 1877-1878] |
| 11.4.1, 11.4.3 LSQ, store buffer | N/A | |
| 11.5.1, 11.5.3, 11.5.4 Contention, interconnect, sync cost | Covered | [R 2225-2227]; NoC vs BookSim 2 [R 1843-1846]; barrier cost and sync class [R 2198-2199], [R 2338-2339] |
| 11.5.2 Cache coherence | Out of scope | Declared omission [R 112] |
| 12.1–12.5 gem5 O3 experiments | N/A | |
| 13.1, 13.2, 13.4 Ruby/MESI, design, false sharing | N/A | |
| 13.3 Multicore scaling | Covered | Blackhole matmul across 1/4/16/64 cores [R 2333-2334]; 32×32 variant [R 2215-2216] |
| 13.5 Synchronization cost | Covered | [R 2338-2339]; L0m [R 1696] |
| 14.1, 14.2, 14.4 SIMT, warp scheduling, occupancy | N/A | |
| 14.3.1–14.3.3 Shared mem/L1, L2/HBM, coalescing | N/A | GPU semantics; scratchpad and HBM assessed at 16.4 and 8.2 |
| 14.3.4 Asynchronous data movement | Covered | DMA engines with outstanding limits [R 193-194]; DMA/compute overlap [R 2068-2069] |
| 14.5.1, 14.5.2, 14.5.4 Divergence, uncoalesced, atomics | N/A | |
| 14.5.3 Bank conflicts | Partial | Built at compute level 2 [R 2194-2195] and reported [R 276]; no acceptance test shows a conflict biting (contrast the hotspot and interleave tests [R 2225-2230]) |
| 14.5.5 Execution throughput bottlenecks | Partial | Vector engine is one `ops_per_cycle` [R 191]; no per-operation throughput (exp vs add) for softmax |
| 15.1–15.4 Accel-Sim experiments | N/A | |
| 15.5 Latency tolerance | Covered | Analogue: latency-bound transfer class [R 2335-2336]; L1 [R 1829-1831] |
| 16.1 Case for tensor accelerators | Covered | Two proposed designs, two references [R 1410-1414] |
| 16.2 Systolic array | Covered | Pipeline formula [R 1832-1833]; SCALE-Sim [R 1848-1849]; MXU-fill shapes on silicon [R 1906-1907] |
| 16.3 Dataflow choices | Partial | Dataflow declared and checked [R 189], [R 1752-1754]; no named policy is anything but weight-stationary, and the WS-vs-OS study [R 2280-2281] cannot run (Finding 8) |
| 16.4 Accelerator memory hierarchy | Covered | Buffer placement and refusal [R 384-385], [R 1752-1756], test [R 1799-1800]; double buffering [R 2068-2069]; shared SRAM [R 2196-2198] |
| 16.5 Mapping and bottlenecks | Covered | Named policies [R 1742-1756], tile-count test [R 1797]; critical-path attribution [R 398-400]; regime diff [R 2262-2263] |
| 17.1 Simulator configuration | Covered | HardwareSpec and operators with per-operand layout [R 1223-1248], [R 338-339]; acceptance [R 1298-1301] |
| 17.2 Experimental design | Covered | [R 2252-2256] |
| 17.3 Dataflow comparison | Partial | As 16.3 [R 2280-2281] |
| 17.4 Array size and mapping efficiency | Partial | Array fill is a shape-regime axis [R 424-426]; silicon and L2 shape sweeps [R 1906-1907], [R 1848-1849]; array size cannot be a study variable [R 189], [R 2257] |
| 17.5 Sparsity | Out of scope | [R 108] |
| 18.1 Why model power | Covered | Energy per token with conditions [R 2268-2272]; L0 conservation [R 1683-1684]; tests [R 2296-2297] |
| 18.2–18.3 McPAT, AccelWattch | N/A | |
| 18.4 Looking further | Partial | The energy rung ends at L2, for SRAM pJ only [R 1854-1857]; MAC, NoC-hop, DRAM pJ and static power have no reference; board power is "coarse context" only [R 2393-2394] |

## 5. Disagreements with the earlier review

The earlier review rates Rev 1 at a finer granularity (164 concept rows against 97
section-parts here) [R docs/reviews/rk-uarch-book-coverage-review.md:36-47]. Most status
changes since then (2.2.2, 3.2.1, 8.2, 8.3, 11.4.2, 14.3.3 and others moving from Gap to
Covered) come from Rev 2 applying its F1–F17; those are not disagreements. Its status line's
"U0 is tagged `u00-end`" is confirmed by git; "CI is green on GitHub" cannot be checked from the
repo [R docs/reviews/rk-uarch-book-coverage-review.md:3]. The real differences:

1. **1.2.3 Cycle-accurate simulation: Covered there, Partial here. This review is right.** The
   earlier row cites "Level 2 (BookSim 2, Ramulator 2); level 3 reference (Gemmini RTL)"
   [R docs/reviews/rk-uarch-book-coverage-review.md:281]. But no prompt builds a cycle-accurate
   model: native compute stays at O(1–10) events per tensor job even at level 2
   [R docs/build-spec.md:2194-2196], BookSim 2 is only an L2 reference and U-P13 forbids a
   flit-level router of our own [R docs/build-spec.md:2185-2186], and Gemmini RTL is optional
   [R docs/build-spec.md:1850-1851].
2. **17.3 and 17.4: array-size and dataflow studies. This review is right that neither
   runs.** The earlier review says "Studies can vary array size"
   [R docs/reviews/rk-uarch-book-coverage-review.md:459] and that a dataflow field plus an
   example study closes 17.3 [R docs/reviews/rk-uarch-book-coverage-review.md:124-127]. The
   array is a plain int pair,
   `dataflows` a plain enum, and variants may change stipulations only
   [R docs/build-spec.md:189], [R docs/build-spec.md:217-219], [R docs/build-spec.md:2257]. The
   earlier review's own 9.1.2 row says the same ("StudySpec varies stipulations only")
   [R docs/reviews/rk-uarch-book-coverage-review.md:373] without drawing the consequence (Finding 9).
3. **F8 (demo reachability): treated as closed by Rev 2; still open here. This review is
   right.** The earlier review saw the risk
   [R docs/reviews/rk-uarch-book-coverage-review.md:141-155], but its fix (`characterize`-based
   shapes, decide BLOCKFP8 in U0001) leaves the proposed default "BLOCKFP8 does not cover fp8"
   [R docs/build-spec.md:429-430] and adds no end-to-end mesh class. It also counts Blackhole
   "multi-core" as end-to-end validation
   [R docs/reviews/rk-uarch-book-coverage-review.md:327], which U-P10's rule forbids
   [R docs/build-spec.md:1998-1999] (Finding 7).
4. **Where the pre-U4 risk lies.** The earlier verdict puts the weak side in the hardware
   description and says each contract field costs "one line each now"
   [R docs/reviews/rk-uarch-book-coverage-review.md:22-32]. Adding those fields was right, but
   this review finds the larger pre-U4 risks elsewhere: tp semantics, U2's missing oracle, the
   unlabelled fork levels and attention residency (Findings 1, 2, 5, 6), none of which it names,
   with evidence at each finding. On one point the earlier review was right and Rev 2 did not
   follow it: it proposed a structured `timing: {preset, source}` field
   [R docs/reviews/rk-uarch-book-coverage-review.md:498]; Rev 2 used free-text claim sources
   [R docs/build-spec.md:220-222] instead, and that is what makes U-P1's `UnnamedPreset` test
   unwritable (Finding 3).
5. **6.3 / 6.4.1 warm-up: its fix closes the gap; Partial here. This review is right.** Its
   fix, "simulate one priming iteration and report the second"
   [R docs/reviews/rk-uarch-book-coverage-review.md:73-76], is what Rev 2 adopted
   [R docs/build-spec.md:319-320]. Book 6.3.3 is about warming *length*, and the cold-vs-steady
   delta measures distance from cold, not convergence. Nothing checks that one priming
   iteration is enough.
6. **F11 energy rung: recommended there; defer or scope it here. This review is right.** An
   Accelergy/CACTI estimate checks SRAM pJ only [R docs/build-spec.md:1854-1857], but citing
   it fills `energy_verification`, which turns off the "unverified" label for all energy
   [R docs/build-spec.md:1527-1528]. Recommended in
   [R docs/reviews/rk-uarch-book-coverage-review.md:184-188], it verifies one coefficient
   family and relabels four.
7. **F9 shared SRAM: "decide now" there; defer here. Both have a case; deferral is cheaper.**
   Its concern (a study can't ask "per-core or shared SRAM?") is valid
   [R docs/reviews/rk-uarch-book-coverage-review.md:159-165]. But Rev 2 now builds two levels
   and a composite-rule case for a level that no example study varies and neither reference
   prompt asks for [R docs/build-spec.md:2196-2198], [R docs/build-spec.md:2231],
   [R docs/build-spec.md:2278-2281], [R docs/build-spec.md:2320-2326]. The earlier review's own fallback (declare it absent in
   "what this table does not claim") costs one line.
8. **Calendar: "Lane A (about 778 h) on the critical path, so about 39 weeks"
   [R docs/reviews/rk-uarch-book-coverage-review.md:34]; Rev 2 keeps that premise at 42 weeks.
   This review is right.** Sprints are gated on both lanes, so the calendar is Σ max(A, B) per
   sprint: 906 h realistic, about 45 weeks (§3.5).

Smaller status differences, where this review applies the prompt's definitions more strictly:
2.3.1 ILP and 14.5.5 throughput bottlenecks are Covered there and Partial here (no issue model;
one `ops_per_cycle` for every vector operation); 7.3 and 8.1 are Partial there and N/A here
(caches have no scratchpad counterpart); 10.5 is N/A there ("not a v1 goal") and Gap here,
because §1.3 does not exclude it.

## 6. Cannot verify from the repo

| Claim the plan depends on | Why it matters |
|---|---|
| ONNXim / PyTorchSim use BookSim 2 and Ramulator 2 internally by default; whether they offer "simple NoC / simple DRAM" modes; whether they model SRAM bank conflicts; what stats they emit (per-op timelines for critical-path attribution; a second iteration for `steady`); their LLM input formats; MIT licences [R docs/build-spec.md:1586-1588], [R docs/build-spec.md:1598-1599] | Decides whether G3's NoC L2 bound is a self-comparison, whether G5's "matched levels" exist, whether the U4 table can be C2 under the rule, and whether U-P5's attribution and `steady` are buildable (Finding 5) |
| Ramulator 2's External frontend works as a library, and its controller queue sizes and scheduler can be set from our spec [R docs/build-spec.md:2187-2190] | Finding 8; U-P18's backpressured boundary |
| BookSim 2 builds standalone with uniform-random, transpose and hotspot traffic; SCALE-Sim v3 supports each dataflow the specs declare; licences as listed [R docs/build-spec.md:522] | L2 rungs in U-P8 |
| Accelergy and Timeloop licences pass the allow-list; CACTI estimates are meaningful at 1.5–3 MB per core [R docs/build-spec.md:522], [R docs/build-spec.md:1854-1857] | Whether the energy rung exists at all |
| TPU v5e: MXU size and count, HBM capacity and bandwidth, int8/fp8 support, whether XLA can pin a layout (otherwise the `matched` group is empty), cost-analysis and profiler granularity, $1.20 per chip-hour [R docs/build-spec.md:1924-1926], [R docs/execution-plan.md:461] | Whether G4 can be evaluated per mapping-match group; how many reference fields are stubs |
| Blackhole p100a: whether it runs plain fp8 or only BLOCKFP8; two opposite-direction torus NoCs, 64-byte flits, ~9 cycles router-to-router; profiler limit of 125 zones per core and clock skew; Ubuntu 22.04 requirement; tt-smi power; ttsim coverage; $999 [R docs/build-spec.md:2311-2314], [R docs/build-spec.md:2344-2347], [R docs/execution-plan.md:462] | Finding 7 (fp8 coverage); the lookahead L; whether the kit can be dry-run |
| The Tensix core's in-core pipeline (unpack, math, pack, destination-register capacity) and its share of per-tile time | Whether Finding 8's missing operand and accumulator stage dominates the mesh L3 error [judgement] |
| rk-sim: `IterationCost`'s interface and `_time_s` dividing by tp; how its C0 counts attention bytes; its KV block size; ADR 0046's timeline export (the `visit_weights` shape); P16's baseline operator list; the Channel names [R docs/build-spec.md:1091-1096], [R docs/build-spec.md:254-255], [R docs/build-spec.md:335-340] | Findings 1, 2 and 6; U-P1's operator vocabulary; U-P19's tp rule |
| npu-m256 and npu-l4 HBM/GDDR capacities (not yet stipulated) against a whole 70B model at tp = 1 | Whether G3's bf16 table and the demo table raise `ResidencyExceedsCapacity` (Finding 1) |
| CI ran green on GitHub for `u00-end` [R docs/reviews/rk-uarch-book-coverage-review.md:3] | U0's exit criterion; only the workflow files and the tag are in the repo |
