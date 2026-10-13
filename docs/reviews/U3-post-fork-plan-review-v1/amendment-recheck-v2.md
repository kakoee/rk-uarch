# Amendment recheck (v2): U3-plan-amendment-v2

Independent recheck for Javid and the coordinator, 2026-10-12.

**Verdict: ACCEPTED for this exact amendment.** That means package commit
`607b3dc92625f203dddf24425b5938308ed69322` with `plan.patch` sha256
`c3b8beef81e223a852c48f1d59bfd40bf992e5e7a2151d440931cb89e9930e63`.

- **The earlier findings are fixed.** All three blocking findings from recheck v1 (R-1, R-2,
  R-3) are corrected in the resulting documents. The non-blocking R-4 to R-8 are corrected
  or recorded as required.
- **No new problems in protected files.** The patch introduces no new contradiction in
  protected text (CLAUDE.md, U0005, U0023).
- **Small non-blocking residuals remain.** They are listed below, all in unprotected prompts
  or in pre-existing text, and can be fixed by ordinary documentation commits before the
  affected tasks are commissioned.

This is a review verdict only. It does not install the amendment, release implementation,
close a gate or authorize hosts, runners, hardware or spending. No live worktree was
modified, nothing was staged or committed in the repository, and nothing was generated.

## Identities and preservation

| Item | Result |
| --- | --- |
| Live HEAD | `607b3dc` (clean). The package commit adds only 8 files under `docs/reviews/` and modifies none |
| Patch digest | Matches the reviewed value. It is pinned in `review.json` and inside the installer |
| Declared baseline | `451264b`, which contains the uninstalled v1 package. The v1 package files are unchanged |
| Earlier reports | Byte-identical to `review_inputs`: README `34bc9a56…`, coordinator response `005960c4…`, recheck v1 `5c2f6efb…` |

## Checks I executed

All checks ran in session scratch space. Nothing ran in a live worktree.

1. **Patch application.** In a private export of `451264b`, `git apply --check` and then
   `git apply` succeeded. All **29/29** before/after hashes match `review.json`, and no other
   file differs from the baseline.
2. **Delta from v1.** I also applied the v1 patch to an export of `afb3502`. Exactly **18**
   resulting files differ from v1, and they are the 18 paths declared in
   `changed_target_paths_since_v1`.
3. **Checks on the v2 export:**
   - `tests/unit/test_prompt_sync.py`: 4 passed. This covers the new U-P15a, all canonical
     §8 prompts and the shipped P18/P19 mirrors.
   - `scripts/vendor_rk.py --check`: passed, so U0002 enforcement is unchanged.
   - `git diff --no-index --check` over the 29 paths: clean.
   - The build-spec §4.0/§4.13/§4.15 copies equal CLAUDE.md and the native and containers
     READMEs.
   - The G7 and G8 blocks are byte-identical. The G4 thresholds (≤25% median, no class
     above 50%) are unchanged; only v1's fail-branch wording differs.
   - The patched U0023 is byte-identical to `proposed-U0023.md`.
