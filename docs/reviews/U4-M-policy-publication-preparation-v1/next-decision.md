# U4-M-policy-publication-v1

**HOLD — not ready to request publication approval.**

The human adoption checkpoint is verified, but the combined integration tree fails an
existing relocation test (PUB-C1). See [the handoff](README.md) and the
[bounded B correction task](lane-B-lifecycle-test-followup.txt).

The intended publication includes source installation
`0cf24d91eeca5cc45182eb6fb03202677fd97dcb` and adoption
`5e774682a7abdc21aa0bac6a8f738e66c852d3e5`. It changes 41 paths against the tested
published main: source32 plus adoption10, with one overlapping path. No publication
approval is requested until the correction has been reconciled and checked.

The proposed integration direction remains merging published review documentation into A
with normal hooks, then an ordinary fast-forward push preserving the human commits. Any
additional test correction must be recorded and reviewed explicitly. Fetch and inspect peer
work before publication; new implementation/configuration changes require reconciliation.
Preserve untracked reviewer/author packages. Never force-push or bypass human-owned hooks.

Publication, K1 acceptance, K2 release and U4 closure remain separate. No new generation or
adoption is justified by this test failure. Hosted CI is left to Javid without polling.
