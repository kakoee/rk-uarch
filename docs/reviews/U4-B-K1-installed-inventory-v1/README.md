# Installed K1 inventory — unapplied B reconciliation

The coordinator's real inventory is consistent with installed, tested source
`fb7ba4a75d17650d91c2d2532460ccc1c16b5808`, tree
`4c0a63945d0c793347a7791f5ba1183f4e8bd90e`. B independently checked its Git/source identities,
raw metadata, tools, 28-name counters, six payloads and inherited fault receipts. **No native
execution was repeated.** All raw paths were available; no concrete native delta or missing
receipt warranted a rerun. The new host guard selection passes **35 tests**.

B started and integrated published main at `1c42aedac760fdabc264282153d270d31dc0998b`.
The exact approved installation and KI-C1 exception are accepted inputs, not new voting items.
This package stops before live inventory replacement.

## Exact candidate for review

[Unapplied patch](inventory-bindings.patch), SHA256:
`4b807f41653a33e1a7e29ed840ce0f55e4d3313da10c91791142bf2a781c070d`.
It has exactly two paths:

1. Replace `.github/native-k1-tests.json` with the coordinator's
   [inventory.candidate.json](../U4-K1-publication-v1/inventory.candidate.json), **byte for byte**.
   Postimage SHA256: `e2a7bf61a71dce69485765a76759d4add7bbe5ada11ddd3a0b179742c253be46`.
   It identifies the real tested `fb7ba4a` commit/tree, 28 names in each mode, unchanged
   all-features/target/tool/image inputs and the accepted replay payload.
2. Add `.github/native-k1-controls.json`, the separate
   [control binding](controls.candidate.json), SHA256
   `6df76826563a61caa208c8619f6ef35dda74a5122e03bcd2000a9603229e98ef`.
   It binds the inventory, final-source subject/metadata, replay selection and mutation,
   eleven semantic anchors and the original installed-source fault evidence by exact hashes.
   Historical anchor/controller files remain unchanged; the new binding references their
   exact reviewed bytes instead of rewriting historical packages.

[Patch verification](patch-verification.json) records the base, both postimages and successful
reverse/forward controls in a private scratch repository. Reverse recovers the exact old
19-test record; forward recovers the exact candidate. Its configuration tree is only a patch
identity, **not a newly tested source commit**. No new source pin is invented for this or a
future documentation/configuration commit.

The live inventory remains at SHA256
`81a62eec7f1d51f2f97298fbcb5b8508c8ca55272ad5547d7ad3feae383a03d1`, with 19 names and its
historical tested source `892b9ee00c485718082e8ea9a765578cbd64d684`. The new binding records
where those exact bytes remain reachable in Git at `fb7ba4a:.github/native-k1-tests.json`.
All historical receipts remain intact. The new controls path does not exist in live source.

## Exact approved exception and evidence attribution

[Host audit](evidence-audit.json) verifies all twelve installed postimages and the unchanged
lock SHA256 `3df872c1e8c445b179dd8162430a5265fa770a62bcfa009009dae49d878bf084`.
The sole non-review delta from fault-tested
`63ca8bec5a4ac1d7dcf87290a5cf080c846de66d` is the approved wrapping in
`tests/unit/test_third_party_patch_check.py`, SHA256
`26a882fdb9c0930864e47c88dae36c571085c614c64dd425a1cdbcb66f4c8762`.
B compared Python ASTs directly and required equality. All eleven other reviewed hashes and
all native/dependency bytes are unchanged. The subject comparison permits precisely that
one hash and the exact recorded exception metadata. Historical subject tree
`6d5263e13e43a5dfb44d8addf93cc47cc814a0ac` remains a review reference, never an installed tree.

| Evidence | Actual execution source | B's work here |
| --- | --- | --- |
| 28 tests in debug and release, multiplicity one; six fresh replays | Coordinator on `fb7ba4a` | Revalidated raw counters, result summaries and payload bytes |
| Full/target Cargo metadata, tool/lock/features and checks | Coordinator on `fb7ba4a` | Revalidated graph hashes, raw native source, discovery, exact versions and command success |
| 13 metadata-fed Python linkage/guard checks | Coordinator on `fb7ba4a` | Verified explicit command/environment, real metadata join and saved passing output |
| 22 semantic failures and 22 individual restorations | Coordinator on `63ca8be` | Verified every command/log hash, exit101, selected failure, diagnostic and restored positive |
| Generic failures, replay drift and restoration | Coordinator on `63ca8be` | Verified intended diagnostics, refused incomplete selections and restored payload hash |
| Two F5 failures and four positives | Coordinator on `63ca8be` | Verified graph/source binding, log hashes, statuses and restoration receipt |
| 35 inventory/binding guard controls | B, this task | Newly executed host-only checks over saved evidence and in-memory negative mutations |

