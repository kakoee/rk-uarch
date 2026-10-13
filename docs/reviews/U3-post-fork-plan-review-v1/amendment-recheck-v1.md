# Amendment recheck (v1): U3-plan-amendment-v1

Independent recheck for Javid and the coordinator, 2026-10-12.

**Verdict: NOT ACCEPTED for this exact amendment.**

- **Most of the amendment is right.** The direction is right, and the coordinator's
  qualifications are sound. The patch is mechanically exact, and the installer behaves as
  described.
- **Three defects need text corrections before human installation:**
  - Blackhole readiness is explicit but not executable. U-P15 also became self-contradictory.
  - Whether the controlled host and self-hosted nightly gate U7, G6 and U10 is
    contradictory.
  - U0023's supersession clause omits U0005 requirements that the amendment changes.
- **The fixes are small.** All three can be corrected without redesign, and a recheck of a
  revised package should be quick.

This is a review verdict only. It installs nothing, closes no gate and grants no authority.
No live worktree was modified, nothing was staged or committed, and nothing was generated.

## Scope and identities

| Item | Identity / result |
| --- | --- |
| Package commit (live HEAD, clean) | `451264bb422b38c12fd71a1c6c9e771e86e64bad`; it adds only 8 files under `docs/reviews/` |
| Declared baseline | `afb35022971e56703fe35104b818b8a226c039d7` (tree `b3dd42e`) |
| `plan.patch` | sha256 `12d5e17c…3c03ca`, matching `review.json` |
| My earlier report | Preserved byte-identical in the package (sha256 `34bc9a56…50a3`) |
| Read | Coordinator response; amendment README, `review.json`, `plan.patch`, proposed U0023, installer; artifact-dependency proposal. I also read the resulting amended documents in full where they changed, and re-read the unchanged related prompts (U-P16, P19) |

## Checks I executed

All checks ran in session scratch space. Nothing ran in a live worktree.

1. **Patch application.** In a private `git archive` export of `afb3502`, `git apply --check`
   and then `git apply` succeeded. All 24 paths match `review.json`'s before and after
   sha256 values, and no other file differs from the baseline export.
2. **Amended export:**
   - `tests/unit/test_prompt_sync.py`: 4 passed. This covers canonical prompts against
     build-spec §8 and both shipped rk-sim prompt mirrors.
   - `scripts/vendor_rk.py --check`: passed.
   - `git diff --no-index --check` over the 24 changed paths: clean.
3. **Embedded README copies.** Build-spec §4.0, §4.13 and §4.15 now equal the amended
   `CLAUDE.md`, `native/README.md` and `containers/README.md` byte for byte. Before the
   patch, two of these copies had drifted, so this is an improvement.
4. **Package commit export.** `vendor_rk.py --check` passed on an export of `451264b`, so
   committing the package does not break the CI `contract` job. In the amended plan, the
   G7 and G8 blocks are byte-identical and the G4 thresholds (≤25% median, no class above
   50%) are unchanged.
5. **Installer, in a disposable private clone of `451264b`:**
   - `--check` passed and left no changes.
   - Each guard refused as intended: `--commit` without `UARCH_HUMAN`, a wrong commit, and
     an untracked file present.
   - I ran a copy of the script with only its final `git commit`/`show`/`echo` lines
     removed. It staged exactly 24 paths, its own staged-byte check passed, and the staged
     bytes equal my independent export.
   - `scripts/hooks/human_owned.sh` passes with `UARCH_HUMAN=1` and blocks without it.
   - The script contains no push.
   - The clone was reset and deleted. No commit was created anywhere.
6. **Stale-statement sweep.** I grepped unchanged READMEs and prompts for runner and
   full-table statements, and for bare G3 references.

**Not run:** the full suite, mypy and ruff (Markdown-only patch); native builds; hosts,
runners, generation or adoption. I used the existing `.venv` interpreter directly, with no
`uv` sync or rebuild this time.

## Checklist results

| # | Check | Result |
| --- | --- | --- |
| 1 | PF-01 to PF-14 dispositioned | **Met.** Each finding maps to concrete text. PF-05 is explicitly deferred to the separate audit, with current enforcement retained, but has no milestone (R-7) |
| 2 | Coordinator qualifications sound and implemented | **Met.** Details below |
| 3 | Plan, gates, ADRs and prompts agree | **Mostly met.** Prompt sync is exact. Residual mismatches: R-1, R-2, R-3, R-4, R-6 |
| 4 | Full product tables in U7; silicon pass not a prerequisite | **Met** for silicon (U7 depends on G5 and its decisions; G3b states it). **Ambiguous** for host and runner (R-2) |
| 5 | U5 TPU and U8 Blackhole readiness explicit and executable | **TPU: met** (U-P8 readiness → U-P11b R → G3a → U-P9). **Blackhole: not met** (R-1) |
| 6 | Kernel/schema, correctness CI, performance host and nightly without contradictions | **Kernel/schema and correctness CI: met** (K1/K2 consistent across G2, U-P11a, U0023 and CLAUDE.md). **Host/nightly: contradictory** (R-2) |
| 7 | No accidental weakening | **Met in substance; see below.** The scope reductions are deliberate and consumer-justified, but the ADR record of them is incomplete (R-3) |
| 8 | Artifact proposal leaves U0002 enforcement unchanged | **Met.** The proposal is one Markdown file. The vendor check passes at baseline, amended export and package commit, and no bound path is in the patch |
| 9 | Installer applies only the reviewed patch; commit and push stay separate | **Met.** One sequencing caveat (R-8) |

