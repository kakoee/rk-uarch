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

## Reconciled proposal, with inherited native results

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

## Missing execution prerequisite and concrete next procedure

[Availability](availability.json): the Docker command resolves to the Windows integration
stub and exits 1, reporting Docker unavailable in this WSL distro. No runtime was activated,
image pulled/built, dependency installed or infrastructure changed. The accepted local image
remains `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
A's Rust results and tools/image receipts are inherited. No current native qualification is
claimed.

The actual full `cargo metadata --locked --offline --all-features --format-version 1` output
needed by `native/test_register_linkage.py` was not delivered and could not be reconstructed
without the accepted runtime. `linkage-roles.json` and tree text are not substitutes for that
resolved graph. The manual linkage test is **not newly executed** here.

[Post-install procedure](post-install.md) and [proposal helper](post_install.py) generate fresh,
retained full/target metadata, check actual source/lock/features/tool bindings, and explicitly
invoke the otherwise-undiscovered manual test with `K1_METADATA` pointing to that run's full
metadata receipt. They create an inventory candidate bound to a real installed commit; they
never install an inventory or activate CI. Their native execution path remains untested until
the exact local image is available. Pre-install refusals and Python syntax/lint were tested.

**Stop for coordinator reconciliation.** Preserve this exact twelve-path binding for the
same reviewer's Stage 3. Any later source/guard delta needs a new tree binding; this package
proposes none to A's bytes. F1 and the disclosed F3/F4 probe disagreements remain for that
reviewer. Installation, real post-install inventory, native re-execution, manual linkage,
remote qualification, K2 and closure remain separate. This work did not change frozen A, live native/protected files,
the saved candidate or artifact bindings. No hosted CI was polled.
