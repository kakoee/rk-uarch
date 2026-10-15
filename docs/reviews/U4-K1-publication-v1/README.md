# K1 installation and KI-C1 formatting published

Javid approved the exact KI-C1 formatting exception. Local commit
`40831b8e0092fdc4e2836dc45c43be133830a647` wraps one parametrization decorator; its Python
AST is identical to the reviewed test. It preserves native installation
`63ca8bec5a4ac1d7dcf87290a5cf080c846de66d`. Normal merge
`fb7ba4a75d17650d91c2d2532460ccc1c16b5808` preserves the published documentation history.
That final source was checked, then separately pushed and verified on origin/main.

[Formatting receipt](formatting-commit.json), [merge receipt](source-merge.json), and
[publication/readback](publication.json) record the separate actions. No force push or
human-owned bypass occurred. Coordinator, A and B fast-forwarded with clean tracked/index
states; untracked reviewer/author packages were not staged or overwritten.

## Final installed-source checks

[Verification summary](verification.json) is newly executed against `fb7ba4a`, in the exact
accepted local image, offline. No new image, dependencies, server or registry action.

- **28 tests per mode**, with exact discovery/multiplicity validation; [debug](debug-tests.log)
  and [release](release-tests.log).
- [Six fresh replay payloads](replays.json) match expected SHA256 `4490d63c…`.
- [13 explicit linkage/guard checks](python-linkage.log) pass with actual fresh Cargo metadata.
- [Full-tree Ruff](final-ruff.log) and [strict currentness](final-currentness.log) pass.
- Container formatting, Clippy, licence/bans/sources checks, exact tool and lock/feature/
  checksum checks pass; [commands](commands.json) and [metadata binding](metadata-binding.json).
- [Source bytes/mtimes](completion.json) remained unchanged in the verification export.

The unmodified [full Cargo graph](cargo-metadata.full.json) and [Linux graph](cargo-metadata.linux.json)
are bound to the actual installed source. The work directory is recorded in verification.json.
Selected logs remove trailing whitespace/final empty lines only; raw hashes are in
[log-normalization.json](log-normalization.json). No full Python-suite rerun is claimed.

## Exact binding and retained fault evidence

[subject.json](subject.json) changes only the approved test-file hash plus explicit explanatory
metadata. All eleven other reviewed postimages, tool pins, lock, features, target and image
requirements are unchanged. [verify_installed.py](verify_installed.py) checks that exact
one-hash difference and byte-identical proposal inventory, then invokes B's unchanged helper
with its subject directory redirected. No historical B subject or review verdict is rewritten.
The old proposal tree remains a historical review reference, not the final installed tree.

The [completed fault campaign](../U4-K1-installed-verification-v1/README.md) remains attributed
to `63ca8be`: 22 intended semantic failures with 22 restored positives, generic-failure and
replay-drift controls, and two F5 faults with four positives. Git confirms the only non-review
change since that campaign is AST-identical Python test formatting. Native and dependency
bytes are identical. Those fault runs are retained evidence, not newly executed on `fb7ba4a`.

Raw completion/binding receipts still contain the old helper's unconditional
`fault_campaign_pending`/`reviewer_stage3_pending` fields. They are preserved rather than
rewritten: proposal Stage 3 was accepted, the earlier installed-source fault campaign passed,
and this run supplies fresh final-source metadata/tests. They do not assert remote or full
K1 qualification.

## B inventory reconciliation remains separate

[Concrete inventory candidate](inventory.candidate.json) identifies tested source `fb7ba4a`.
The live historical 19-test inventory has not been replaced. Send B the
[bounded reconciliation task](lane-B-inventory-reconciliation.txt) to verify the candidate and
prepare the exact live inventory/replay/fault-binding update for review. Do not manufacture a
new tested source identity or combine proposal, parent-fault and final-source results.

No K2 release, G3a/U4 closure, hosted/remote activation, performance qualification, tag or
infrastructure change. U0024 remains in force. GitHub CI was not waited on or polled.
