# K2 combined-runtime v2 — completed local first use

The approved campaign and required saved-output replay completed successfully. This is
actual local WSL2/Docker execution with the accepted offline image, original candidate-04
native binaries, and separately approved immutable Python runtime. It is not inherited
construction evidence, hosted qualification, component execution or final U4 acceptance.

| Actual outcome | Result |
| --- | --- |
| Frozen cases | 133 |
| Fresh native calls | 798: debug/release × three repetitions per case |
| Results | 780 successful results; 18 expected TimeOverflow refusals |
| Determinism | Six exact output/status comparisons per case passed |
| Workers | 11, bounded by observed memory headroom; 16 visible CPUs |
| Campaign elapsed | 259.99 seconds |
| Shared authority resolution | 79.77 seconds |
| Case processing | 173.87 seconds |
| Saved-output replay elapsed | 194.25 seconds |
| Replay | K06-02 and S08-zero-bridge both passed; 26 corruption controls refused; originals restored and passed |
| Additional native calls during replay | 0 |

These times describe this validation run, not simulator throughput or hardware prediction
accuracy. The complete launch, operational and runtime identity receipts agree. The coordinator
independently checked every saved call/blob against the original frozen plan, exact receipt
membership, both exit-zero launches, expected outcomes, replay controls and final 45-file
root-owned seal. Campaign input snapshots are byte-identical. The reviewed replay runtime
checks its snapshots in memory before writing its complete operational receipt; it does not
emit the standalone scheduler's parallel-replay-inputs.json. An initial coordinator audit
expected that unused filename; only the audit was corrected, with no execution retry.

## Identities and authority

- Original native source: `24fa36803081e5077d5977baa91441a2c8534ec8`.
- Reviewed runtime helper: `0c4afcfa0ab314724afa869ac2d5736a22fb0e89`.
- Runtime candidate: `ecc0dfafea975701bd933beda08735d0def9c7a3e76c03616a543a98664c9b81`.
- Actual human decision: `026d365e0bee9da1ff1ea1a8717e12ab1dfe23e8`.
- Actual placement/preflight publication: `b11bf3add519085608adb9f69d2969423de65fd6`.
- Human authority-placement helper: `96cc29a630f11d59d6182b72a2223f6887dd6e61`.

The user returned the placement command without stdout. The coordinator read and verified
all five actual authority files, their exact hashes/joins and root-owned modes, and the
unchanged 40-file payload before launch. [That verification](authority-verification.json)
is distinct from a claimed transcript of the human command.

Both launches used the exact reviewed launch.py, `--execute-placed`, that helper publication,
and `/tmp/u4-k2-combined-campaign-v2`, first `campaign` then `replay`. Each verified actual
remote publication in a fresh Git context. The accepted image ran offline and read-only;
workers parallelized cases while preserving all six fresh calls and per-response validation.
The stopped 88-checked/89-transport run was neither resumed nor credited.

## Evidence and limits

[Execution summary](execution.json) binds all pins, timings and artifact hashes.
[Raw manifest](raw-manifest.json) lists all 2,012 output files (287,116,356 bytes).
[Compact receipts](receipts.tar.gz) retain all non-blob outputs. Every real request/stdout/stderr
blob is also retained in the full, round-trip-verified local archive:
`tables/U4-K2-completed-first-use-v2/evidence.tar.gz` (ignored by Git), SHA256
`f10e60d56c6749e8b142bb256ce2e4c387f762f0af093e3b2353af21e5bc67e0`.
The original `/tmp/u4-k2-combined-campaign-v2` output and its full temporary archive remain.
Compact public receipts alone do not replace the raw blobs for an independent replay.

[Replay controls](replays.json), [campaign launch](campaign-launch.json),
[worker timings](worker-summary.json) and [replay launch](replay-launch.json) are copied
verbatim. No tests, binaries, protected sources, native authority, historical evidence,
artifact lifecycle or canonical runtime source was changed to achieve this result.

This establishes the authorized fixed-delay K2 public first-use and replay evidence only.
Component semantics/profile decisions, protected installation, native models/authority,
human L1 workings and the independent component Stage 3 remain separate. U0024's remote,
nightly and performance qualification deferrals remain open, as do final U4 review and closure.
The next review handoff is [component Stage 3](../U4-component-stage3-v1/reviewer-prompt.md).