The fault evidence applies by exact unchanged-code identity; it is **not a new fault run on
fb7ba4a**. The old adapters' unconditional `fault_campaign_pending` and `reviewer_stage3_pending`
fields are retained in their raw receipts. They are not new blockers or a reversal of accepted
Stage 3 and completed original fault campaigns. No remote/native qualification is inferred.

## Replay, fault and manual-linkage consumption

Replay remains `tests::canonical_replay_private_bytes`, prefix `UARCH_K1_REPLAY_V1=`, sink
`UARCH_K1_REPLAY_OUT`, with payload SHA256
`4490d63cd5b49bac327ded1661df7802356f541e003391666963965809f2a62a`.
The guard requires both six-way nonempty byte equality **and** that expected hash; equal stale
payloads refuse. The new binding references the Stage 2 release-only whitespace mutation with
simulation.rs SHA256 `472698e658e4741516b0aa98ea94095bb4ed1cda0aa656b5ead2bdc32fa52191`.
All eleven semantic anchors are checked against both actual source commits for exact bytes,
preimage hashes and unique replacements.

The new control file is passive data. It does not change an entry point, invoke old drivers,
install a CI job or cause the old historical replay driver to read a new input implicitly.
An explicit consumer must verify the binding's referenced file hashes, read only the `faults`
field from the historical Stage 2 proposal, and read the bound replay mutation. Retain the
reviewed literal-to-regex adaptation, exit101/selected-test/mode-specific diagnostic checks,
private-export restriction and byte/mtime restoration used by
[installed_faults.py](../U4-K1-installed-verification-v1/installed_faults.py). Do not call the
old hard-coded historical replay input against Stage 2 source. No new fault execution is
needed merely to replace a data binding whose source bytes and existing evidence match.

Manual linkage is explicit: `native/test_register_linkage.py` is outside default pytest
collection. The coordinator invoked it alongside `tests/unit/test_third_party.py` and
`tests/unit/test_third_party_patch_check.py`, with explicit pytest root/config, isolated
Python paths and `K1_METADATA` set to that run's actual full Cargo graph. The graph came from
`cargo metadata --locked --offline --all-features --format-version 1`; Linux-filtered metadata
is separate. The new binding points to the complete metadata identity and recorded tool hashes.
Host Python validation is not container-native execution.

The accepted image remains
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
If the recorded raw work later disappears, the host audit refuses. Reconstruct final-source
receipts using the unchanged publication `verify_installed.py` with `--source-commit fb7ba4a…`
(the full hash above), a new private `--work`, the ordinary repository and existing host Python.
It uses the exact accepted image offline, with no pull/build fallback. Fresh graph paths/hashes
must be recorded as new evidence, not substituted beneath old receipt hashes. This task did
not need that fallback or perform image/network/dependency operations.

## Newly executed controls and coordinator stop

[Auditor](reconcile.py), [audit command](host-audit.json), [guard tests](test_guards.py),
[command](guard-tests.json) and [result](guard-tests.log) are owned proposal tools only.
Controls reject missing/extra/duplicate/old19 tests, incomplete/failed/ignored executions,
wrong or untested source pins, the historical review tree as an installed tree, stale/missing/
divergent replays, image/features/metadata drift, stale anchors, fault misattribution and any
unapproved postimage/exception change. Mutations are in-memory; no raw source or receipt is
changed. Scoped Ruff check/format passes. Only this owned package is published.

Coordinator action: review this exact two-path patch and attribution, then separately authorize
live replacement. Installation approval and the KI-C1 exception are already settled; this is
the remaining inventory decision. The historical 19-test record and live replay/fault bindings
are unchanged now. K2, remote/hosted activation, registry/server work, performance claims,
G3a/U4 closure and tags remain outside scope. No GitHub CI polling occurred.
