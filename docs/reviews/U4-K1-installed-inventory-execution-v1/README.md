# Installed K1 inventory: execution receipt

Javid approved [U4-K1-installed-inventory-v1](../U4-K1-inventory-reconciliation-v1/next-decision.md)
with “yes”. The exact two-path patch was installed, committed locally with normal hooks,
then pushed in a separate action. Remote main was verified at
`1351d2977c682026d61fb42e4db7397a0004f256`.

The live inventory now records 28 tests per mode and canonical replay
`4490d63cd5b49bac327ded1661df7802356f541e003391666963965809f2a62a`.
The separate controls binding retains fault evidence at `63ca8be`; the final test and
replay evidence remains at `fb7ba4a`. The configuration commit is not a new native test run.
Historical bindings and receipts remain available unchanged in Git.

Executed checks: exact patch/preimage/postimage hashes, byte equality with both reviewed
candidates, saved-evidence audit, 35 passing host guard tests and whitespace checks.
Other tracked paths and all pre-existing untracked reviewer/author files were preserved.
The tracked worktree and index were clean after publication. See [receipt.json](receipt.json).

No full suite or native campaign was rerun. No hosted workflow was activated and CI was
not polled. The controls file remains passive data for explicitly verified consumers.
K2 implementation/release, remote/performance qualification and G3a/U4 closure remain
separate. This completes the approved installed-inventory reconciliation.
