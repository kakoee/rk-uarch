# K1 Stage 2 — B guard, inventory and replay reconciliation

**Owned proposal only. A's two patches remain unapplied.** B started from integrated main
`eb99399b96b1271a097aa9f635510f84622bf8dc`; [later peer integration](integration.json)
preserves separately published adoption documentation. AD-M1/adoption is a separate workstream.
No A proposal bytes need changing. The primary patch followed by A's separate B guard
proposal reproduces the coordinator's exact twelve-path tree:
`6d5263e13e43a5dfb44d8addf93cc47cc814a0ac`, on base
`9b1408437b6dc08d9b77848f5fffe56c0cf1db72`.

[subject.json](subject.json) binds all twelve postimages, the lock, tool package and accepted
local image. Primary patch SHA256:
`9897cb1407d26412bcea76e8e8a5a353c508b4d0ce5ca236efa8fb6b66cabfad`;
B guard patch SHA256:
`7bf806d04280f0ac66e37bfe0d292207e9a17b6e615b952a868ccb4e8afcc57e`.
A's package and the coordinator identity agree. This tree is a review subject, **not an
installed source commit**. B confirms the exact guard proposal for coordinator reconciliation;
this is not the independent Stage 3 verdict or permission to apply it.

## Newly executed evidence

[Audit and commands](verification.json), [reproducer](audit.py): a private export applied
both patches in order, verified every primary postimage and the full twelve-path Git tree.
All 1,962 exported source files retained bytes/mtimes through checks. The private export was
removed; all 134 files of A's uncommitted package remained unchanged.

- **12 Python checks passed**: licence register, README boundary and the proposed chain guard.
- Chain refused missing first/second patches, extra patch, swapped numbered-patch contents,
  tampered first/second patches and disconnected hashes. Attempting reverse 0001 before 0002,
  or forward 0002 before 0001, also refused.
- Correct reverse 0002 → 0001 recovered the original register preimage; forward 0001 → 0002
  verified both intermediate hashes and returned the exact proposed register.
- **35 host Python controls passed**, covering source/selection failures, replay completeness,
  tool/cache/metadata guards, scratch restoration and post-install identity preconditions.
  These are host/synthetic controls, not native fault executions. [Receipt](host-controls.json).
- The initial combined host-test launch failed collection because the historical test imports
  `ci_guard` by basename. The corrected launch adds that exact module directory explicitly,
  asserts its origin and leaves PYTHONPATH/MYPYPATH unset. Both logs are retained; no pass is
  credited to the failed collection. Final owned Python Ruff and whitespace checks passed.

The original first-patch record remains byte-identical, SHA256
`50b7545173b41140ea896ff46a562babd913083b73f76113503cfeb05a407e8f`.
Patch 0001 remains `c7ddd4456180a0338afd20908dac12275ad648505aef0abd690a9b953b70834e`.
Neither historical evidence nor the live 19-test inventory was overwritten.

## Reconciled proposal and retained inherited results

[inventory.proposed.json](inventory.proposed.json) records **28 distinct names, multiplicity
one in debug and release**. The old 19 names remain; nine are added. The proposal has an
explicit base/patch/tree identity and no `source_commit` field. A's null field is not treated
as a source identity. [Exact delta](inventory-delta.json) and [saved input hashes](inherited-inputs.json) preserve
that provenance. Saved listings and full-run logs match the 28-name counters; the guards
refuse the old19, missing, extra and duplicate selections.

Replay test and prefix remain `tests::canonical_replay_private_bytes` and
`UARCH_K1_REPLAY_V1=`; the sink remains `UARCH_K1_REPLAY_OUT`. The six saved debug/release logs
contain identical payload bytes with SHA256
`4490d63cd5b49bac327ded1661df7802356f541e003391666963965809f2a62a`.
The historical `30c1e070…` payload is preserved and must not be used as the new expected bytes.
The changed private predecessor field and addressed dispatch records explain this deliberate
payload change; this receipt does not adjudicate F3/F4 semantics.

[faults.proposed.json](faults.proposed.json) binds A's eleven current source mutations to their
actual file hashes, unique anchors and selected test names. All 66 saved runs were checked:
22 intended failures with their diagnostics and 44 baseline/restored passes. These are **A's
inherited Rust executions**, not B reruns. [Replay mutation](replay-mutation.proposed.json)
updates only the source hash for B's existing release-only whitespace fault; its exact
replacement and selected test are unchanged. [Control reconciliation](controls.md) explains
which old driver assumptions must not be reused unchanged.

## Restored Docker access: newly executed local evidence

