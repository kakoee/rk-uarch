# U3 plan amendment v2 — bounded review corrections

For Javid and the independent reviewer. **Ready for recheck, not live installation.**
This replaces the uninstalled v1 proposal at `451264b`. V1 and all prior reviewer and
coordinator text remain unchanged. Only the review package is being prepared/committed;
the installed plan remains the pre-amendment plan until a human installs accepted bytes.

- [Exact corrected patch](plan.patch)
- [Proposed U0023](proposed-U0023.md)
- [Exact paths, hashes, v1 target delta and checks](review.json)
- [Correction dispositions](response.md)
- [Guarded human installer](human-install.sh)
- [Independent recheck of v1](../U3-post-fork-plan-review-v1/amendment-recheck-v1.md)
- [Separate audit milestone](../U3-artifact-dependency-repair-proposal-v2/README.md)

Baseline: `451264bb422b38c12fd71a1c6c9e771e86e64bad`. It contains the v1 package but
has never installed its protected changes. This is a complete replacement patch against
that baseline, **not a patch to apply on top of a live v1 installation**.

The patch changes 29 Markdown paths, 18 of whose resulting contents differ from v1's
proposal. The remaining proposed files are byte-identical to v1. Five added-to-scope paths
are the new U-P15a task and the existing U-P16/U-P17/U-P18/U-P21 prompt corrections;
canonical and shipped copies are synchronized. No runtime/support bytes change.

## Javid's R-2 decision

> option 1, with conditions. Correctness should gate the U7 tables and U10 integration.
> Controlled-host performance and the self-hosted nightly stay open requirements for full
> G5, U9 entry, any performance claim and final closure.

The plan now names G5-correctness, G5-performance and G5-automation. Full G5 requires all
three. G5-correctness and the relevant fidelity/table tests gate U7/G6/G3b/U10. Host and
nightly obligations remain explicitly open if not done; they still block full G5/U6
closure, U9 entry, simulator-performance claims and final closure. Qualified host-speed
claims are distinct from explicitly unvalidated chip-duration predictions in tables.

Blackhole's assigned path is U-P16 S (B reference/sourcing/measurement feasibility) →
U-P15a (A native admission and independent tests) → U-P15 (separate prediction freeze) →
U-P16 M (authorized measurement). Source preparation has no card-access prerequisite.

## Checks

- Prompt synchronization: **4 passed**, including new U-P15a and shipped P18/P19 checks.
- Strict vendor currentness: passed on the amended private export; **97 bound support
  paths unchanged**.
- Clean-export application reconstructs all **29 target files** exactly.
- Patch whitespace passes; G7/G8 blocks unchanged and G4 numerical thresholds retained.
- No full suite, native build, measurement, artifact generation/adoption or independent
  recheck of these v2 bytes is claimed.

## Review and installation order

1. Commit this ordinary package and the v1 recheck report, preserving their bytes.
2. Ask the reviewer to recheck this exact package revision and patch digest.
3. Commit any new review report as ordinary documentation. Do not amend the reviewed
   package to add its verdict; that would change the package under review.
4. Only after acceptance, the human invokes the v2 helper with **the reviewed package
   commit and reviewed patch digest**, even if HEAD has advanced to commit review records.
   The helper requires that reviewed commit to be an ancestor, its package unchanged at
   HEAD, a clean worktree/index and unchanged target preimages. Unrelated lane commits
   require reconciliation rather than bypassing the guard.

Read-only preflight:

```bash
bash docs/reviews/U3-plan-amendment-v2/human-install.sh --check
```

The later human installation command has this form; do not execute placeholders:

```bash
UARCH_HUMAN=1 bash docs/reviews/U3-plan-amendment-v2/human-install.sh \
  --commit <REVIEWED_PACKAGE_COMMIT> c3b8beef81e223a852c48f1d59bfd40bf992e5e7a2151d440931cb89e9930e63
```

The exact digest is pinned inside the helper as well. Installation creates one local
protected documentation commit, using normal hooks, and never pushes. Commit, push and
lane runtime release remain separate. Do not run the superseded v1 installation command.