Notes on item 7 (no weakening):

- G3's explicit derated-DRAM and latency-bound L1 sentence moved into G3a's "applicable
  independent L1". U-P8's acceptance tests 5 and 6 are unchanged.
- The 10% NoC bound remains in U-P8, G6 and U0005.
- The U-P6 and §5 checklist changes align with the accepted U0006 reductions. `not_run`
  still blocks whole-rung claims, and G2 now requires a consumer and deadline per case.
- The six U5 classes, ≥24 measurements, G7/G8, STUB rules and "no silent drops" are intact.
- The first table's precision and policy scope narrows from fp8+bf16 with both policies on
  npu-l4 to the npu-m256 FP8 demo. That is deliberate, but see R-3.

**Coordinator qualifications.** I accept all of them, and two correct my earlier report:

- My earlier report suggested a CI regenerate-and-compare check. That conflicts with U0002
  lifecycle step 7, which forbids generation in CI.
- My conclusion 3 said "every Python file in the repo". The binding actually covers three
  trees plus named inputs; PF-05 itself was precise.

The remaining qualifications are sound:

- No blanket acceptance of A's items.
- Pilot policy: no pilot now, with a future development-versus-held-out protocol.
- Ceiling ≠ forecast.
- The conformance test states its coverage.
- The 70% rule selects a hypothesis.
- Regression reruns are not duplication.
- No blanket analytic pause.
- The study path needs a point/table adapter.

The patch implements each of these in U0023, G4, U-P5, U-P6, U-P12 and U-P14.

## Residual problems

### R-1 · Medium · blocking — Blackhole readiness is explicit but no prompt can execute it

**Introduced in part by this amendment.**

- Execution-plan U8 Lane A says "Complete and verify Blackhole reference admission before the
  U-P15 freeze" (amended `docs/execution-plan.md:276`). U8's only Lane A prompt is U-P15.
- U-P15's new READINESS block (`docs/build-spec.md:3505-3512`) says admission must be done
  before the freeze and is "not permission to edit the engine while generating predictions".
  No other prompt owns Blackhole admission:
  - U-P8 (`:2632-2638`) only says "Repeat this readiness process", which means sourcing and
    identifying tasks.
  - U-P11b R is explicitly TPU-scoped (`:3019`).
  - U-P13a–d target npu-m256.
- What admission involves: Blackhole needs a torus, two opposite-direction NoCs, BLOCKFP8
  and GDDR6 admission, which is real engine work. By contrast, TPU has U-P11b R.
- **Regression.** U-P15 item 1 changed from "Complete" to "Verify the already admitted
  hw/references/blackhole-p100a.yaml" but still instructs "Fill the Rev-2 fields from the
  docs … otherwise stub them" (`docs/prompts/U-P15-…md:33-40`). It now asks the worker to
  verify a spec and also to complete it, while no prompt is assigned to create it.
- **Scenario.** A worker running U8 literally finds no admitted Blackhole support, and
  cannot add it in U-P15. They must stop with no assigned task to unblock them.
- **Minimum fix.** Add an explicit admission phase, either a Blackhole R phase or a U8
  admission phase separate from the freeze. Name who completes the reference YAML. Make
  U-P15 item 1 consistently either "verify" or "complete".
- **Same U8 consistency issue, also introduced here.** U-P15 made tt-npe optional, but
  U-P16 is unchanged. It still requires a tt-npe ledger source and a tt-npe-vs-silicon
  section (`docs/prompts/U-P16-…md:28,37`). Align U-P16 with "admitted matched scope, or
  retained not_run".

### R-2 · Medium · blocking — Contradictory host and nightly gating of U7, G6 and U10

- The G5 pass condition requires controlled-host time/memory, U0012 regression controls
  and an "executed applicable self-hosted nightly". It also says "Missing host/automation
  evidence leaves that qualification open; correctness work may continue" (amended
  `execution-plan.md:409-412`).
- G5's fail text (`:416-418`) says only a missing or failed **correctness** case "blocks
  G5/U7", while missing performance leaves qualification "pending".
- U7 "Depends on G5" (`:268`).
- U-P13d acceptance 5 (`build-spec.md:3384`) now requires controlled-host metrics, and that
  acceptance belongs to G6. U10 requires G6 + G3b.
- **Consequence.** One reading makes runner registration and host allocation de facto
  prerequisites for the first product table and for rk-sim integration. That contradicts
  the correctness/performance separation U0023 adopts. The other reading lets U7 start
  with G5 open, which contradicts "Depends on G5".
- **Minimum fix.** State which parts gate what:
  - **Option (a):** U7, G6 fidelity, G3b and U10 require G5 correctness only.
    Controlled-host metrics and nightly automation gate performance claims, U9 entry and
    U-P13d's scale-metric acceptance.
  - **Option (b):** state explicitly that host and runner readiness are prerequisites for
    U7.