The initial [Docker refusal](availability.json) is retained. After the user's access restoration,
[actual image inspection](native-availability.json) found the exact accepted final image
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`, Linux/amd64.
No image was pulled or built. [Native reproducer](native_check.py) exports the exact base,
applies the same two patches, verifies the twelve-path tree, then runs the accepted tools
with network disabled, read-only source and private outputs. This is proposal execution,
not an installed-source identity or native qualification.

The real image checks passed tool version comparison, lock/features/registry/checksums,
27 cached archives and notices, full 27-package versus Linux-selected 26-package discovery,
fmt, clippy and accepted cargo-deny policy. Both full suites passed all **28 names once**;
six fresh replay processes reproduced the exact `4490d63c…` payload. Tool versions and exact
metadata commands are in [native-metadata-binding.json](native-metadata-binding.json).
The raw [full graph](cargo-metadata.full.json) and [Linux graph](cargo-metadata.linux.json)
are actual unmodified Cargo output, bound to source, lock, all-features, target and image.

The explicit host selection passed **13 tests**, including both functions in
`native/test_register_linkage.py`, with `K1_METADATA` set to that run's full graph,
PYTHONPATH/MYPYPATH unset and explicit pytest config/root. [Log](native-python-linkage.log).
[F5 controls](linkage-controls.json) additionally ran A's exact register and README mutations
in the first independently verified export: two intended assertion failures and four passing
baseline/restored checks, with module origins checked and all source bytes/mtimes restored.
Those are host Python checks over genuine native metadata, not Rust test executions.

The first native run passed verification but B's new collector then expected the wrong receipt
filename (`metadata-full.exit` instead of the existing command JSON's `exit` field).
[Failure receipt](native-collector-initial-failure.json). The corrected collector repeated
verification in a fresh export. The first export's successful real metadata was retained for
F5 controls; the second export is used for the native campaign. No native source repair was
made to accommodate the collector.


The second run completed nine semantic faults in both modes with individual fresh-build
restorations, then refused the tenth diagnostic: A supplies literal `Ok(1)` while the old
B driver consumes a regex. [Exact partial campaign and refusal](native-prefix-campaign.json)
preserve the actual intended Rust failure and successful source restoration. The owned
adapter now escapes literal diagnostics before that unchanged consumer, and also requires
exit101, the exact selected FAILED row, a one-failure summary and mode-specific owner
messages. It does not change A's source, patches, anchors or literal expectations. The
remaining two cases are run in a fresh export with `--fault-start 9`; this is an explicit
suffix campaign, not a claim that a single uninterrupted eleven-case run passed.

[Combined native summary](native-summary.json) now confirms **22 intended exit101 failures
and 22 individual restored positives**, covering all eleven semantic cases in both modes.
The baseline is the full 28-test suite in each mode. The generic campaign also refused
missing source, real compiler/runtime faults, empty/ignored/filtered execution, absent offline
cache, unavailable toolchain and the unexcepted Unicode policy. Release-only payload drift
was refused while its Rust test passed; restoration recovered the exact expected bytes.
All 1,962 source files passed verification isolation, and each fault campaign restored bytes
and mtimes. [Exact suffix commands](native-commands.json), [prefix evidence](native-prefix-campaign.json),
[cache archive checksums](native-cache-archives.stdout), [cache notices](native-cache-notices.stdout)
and the [actual canonical payload](native-replay.canonical) are retained. Raw command output
is byte-preserved, including pytest trailing whitespace and Cargo final blank lines; the
whitespace check excludes those raw logs. Owned Python lint/format and other diff whitespace
checks pass. No inherited native
result is counted as one of these new runs.

The proposal helpers always create or explicitly validate a private export and use metadata
from that run. Recorded `/tmp` paths identify retained historical receipts, not a future test
prerequisite. Recreate the graph with the accepted image for each later source identity.
No test depends on A's missing temporary metadata file.

[Post-install procedure](post-install.md) and [proposal helper](post_install.py) require a
real separately authorized installed commit, regenerate its metadata and explicitly invoke
the otherwise-undiscovered manual test. They produce only a reviewable inventory candidate.
Their complete installed-commit entry point has not run: no such installation is claimed.
The underlying image verification, discovery, metadata linkage and fault mechanisms have
now been exercised on the exact proposal export; pre-install identity refusals also passed.

**Stop for coordinator reconciliation.** Preserve this exact twelve-path binding for the
same reviewer's Stage 3. Any later source/guard delta needs a new tree binding; this package
proposes none to A's bytes. F1 and the disclosed F3/F4 probe disagreements remain for that
reviewer. Installation, real post-install inventory, remote qualification, K2 and closure
remain separate. Frozen A, live native/protected files, the saved candidate and artifact
bindings were untouched. No hosted CI was polled.
