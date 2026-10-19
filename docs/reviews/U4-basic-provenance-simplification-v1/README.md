# U4 simplification: basic provenance and ordinary execution

**User direction approved; implementation and exact protected text are not yet installed.**
Javid retains the native-first U4 decision and requests basic provenance, explicitly excluding
mandatory executable hashes and the added deployment/authority/startup/tracing machinery.
He requests one fresh implementation session, not A/B lanes for this task.

Use [the single-session prompt](fresh-session.txt). Existing A/B provenance tasks are
superseded; preserve their commits and uncommitted work, but do not finish another approval
record, staging-proof or capture interface merely for the retired architecture. Do not
reset/rebase/delete peer work. One fresh independent clone owns the cross-cutting change.
No subagent or A/B confirmation dependency is required. Normal independent milestone review
still applies to the final source; author self-checks are not that review.

## Exact baseline and original intent

Published preparation baseline: da6ee495f30f9a98de2f2494efe32527e8d6e013.
Latest A source:0212cb5d1488baefa9be9580a77d06c7bd3237b1; handoff:945a3eab2e6c768e041f9f521b3c4f117429fb6f;
manifest:0c47762ec6bdd51dedd72f9e19a1a59e08ec8bed23be20a00bf15ff86930e250.
B81411e3 supplies the now-superseded ordinary build consumer. Bda6ee49 finds
B-PROV-STAGING-01 in that mechanism. Preserve that finding as historical/unresolved in the
old implementation; do not call it fixed by removing the mechanism. Normal build commands
must still compile their intended sources using the accepted lock/tools.

The user-selected original reference is Reza's commit
1d497be1a1c3b7fc621391d9f9c715cccaa09e97, not the later u03-end amendment.
Its build-spec §2.3.3 records uarch_version, request/table/spec hashes and model metadata;
§6.5/6.6 specify data hashing and deterministic outputs. U-P11a pins Rust/Cargo.lock and
requires actual tests/debug-release result agreement. Original U4 built tables with a fork,
with native in U6. We retain the later intentional native-first schedule; we do not restore
the fork or advance full-table work. The extensive current runtime evidence dependencies
are later additions. Table-build determinism is not executable bit-reproducibility.

## Concrete policy and documentation

[Proposed U0011 section](proposed-U0011-section.md) states the simpler boundary and explicit
supersession. [policy-and-plan.patch](policy-and-plan.patch) keeps U0011, execution-plan,
build-spec architecture and five canonical prompts/their §8 copies in sync. It applies to
the current installed documents, not to the superseded unapplied provenance patch. The
new text supersedes older authority clauses prospectively; historical approvals/receipts
are not rewritten. No live source/default-route/contract/ADR is changed by this package.

CLAUDE.md states: “Agents propose and stop on contract/, tests/golden/expected/,
CLAUDE.md, docs/decisions/.” Therefore the protected documentation patch remains unapplied.
The fresh worker prepares the exact combined protected carrier/ADR patch with the code,
then returns it for the existing human installation step. This is not a request for another
general scope vote: the simplification direction is already authorized.

[Transition map](transition-map.md) identifies real code hooks and the required replacement.
Do not use fake assurance flags, zero hashes, cfg(test) public bypasses or old accepted
runtime evidence to simulate success. The normal executable must work with the installed
package and actual input files, with developer sources and evidence absent.

## Next task and stopping point

One fresh session implements the Python/Rust/packaging changes, proposes the minimal
protected schema changes and verifies the ordinary executable in a disposable installed
package. Necessary bounded local builds/tests use existing approved tools/image; no root
placement, registry, remote CI polling, spending, new dependencies or real product campaign
is requested. Keep synthetic development runs distinct from shipped/installed results.
Return one coherent source freeze, exact protected patch and measured observations about
files read during the smoke test (no syscall tracing requirement). Then perform one focused
independent review and the normal protected installation. No further A/B author handshake.
