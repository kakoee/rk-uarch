# U2-artifact-adoption-v2 — exact candidate ready for decision

**Complete audit passed. Adoption is pending Javid's explicit approval.** The human created/verified-identical pair completed from the accepted freeze and unchanged environment. The coordinator independently audited the complete candidate; no agent ran oracle generation.

Candidate MANIFEST.json SHA256:

`f8220c9457226562040e5646835c3073acd2f58cd7631a5eb9e74632e60cc96e`

Current adopted predecessor:

`2d15afd7dd80124f70d387bc7cde4addda29162cd49370d40da7b99830709b44`

Accepted input manifest: `9a30b29029a32339dfc6062e138cebc23f7f1474044b414068dd9c8113c1dca0`. Source commit: `14fa0ede963c03ebe4bdafa3b396e7d513d0f24f`. Upstream remains `1e5706e0ebfcc67c1a7333079a35b75f693e9963`.

## Complete differences

| Item | Independent result |
| --- | --- |
| All 1,008 workload rows | Complete fixture bytes identical; no count, duration, null, query, attribution or identity changes. |
| All four actual precision refusals | Complete bytes identical, including outcomes, messages and source/component bindings. |
| Complete 48-file package | 45 unchanged, three changed, zero added or removed. |
| Three changed files | MANIFEST.json; u2-inputs/SHA256SUMS; u2-inputs/support-files.json. |
| Embedded inputs | All 24 match the accepted freeze exactly; only build.py's entry changes among 84 support files. |
| Upstream sources | All 12 copied sources independently match pinned Git objects. |
| Generator, environment, scopes | GENERATOR.json is byte-identical, including fingerprints and recorded environment. Component descriptors, model sidecars, schema and lock are unchanged. |

This refresh records the reviewed RR-C1 source binding. It does not change oracle performance values or prove model accuracy. Same workloads and the same accepted numerical gates remain in effect.

Evidence: [audit.json](audit.json), [reproducible read-only audit](audit.py), [strict check](strict-check.txt), [created log](../U2-real-generation-v2/created.log), [verified-identical log](../U2-real-generation-v2/verified-identical.log), and [complete semantic diff](../U2-real-generation-v2/semantic-diff.json). Audit.json records the generation-evidence hashes and all three matching preflights. The canonical adopted directory and its complete 48-file predecessor match the existing Git commit byte for byte. No extra predecessor tree was copied merely for this review.

## Exact proposed approval scope

Approve **U2-artifact-adoption-v2** to:

1. Record Javid's acceptance of this exact candidate and materialize the separate administrative adoption ReviewRecord, with the candidate manifest as its sole subject.
2. Reverify the candidate/frozen inputs/predecessor; stage the complete exact candidate and place it at the canonical vendor location in integration. Preserve the displaced predecessor and existing human logs/candidate. Do not hand-edit any generated file.
3. Apply the exact [current-adoption bindings patch](current-adoption-bindings.patch): update only CURRENT_MANIFEST and REVIEW_SHA256 in contract/tests/test_u2_historical_snapshot.py, and replace tests/fixtures/u2_b/received-adoption-review.json with the new accepted administrative record. No test assertion, threshold, historical fixture or acceptance rule changes. Both paths are outside the 84 bound support files. This is an explicit proposal for the contract-test change; it remains unapplied.
4. Run strict placed-artifact checks, full tests, actual adopted consumption and revised-input table/report/repeat/prepared replay/capability checks. Report executed results and outstanding obligations separately.

[Placement plan](placement-plan.json) gives exact paths and identities. [Proposed adoption text](proposed-adoption-record.json) is wrapped as **DRAFT TEXT ONLY**, not a runtime ReviewRecord or human approval. It has not been consumed as adopted evidence. After explicit approval, the proposed runtime-record bytes would have SHA256 `5ab5192e35d395b93d7da1ee5bac0b33e2a9f0961c5b03fb60a7368981866fbb`. The patch SHA256 is `f3b5f1ff00446932d0fd59e07d3b4f5f14c6bb9e281413c24d9a90a47183577a`; check-only application passed. The old administrative record remains preserved in Git and existing v1 evidence.

This artifact approval is required by U0002's complete-candidate adoption rule. It is separate from the already accepted source freeze and local source checkpoints. No actual revised-artifact runtime acceptance is claimed yet. Existing physical capacity failures, unexecuted hardware cases, unknown error/energy quantities and unsupported proof capabilities retain their dispositions.

No canonical placement, fixture/constant update, runtime adoption record, commit, push, main publication, tag, cleanup or sprint closure occurred during this audit. Commit/push/closure remain separate after adoption, and worker worktrees remain preserved.
