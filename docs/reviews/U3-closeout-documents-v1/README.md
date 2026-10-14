# U3 closeout documentation package

Javid approved the detailed design and dependency policy for **U3 closeout only**.
[Approval](../U3-reviewed-design-and-policy-v1/acceptance.md) excludes U4 authorization.
This is the original installation package. The human has since installed all five exact
postimages, and the coordinator has installed the fresh narrative. See the
[current commit preparation](../U3-final-local-checkpoint-v1/README.md). The installation
instructions and preparation checks below are retained as their original scope.

- [Exact patch](closeout.patch), SHA256 `2b0bc1934020e1d0da2d21ab3514d26c1595a780d3d539b300f79a05286d9416`.
- [Targets/preimages/postimages](review.json) and readable [proposed files](proposed/).
- [Closeout record](../U3-closeout.md), with publication gates still pending.
- [Fresh documentation session prompt](fresh-documentation-session.txt).

The five targets are U0011, a prospective U0002 addendum, build-spec, execution-plan and
U-P6. The prompt text and build-spec copy are synchronized. Current source/artifact
currentness, protected schema bytes and runtime code do not change. The U0002 code repair
stays unapplied; its migration belongs to separately authorized future work. U0011's
numeric host/performance limits remain proposals, not accepted budgets.

## Human installation, separate from commit and push

From the main rk-uarch folder, check the exact package:

```sh
python3 docs/reviews/U3-closeout-documents-v1/human-install.py --check \
  --expected-head 7afba9b16d954fd46684711764cb3718170e53aa \
  --patch-sha256 2b0bc1934020e1d0da2d21ab3514d26c1595a780d3d539b300f79a05286d9416
```

After reviewing the five-file patch, the human installs it by changing `--check` to
`--apply` and setting `UARCH_HUMAN=1` on that invocation. Agents do not set that variable.
The helper verifies HEAD, branch, empty index/clean tracked worktree, exact patch identity,
path selection and all preimages. Untracked reviewer/coordinator files are preserved and
not staged. It applies only the documentation and verifies exact postimages.

It **does not stage, commit, push or tag**. Return the receipt; coordinator reconciles the
selected closeout contents and prepares the separate human commit. If HEAD or any target
changed, it stops rather than overwriting. The `--verify` mode checks installed postimages.
No request to approve the design/policy again is needed; this is the separate protected
installation step required by CLAUDE.md. U4 remains unauthorized.

## Outstanding work after this package

The fresh documentation session must return its proposal; selected reviewer evidence must
be made durably publishable without editing reviewer bytes or committing interpreter
caches. Then finalize the closeout selection, integrated checks and separate commit/push,
followed by fresh hosted/local same-commit validation and human tag/closure. No full suite,
CI, cold clone or completed sprint is claimed by preparing this patch.

## Coordinator verification

The private export plus exact five-file patch and provisional publication selection passes:
four prompt-sync tests, all-tree Ruff, strict current vendor verification and schema
freshness. Local link targets verified; exact before/after hashes match. The helper passes
check-only mode and refuses wrong digest, wrong HEAD and a nonhuman apply invocation.
See [validation](validation.json), [installer checks](installer-checks.json) and [links](checks/links.txt).
No protected live file changed. Full suite, hosted CI and fresh-clone closure validation
remain pending on the eventual published selection.

Immutable review probe source is selected as byte-identical `.py.txt` with per-directory
replay instructions; original `.py` files and reviewer bytes stay untouched locally.
See [evidence publication mapping](evidence-publication.json). No new lint exemption or
review-result rewrite is introduced. The provisional path list is for review, not a command
to stage everything; final documentation and this verification material must be included
when preparing the exact final commit selection.
