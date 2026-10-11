# U0003 Lane A revised proposal package

**Revision 3: R1/R2 corrections only. S remains selected for drafting. Unaccepted, uncommitted, unpublished.**
No runtime or public contract implementation. Existing exits remain operative until Javid
accepts exact replacement bytes. The initial 36-entry package is preserved by the coordinator
under manifest e67cfdae8b6eb3c030670640b0f8760cc541f9ed8bb5c3b223bdff998e078ee1.

Current correction: [R1/R2 dispositions and exact rules](R1-R2-corrections.md),
[r1-r2-validation.json](r1-r2-validation.json), and
[delta from the 81-entry package](changes-from-81-entry.json). The earlier
changes-from-initial.json and validation records remain preserved revision history, not
new executions or current file digests. Public amendment hunks and their index are unchanged.

Read in this order:

1. [Handoff](../U2-U0003-proposal-handoff.md) and [ADR](../../decisions/U0003-one-chip-one-set-of-facts.md).
2. [Finding dispositions](amendment-dispositions.md) and [two-track amendment](two-track-amendment.md): exact old/proposed gates, model ownership, tests and limitations.
3. [Interfaces](interfaces.md) and [comparison/evidence/export closure](comparison-evidence-export.md): structural and semantic contract proposal.
4. [Schema](proposed.schema.json), fixtures/amendment-fixture-catalog.json and independent expected/mutation cases. Schema validation is distinct from planned runtime semantic validation.
5. [Public amendment hunks](public-amendments.patch) and public-amendments-index.json: 16 exact source/proposed document identities, not applied; three prompt mirrors agree. U0021 comes from the coordinator's accepted local host record; hunks need that integration baseline.
6. [Accounting](accounting.md) preserves exact original arithmetic evidence; [delivery](delivery.md) names ownership, sequencing and revised estimates.
7. validation.json, loader-probe-results.json and prompt-sync-results.txt distinguish executed checks from planned work. changes-from-initial.json records revision 2 history; changes-from-81-entry.json records the current delta.

The physical graph/result/table fixtures are hand-authored expected data, not executed engine
results. Hardware is the existing synthetic reference fixture with stub claims, not a real
chip or npu-l4. New primary/projection/precision fixtures have complete internal hash bindings;
retained upstream-only components use actual frozen bytes without invented uarch spec hashes.
Nominal input/output fixtures are independent expected literals, never generated oracle data.
Synthetic evidence/review/ordering fixtures cannot promote a real model or imply human approval.

`SHA256SUMS` covers every authored output except itself, including ADR, handoff and change log.
Its digest is returned in the final response, avoiding a self-referential hash. Relative paths
are rooted at Lane A. The change log's own and manifest digests are supplied by that manifest
and final response, respectively. Uncommitted hashes identify bytes; they are not Git recovery
history. Preserve worker worktrees. No production/public document patch has been applied.