4. **Installer, in a disposable private clone of `607b3dc`.** The clone was deleted
   afterwards. I removed the copy's final commit lines, so no install commit was made
   anywhere.
   - `--check` passed, with and without the reviewed commit and digest.
   - It refused each of these: wrong digest, missing commit, non-ancestor commit, and a
     missing `UARCH_HUMAN`.
   - **Advanced HEAD.** I added a synthetic review-only commit under the allowed review
     directory, then ran the staging path with `607b3dc` and the digest. Preflight passed,
     29 paths were staged, the staged bytes equal my independent export, and the script's
     own staged-byte check passed.
   - It refused a later commit that edits the package ("package changed since reviewed
     commit").
   - It refused an unrelated commit outside the allowed review directories.
   - It refused an uncommitted `review.json` edit ("live package differs from reviewed
     bytes").
   - The superseded **v1 installer refuses** on the v2 tree, because the v2 directories are
     outside its allowed paths.
5. **Sweep for leftover gating language.** I grepped for unqualified "G5" gating. All
   remaining uses either refer to full G5 or name its automation/correctness part
   consistently.

**Not run:** the full suite, mypy and ruff (Markdown-only patch); native builds; hosts,
runners, generation or adoption. I used the existing `.venv` interpreter directly.

## Disposition of recheck v1 findings

| v1 finding | Result in v2 documents |
| --- | --- |
| R-1 Blackhole not executable; U-P15 self-contradictory; tt-npe mismatch | **Resolved.** See the R-1 note below |
| R-2 Host/nightly gating contradictory | **Resolved per Javid's recorded option 1 with conditions.** See the R-2 note below |
| R-3 Incomplete supersession clause | **Resolved.** U0023:121-130 also names G2 analytic completion (now first-consumer deadlines and pass before reliance) and the old U4b scope (npu-l4 grid, both policies, FP8+BF16). It says G3b requires the declared npu-m256/70B/FP8/tp8 demo, and other variants are required at their declared consumers |
| R-4 P18 test 2 | **Resolved** in the shipped and canonical copies. The test runs at the cost/interpolation unit boundary. The C0 fixture keeps C0, the production loader refuses it, and test 7 covers admission |
| R-5 G5 worker wording | **Resolved.** G5-correctness says batch workers 1/N where delivered; full-table workers are G3b |
| R-6 Stale notes / unpinned cargo-deny | **Recorded.** U-P11a now requires B to pin the CI toolchain and cargo-deny before K1 CI evidence counts. The `how-it-works.md` U2 text stays until the standing refresh |
| R-7 PF-05 audit milestone | **Resolved.** U0023:115-119 and the audit supplement set the deadline: before M's protected carrier installation, either the audit decision or Javid's recorded choice to keep enforcement and budget M/K2/B adoption cycles |
| R-8 Installer binding | **Resolved.** The digest is pinned in the script. The reviewed commit must be an ancestor, the package unchanged since it, and live package bytes equal to it. Verified above |

**R-1 in detail.** Each Blackhole phase now has an owner:

- **U-P16 S** (B, no card needed) completes the reference YAML and the feasibility work.
- **U-P15a** (A, new) implements and tests admission, and must stop on missing reference
  or contract decisions.
- **U-P15** verifies and freezes only; item 1 now says "do not fill or alter the reference".
- **U-P16 M** measures after the freeze, with hardware access approved.

The plan's serial row, U8 lane rows, prompt index and U0023 item 4 all agree. U-P15 and
U-P16 agree that tt-npe is optional: it is used only within a prospectively admitted matched
scope, and absent cases stay `not_run`.

**R-2 in detail.** The plan records **G5-correctness, G5-performance and G5-automation**
separately. Only correctness gates U7, G6, G3b and U10, together with each one's own tests;
missing or failed correctness blocks them.

Full G5 needs all three parts. It is required for U9 entry (including the funded-experiment
route, as Javid's decision text specifies), for any simulator-performance claim, for final
closure (G10 and U-P21) and for U6 closure.

My six conditions are each met:

1. G5-correctness includes independent review.
2. Nightly-marked correctness suites must still run explicitly.
3. U-P13d's acceptance is split into acceptance 5 (functional scale points) and acceptance 6
   (scale metrics), and acceptance 6 explicitly does not gate G6, G3b or U10.
4. Long runs need authorized capacity, not a specific runner.
5. Host observations are provisional until host evidence and the nightly both exist.
6. Proceeding never closes U6 or full G5.

## Non-blocking residuals

These are all unprotected prompt text, or pre-existing. Fix them before commissioning the
affected task.

- **N-1 · Low — No B phase owns Blackhole's independent cases.** U-P15a says "B supplies
  independent expected counts/timing/behavior and public-boundary faults". Neither U-P16 S nor
  U-P12 assigns this for Blackhole; U-P12 covers U4, U6 and G3a. Add the work to U-P16 S or
  extend U-P12 before U-P15a is commissioned.
- **N-2 · Low, pre-existing — Where SUITE.md gets signed.** G3a and the U8 rows treat the
  suite as signed before the freeze, and admission scope depends on it. U-P9 item 1 and
  U-P15 item 2 still say to agree the suite "FIRST" inside the freeze sessions. Recommend:
  - sign at the end of readiness (TPU readiness in U-P8/R; Blackhole in U-P16 S, jointly
    with A);
  - turn the freeze prompts into verification of the signed suite.
- **N-3 · Low, pre-existing — 32×32 functional points.** U-P13d acceptance 5 depends on an
  accepted 32×32 design that no task produces. It also doesn't say whether it gates G6.
  State that it serves U9 scale evidence and does not gate G6, G3b or U10 unless a design
  is accepted, or assign the design.
- **N-4 · Cosmetic.** For a non-ancestor commit, the installer refuses with a Python
  traceback rather than a STOP message.
- **N-5 · Informational, carried over.** The `how-it-works.md:341` U2-era runner text, and
  the unpinned CI `cargo-deny` (now an explicit K1 prerequisite).
- **Inherent limit.** The installer verifies the package's data files against the reviewed
  commit, but it cannot protect against a modified copy of itself being executed. Run it
  from an unmodified checkout.

## Remaining human decisions and steps

1. **Install, if Javid chooses.** Committing this report under
   `docs/reviews/U3-post-fork-plan-review-v1/` as ordinary documentation keeps the installer
   preflight valid. Then:
   `UARCH_HUMAN=1 bash docs/reviews/U3-plan-amendment-v2/human-install.sh --commit 607b3dc92625f203dddf24425b5938308ed69322 c3b8beef81e223a852c48f1d59bfd40bf992e5e7a2151d440931cb89e9930e63`.
   Push stays separate.
2. **Unchanged, and outside this amendment:**
   - A's exact U0011, the M schema and model conventions;
   - toolchain and licence pins;
   - performance budgets, host allocation and runner registration;
   - hardware access and spend;
   - the PF-05 audit decision before M's install;
   - the later FP8, ragged and npu-l4 decisions.

## Handoff for the coordinator

```text
Amendment recheck v2 (docs/reviews/U3-post-fork-plan-review-v1/amendment-recheck-v2.md):
ACCEPTED for package 607b3dc / plan.patch c3b8beef. Verified: 29/29 hashes on 451264b
export; 18 paths differ from v1 exactly as declared; prompt-sync 4 passed; strict vendor
check passes; G7/G8 identical, G4 thresholds unchanged; installer guards, advanced-HEAD
review-only commit, package-edit/unrelated-commit/uncommitted-edit refusals and staged
bytes verified in a private clone (no commit); v1 installer refuses on v2 tree. R-1..R-8
resolved/recorded; Javid's R-2 option 1 conditions implemented. Non-blocking (unprotected
prompts): N-1 B independent cases for U-P15a unowned; N-2 sign SUITE.md at readiness, not
inside freeze prompts; N-3 32x32 functional points/design ownership; N-4 traceback on
non-ancestor commit. Review verdict only; installation remains Javid's human step.
```
