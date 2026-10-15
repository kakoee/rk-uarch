# PUB-C1 coordinator reconciliation

**Ready for the separate installation/publication decision.** B's exact single-test patch
resolves the held relocation failure in a new private integration preview. No live test
installation, human-source publication, K1 installation or K2 release has occurred.

B's [handoff](../U4-B-PUB-C1-relocation-test-v1/README.md) is pinned at
`3af7ae2f347d2ff33a89018af27f0e0393622f71`. The patch SHA256 is
`64fce5ddcc4e75dcd540e359336d9daad6bb86492162c4044a29a235fa0bef5c`.
[Exact identity](identity.json) records a private union of that published main with human
checkpoint `5e774682a7abdc21aa0bac6a8f738e66c852d3e5`, then the proposed test correction.
Its corrected tree is `2b9f91ad76c671d77a75fc530a3e2d4565373a05`.

The correction separates two environments. The support-only checkout still validates the
artifact using the selected generator dependencies. The producer-disabled consumer probe
then receives twelve additional explicitly listed source files from the same pinned tree.
Those files are fixture inputs, not generator-support additions. All six producer/oracle
denial patches remain; the child uses isolated Python with explicit private source paths
and checks the origins of all imported project modules. Artifact bytes remain checked
before and after relocation.

## Executed by the coordinator

- [Original failure](baseline.log): reproduced missing `rkuarch.workload`.
- [Corrected affected selection](corrected-regressions.log): **137 passed, zero skips**,
  124.87 seconds. Entire affected module, tooling, support policy, historical snapshot and
  committed snapshot modules were included.
- [Revert](reverted.log): the original missing-module failure returns (3.11 seconds).
- [Restore](restored.log): the corrected relocation test passes (4.33 seconds).
- [Full-tree Ruff](ruff.log): passed on the current preview, including new review scripts.
- [Strict currentness](strict.log): current artifact accepted; exactly 56 support entries.
- [Preservation](preservation.json): all 2,212 tracked private-source files retained bytes
  and modification times across the 137-test run. All 49 artifact files match the preceding
  tested preview. A remains clean at its human checkpoint; no live author/reviewer changes.

[Commands and raw-log hashes](checks.json) record explicit private config/root/import paths,
isolated Python, no cache provider and unset ambient Python/virtualenv/human-approval
variables. The existing coordinator venv supplied dependencies; no install or oracle run
occurred. Logs normalize trailing whitespace only. Scratch paths identify these executions,
not persistent prerequisites.

## Prior evidence and limits

The [previous broad integration run](../U4-M-policy-publication-preparation-v1/full-suite.log)
was **1,893 passed, one PUB-C1 failure, 29 analytic-capability skips and ten deselections**.
It was not repeated after this test-only correction. Comparing Git trees confirms the only
non-review change since that broad run is this one test file. Do not combine counts and
claim a newly executed full-suite pass. Earlier mypy, schema freshness and import-contract
results remain inherited for unchanged targeted inputs; B's additional producer/origin
fault probes are reviewed receipts, not new coordinator executions.

No golden/performance/ordering no-op is credited as execution. No native campaign or hosted
CI was run here. K1's exact proposal and same-reviewer Stage 3 remain separate and unchanged.

[Decision: U4-PUB-C1-and-M-publication-v1](next-decision.md) specifies the exact one-path local
commit, normal integration of published documentation into the human history, and a separate
normal push. These are pending Javid's reserved publication approval. Any intervening
implementation/configuration delta requires new reconciliation; review-only additions may
preserve the same tested implementation. Record final local/merge/remote identities after
approval and leave GitHub CI monitoring to Javid.
