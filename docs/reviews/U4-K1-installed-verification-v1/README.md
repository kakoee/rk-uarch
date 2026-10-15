# K1 installed-source verification — publication held on KI-C1

The exact approved twelve-file proposal is locally installed in A as
`63ca8bec5a4ac1d7dcf87290a5cf080c846de66d`, tree
`894dc89858e65a2bf3929bd1a43e856df9827b4d`. All reviewed postimages match; A's nine paths
and B's three guard paths traveled in one normal commit. [Installation receipt](local-installation.json).
No protected-file bypass, artifact generation/adoption, live inventory replacement or push
of this source commit occurred. A remains clean at this commit.

**One blocker: KI-C1.** Full-tree Ruff refuses one 106-character parametrization line in
`tests/unit/test_third_party_patch_check.py` ([actual diagnostic](installed-ruff.log)).
The reviewed Rust and Python checks pass, but hosted lint would fail. The approval required
reconciliation before changing any reviewed byte, so the installed source is untouched.
[Exact unapplied correction](KI-C1-formatting.patch) only wraps that decorator. Python ASTs
are identical; [full lint](KI-C1-ruff.log) and [all eight affected tests](KI-C1-guards.log)
pass in a separate disposable preview. [Decision and precise hash exception](next-decision.md).

## Newly executed on the actual installed commit

B's unchanged `post_install.py` archived this real commit, inspected the exact existing
local image `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`,
and ran offline with read-only source mounts, private build outputs and no image pull/build.
The [metadata binding](metadata-binding.json), unmodified [full graph](cargo-metadata.full.json)
and [Linux graph](cargo-metadata.linux.json) identify this installed source and accepted tools.

- Full debug and release runs: **28 tests each**, exact names/multiplicities verified.
- [Six fresh replays](replays.json): exact expected `4490d63c…` bytes.
- Explicit metadata-fed [linkage and guard tests](python-linkage.log): **13 passed**.
- Formatting, Clippy and accepted licence/bans/sources checks passed through the container
  checks stage; full versions, lock/features/checksums and discovery guards passed.
- [Strict artifact currentness](installed-currentness.log) passed on the real A checkout.
- [Inventory candidate](inventory.candidate.json) identifies this commit; it is not installed.

The [commands](post-install-commands.json) and [raw completion receipt](post-install-completion.json)
are preserved. That old helper emits `fault_campaign_pending` and `reviewer_stage3_pending`
flags unconditionally. They describe its limited entry point, not the subsequently executed
campaign or the already accepted proposal review. Its "Nothing installed" message means
that evidence helper made no installation; the earlier local source commit is real.

## Installed-source fault and restoration campaign

[Coordinator adapter](installed_faults.py) uses B's reviewed functions against a separate
archive of the **same installed commit**, not the old proposal export. It reuses the accepted
seeded container and verification functions to generate the old driver's actual predecessor
receipts. It then uses B's explicit fault anchors, literal-to-regex adapter, stronger exit101/
selected-test/diagnostic checks and redirected replay input. No historical source/controller
is edited. F5 reuses B's existing code with only its output/config destination redirected to
private receipts. These adapter changes and installed binding are explicit, not a claim that
B's historical proposal launcher ran unchanged against an installed commit.

The independent fault export first passed its full baseline verification. The campaign then
completed without a restart:

- **22 intended semantic failures**: eleven faults in both modes, each followed by its own
  passing fresh-target restoration. [Source-bound command receipts](fault-command-receipts.json).
- Missing source, actual compiler/runtime failure, empty/ignored/filtered selection,
  unavailable offline cache/toolchain and unexcepted Unicode-policy refusals all passed.
- Release-only canonical drift was refused and restored to the expected bytes.
- **Two F5 intended assertion failures and four baseline/restored positives**, using genuine
  fresh Cargo metadata. [F5 controls](F5-controls.json).
- [Baseline isolation](fault-baseline-isolation.json) and [campaign restoration](fault-controls.json)
  confirm preserved source bytes/mtimes. [Installed binding](fault-installed-source.json) and
  [completion](fault-completion.json) retain actual source/image identities.

Full raw logs and private build outputs remain in the two work directories listed in
[summary.json](summary.json); only selected evidence and command/log hashes are published.
No whole source tree or build directory is copied into Git. Selected text logs remove trailing
whitespace only; raw graphs and JSON receipts are preserved. Tests and fault-run counts are
not combined into an inflated unique-test total. The full Python suite was not rerun.

## Remaining steps

Approve the bounded formatting delta; commit it separately; regenerate installed metadata
and the candidate inventory using the one approved hash exception; publish separately after
checks pass. B then reconciles the final source-bound inventory, replay and fault anchors for
review before the historical 19-test inventory is replaced. The Rust fault evidence remains
attributed to its exact commit even if later test formatting is AST-identical.

No K2 release, K1/G3a/U4 closure, remote/hosted activation, performance qualification, server
or registry action, or tag. U0024 remains in force. GitHub CI was not polled.
