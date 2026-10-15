# A C1 precise continuation — candidate evidence, pending acceptance

Both authorized offline updates succeeded. The unchanged B whole-lock predicate passes
on the actual Cargo-generated candidate: **28 retained identities plus exactly eight approved
additions**, with exact versions, sources and checksums. Full and Linux feature comparisons,
archive checksums, offline metadata/fetch repeats and the accepted offline cargo-deny
licences/bans/sources checks pass. This completes the authorized C1 experiment, not dependency
acceptance, C2/C3, installation, public K2 execution or qualification. Stop for coordinator.

Candidate Cargo.lock SHA256:
`cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be`.

## Fixed input and actual corrections

The source remains0718955cc0656e5bac4688d4696abbd547cb4186. The initial lock remains
3df872c1e8c445b179dd8162430a5265fa770a62bcfa009009dae49d878bf084, and the scratch manifest
uses the exact [original diff](scratch-manifest.diff). Only a copy of the rejected lock
(d2b744a9045a124c5edb097c821d2b69e9f0dd5e734554542fdfee6b5a4c6211) seeded the new workspace.
It was unresolved input, not an accepted lock. No hand-built lock or constraint crate was used.

| Step | Actual outcome | Gate |
| --- | --- | --- |
| `cargo update -p crypto-common@0.1.7 --precise 0.1.6 --offline` | exit0; crypto-common corrected; typenum1.20.1 retained temporarily |28 old + six already-correct additions exact; corrected checksum exact |
| `cargo update -p typenum@1.20.1 --precise 1.19.0 --offline` | exit0; typenum corrected |all36 final identities exact |
| Retained B `entries_allowed` |passes on actual candidate, unchanged function |[actual gate](retained-B-gate.json), [full tuples](final-lock-gate.json) |

Both updates used Docker `--network none`; no index retry was needed. All intermediate
locks, raw update outputs and [exact command/environment/exit receipts](commands.json) are
included. The full gate preceded the sole online archive-retrieving command.

## New observations and inherited inputs

The same local Linux/amd64 image e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523
and actual Rust/Cargo1.99.0, cargo-deny0.20.2, rustfmt and clippy identities were reverified
with networking disabled. Version/image outputs match the prior accepted receipts byte-for-byte.
No image pull, install, replacement or infrastructure operation occurred.

All38 original cache files were verified against the old published inventory. Only the35
registry-index files were copied into the fresh private cache; no old Cargo database,
archive or extracted source was copied. Original35 index requests remain inherited evidence.
New activity made **zero index requests and35 archive GETs**, all HTTP200, through the
retained explicit CONNECT proxy. Its host/port allowlist is not a packet firewall; recorded
HTTP paths independently match the exact lock-derived static.crates.io/crates URL set.
No credentials, API host, advisory fetch or global Cargo override was used.

[Network inventory](network.json), [proxy outcomes](metadata-full-network.tsv), and
[filtered HTTP trace](metadata-full.filtered.log) retain the new observations. The complete
raw trace remains private with its digest. Bulk archives/sources/cache remain outside Git.

## Graphs, licences and offline results

[Full metadata](metadata-full.stdout) has36 nodes; [Linux metadata](metadata-linux.stdout)
has35. The only full-only node is the unchanged r-efi6.0.0. Full metadata intentionally
retrieved this allowed old non-target archive. Both graphs retain both cpufeatures versions.
[Full](features.full.json) and [Linux](features.linux.json) comparisons match the old baseline
plus exactly the declared additions and serde_json arbitrary_precision. Complete requested
edges are in metadata; unified feature trees are in [full](features-full.stdout) and
[Linux](features-linux.stdout) outputs. No optional new feature branch was enabled.

All35 [archives](archives.json) match lock checksums. Every extracted archive member was
hashed and matched to its archive; [source inventory](source-inventory.json) binds the
private detailed map. [Licence/notice inventory](licences.json) records actual files,
expressions and digests. The eight additions have the proposed MIT/Apache alternatives
(generic-array MIT). The filename-only first audit stopped on old r-efi: its licence text
is in **AUTHORS**, reached from README, including the MIT grant and copyright notices.
[Follow-up inspection](licence-followup.json) records that actual text and file digest;
no missing licence was fabricated or retrieved from another endpoint. That host audit
error and the initial missing `python` executable are retained in [host errors](host-errors.json).
Neither changed dependencies, constraints or the Cargo results.

Full and Linux metadata/fetch were repeated with Docker networking disabled and explicit
`--offline --locked`. Metadata repeats are identical to their first respective outputs;
all fetches exit0. Linux metadata was already offline on its first invocation because the
full retrieval had populated the exact cache. No redundant online fetch was needed.

The unchanged accepted command was:

```text
cargo-deny --locked --offline --all-features --config deny.toml check licenses bans sources
```

It returned0: [bans ok, licenses ok, sources ok](deny-check.stdout). The three
[unused licence-allowance warnings](deny-check.display.log) are preserved (display whitespace normalized; raw output bound in private receipts). Its existing graph
policy targets Linux; it is not a claim of an automated all-platform licence check for
r-efi. The separate full inventory includes that archive and its actual licence notice.
The workspace has no feature definitions, so `--all-features` adds no workspace feature.
Cargo produced only a rustc version/target-information cache in target; no build script,
probe, engine, object, executable or library was built or run. `force-soft` is selected
in the actual graph; source selection alone is not C2 scalar/disassembly/no-SIMD proof.

## Preservation, validation and next join

[Preservation](preservation.json) verifies all2683 original private files unchanged in
bytes, size and mtime, including raw receipts and cache. The original published C1 package
Git tree remains17e47b78515aecbdf9f7ea4114f968bfaf4d63ea. New workspace:
`/tmp/u4-k2-c1-precise.styffox_`. [Private receipt bindings](private-receipts.json) identify
all raw outputs, executed controls, source export and inventories retained there.

Published main86bfb64 was received normally. The human semantic installation and prior A
history remain ancestors; all ten human postimages match. Publication checks are separate
from experiment checks against0718955. No historical verifier or evidence was retargeted
to installed main. Only this owned review package is added; protected source, live manifest,
lock, artifacts, schema and U0024 deferrals remain unchanged.

Run the read-only [receipt verifier](verify_receipts.py) with the existing Python environment.
It checks source/export bindings, transitions, unchanged whole-lock predicate, graph/features,
archive/receipt hashes, command restrictions, links and publication preservation. In-memory
negative controls exercise gate refusal; they write no Cargo.lock and confer no native evidence.
See [validation](validation.json) for the actual lint/check outcomes.

B's published predicate now joins the actual candidate; B has not reviewed these new receipts.
Coordinator and human decisions remain: accept/reject these exact dependency/feature/cache
bytes and separately authorize any C2 work. No new pin/licence vote was requested to perform
this already-approved C1 continuation. No C2/C3, final authority or qualification follows
from a passing experiment.
