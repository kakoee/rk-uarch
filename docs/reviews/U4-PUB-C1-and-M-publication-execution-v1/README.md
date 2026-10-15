# M/policy and PUB-C1 publication completed

Javid approved `U4-PUB-C1-and-M-publication-v1`. The exact test correction was committed
locally as `cff8f96df7d297027d5adf29f0680d02c303ff6a`; normal merge
`34de1d70ed9f19641b5e984d7e153eedb72af95d` then preserved that human ancestry and the
published documentation history. The separate push fast-forwarded origin/main to that
merge, verified by remote readback. No force push or human-owned hook bypass occurred.

- [Test commit](local-test-commit.json): one approved ordinary test file.
- [Merge](merge.json): only review documents added relative to A's local test commit;
  non-review bytes equal the tested correction preview. The initial full whitespace check
  refused five already-published raw evidence/patch files. Their published blob identities
  were verified and preserved; the check passed excluding only those files.
- [Final relocation check](final-relocation.log): one pass on the actual merged A checkout.
- [Final strict check](final-currentness.log): current artifact accepted on that checkout.
- [Publication receipt](publication.json): coordinator, A and B fast-forwarded to the same
  merge with clean tracked/index states. Existing untracked reviewer/author files were not
  staged or overwritten. One reviewer probe changed concurrently during this operation;
  its old/new hash is recorded and its current content left intact. Do not claim every
  untracked hash remained unchanged.

The earlier coordinator 137-test correction run and broad run are recorded in
[reconciliation](../U4-PUB-C1-publication-reconciliation-v1/README.md), with inherited checks
clearly separated. Neither the full suite nor native tests were rerun for this publication.
GitHub CI was not polled. Artifact generation/adoption was not repeated.

[K1 Stage 3 receipt](K1-review-receipt.json) records the newly returned ACCEPTED response
verdict, verified report SHA256 and unchanged Stage 1 prefix. K1 patches remain unapplied;
no K2 release follows. A [separate installation decision](../U4-K1-reviewed-installation-v1/next-decision.md)
now gives the exact source/guard scope and installed-source verification boundary.