- Javid's decision.

### R-3 · Low-Medium · blocking because the text is protected — U0023's supersession list is incomplete

- U0023 says it supersedes U0005's "full-table-before-silicon ordering, unconditional runner
  prerequisite, complete-M-before-kernel prerequisite and U6 full-table requirement"
  (`U0023:104-106`).
- Its decision items also change two U0005 requirements that the list does not name:
  - U0005 G2 "Complete U-P6's applicable analytic verification" (`U0005:60`), changed to
    consumer-assigned deadlines.
  - U0005 U4b/G3 "Deliver both mapping policies, all required operator and precision
    coverage" on the declared U4 grid (`U0005:67-68`), changed to the npu-m256 FP8 demo
    without mandatory bf16, second policy, npu-l4 or tp1.
- **Scenario.** A reader of the preserved U0005 text could hold G3b to fp8+bf16 with both
  policies.
- **Minimum fix.** Name both items in the supersession clause. The coordinator's own
  standard requires explicit supersession, and once human-installed this ADR is costly to
  amend.

### R-4 · Low — P18 test 2 versus the new admission check

- P18 still requires a test that prices a table "from rk-sim's own C0 closed form"
  (`rk-sim-side/prompts/P18-…md:93`).
- The loader now refuses non-C2 tables, and test 7 says C0 plumbing fixtures never gain
  C2 eligibility (`:106`).
- **Fix.** State that test 2 exercises cost and interpolation below the admission layer,
  so a literal worker is not tempted to relabel the C0 table as C2.

### R-5 · Low — G5's worker wording diverges from U-P11c

- G5 still says "workers 1/N determinism" (`execution-plan.md:409`).
- U-P11c says "batch workers 1/N where delivered. Full table workers are G3b"
  (`build-spec.md:3099`).
- **Fix.** Align the G5 wording with U-P11c.

### R-6 · Informational — stale statements outside the patch

- `docs/how-it-works.md:341` still cites "U3's Linux self-hosted runner" (U2-era text). The
  STANDING refresh will update it.
- `.github/workflows/ci.yml`'s native job installs an unpinned `cargo-deny`. U0023 requires
  pinned tools, so this is a B workflow task before K1 CI evidence counts. It is not a
  defect in this patch.

### R-7 · Low — the PF-05 audit has no milestone

The artifact proposal is correctly separate, but it has no deadline. M's protected carriers
under `contract/uarch_contract/` and every K2/B Python change are bound inputs. Recommend
completing the audit or decision before M's protected installation, or explicitly
budgeting the adoption cycles until then.

### R-8 · Low — installer sequencing against review records

- The installer refuses untracked files and requires HEAD to equal the commit the human
  types. This report is untracked until committed.
- Committing this report moves HEAD off `451264b`. Re-running with the new HEAD would pass,
  but the allowed-prefix check would then also permit edits under
  `docs/reviews/U3-plan-amendment-v1/`. The binding to the reviewed patch would then rest
  on the human.
- **Fix.** Before installing any revised package, either:
  - verify `git diff <reviewed-package> HEAD -- docs/reviews/U3-plan-amendment-v1/` is
    empty and the patch sha256 equals the reviewed value; or
  - have the installer pin the expected patch digest itself.

## Remaining human decisions

**On this amendment:**

1. Choose R-2's host/nightly gating policy.
2. Choose where Blackhole admission lives (R-1).
3. Confirm that the U0005 items in R-3 are superseded.
4. Choose the installation order relative to review records (R-8).
5. Set a milestone for the PF-05 audit (R-7).

**Unchanged and outside this amendment:**

- A's exact U0011, schemas, model conventions, toolchain and licence pins.
- Performance budgets, host allocation and runner registration.
- Hardware access and spend.
- The later FP8, ragged and npu-l4 decisions, and the PF-05 policy/migration.

## Handoff for the coordinator

```text
Amendment recheck v1 (docs/reviews/U3-post-fork-plan-review-v1/amendment-recheck-v1.md):
NOT ACCEPTED for package 451264b / plan.patch 12d5e17. Mechanics verified: patch applies to
afb3502 export, 24/24 hashes match, prompt-sync 4 passed, strict vendor check passes
(amended + package commit), installer guards and staging verified in a private clone
(no commit). Direction and coordinator qualifications accepted. Blocking text fixes:
R-1 Blackhole admission has no executing prompt; U-P15 item 1 says "verify already
admitted" yet "fill fields"; align U-P16 tt-npe. R-2 G5 pass includes host + self-hosted
nightly, U7 depends on G5, G5 fail says only correctness blocks U7, U-P13d accept 5 needs
controlled host for G6 -> state which parts gate U7/G6/G3b/U10 (Javid). R-3 U0023
supersession clause must name U0005 G2 analytic completion and U4b both-policies/precision
scope. Non-blocking: R-4 P18 test 2 below admission layer; R-5 G5 workers wording; R-7
PF-05 audit milestone; R-8 install from reviewed commit or verify package diff/digest.
```
