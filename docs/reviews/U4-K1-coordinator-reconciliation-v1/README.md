# K1 author handoff — bounded coordinator reconciliation

Subject: `892b9ee00c485718082e8ea9a765578cbd64d684`. Native and container bytes are
unchanged from A's executed evidence source `357dea8ee43ae098c284c672a44e6a6cf8482d27`.
Authority: human U0011 release `ab7d9e0`. [A handoff](../U4-A-K1-v1/handoff.md).

**Disposition:** local implementation evidence reproduced; no new blocker found within
this bounded check. Qualifying Linux execution, independent review and actual K1 acceptance
remain outstanding. No K2, G3a or U4 completion follows. The accidentally pasted Lane B
prompt was explicitly withdrawn by Javid; no replacement B task or execution of B's
construction work was undertaken here. B continues its already assigned session.

## Newly executed coordinator checks

A private Git export of the subject was used. Existing local WSL2 stable-alias Rust tools
match the four accepted rustc/cargo/rustfmt/clippy receipts byte-for-byte (Rust 1.99.0 and
compiler commit b940084d7eb6a299eb4bfeb8e34901bc051e7ac4). No toolchain was installed.
The initial attempt stopped before testing because A's historical temporary Cargo cache
no longer exists. The coordinator then fetched exactly Cargo.lock into its own disposable
cache, independently verified all 27 crate archive hashes, and ran every subsequent Cargo
check offline. No author cache or source was written.

| Check | Actual result |
| --- | --- |
| Five accepted native input hash mappings | pass |
| `cargo fmt --all -- --check` | pass |
| Full authored K1 unit selection, debug | 19 passed, zero ignored/filtered |
| Same selection, release | 19 passed, zero ignored/filtered |
| Three fresh-process private replays per mode | all six payloads identical |
| clippy all workspace targets/features, warnings denied | pass |
| Zero-owner-bypass fault, debug and release | both fail the intended 3000 vs 5000 ps assertion |
| Exact source restoration, same selected test in each mode | both pass |
| Live strict vendor currentness | pass |

Replay SHA256: `30c1e07014f238784ba570a367db1584847134280b2e4190c91761b9b179094a`,
matching A's published result. The original source hash and unique replacement were
verified against A's fault-anchors.json before mutation. Only scratch source was mutated;
restored bytes are exact. This is a selected coordinator fault check, not a random
U-REVIEW adjudication or an independent check of all model semantics.

Cargo test/clippy arguments were `--locked --offline --workspace --all-targets
--all-features --target x86_64-unknown-linux-gnu`; release adds `--release`. Replay selects
`tests::canonical_replay_private_bytes -- --exact --nocapture`, requiring exactly one
`UARCH_K1_REPLAY_V1=` payload per process. Properties used 256 cases and seed 41011.
CARGO_HOME and CARGO_TARGET_DIR were isolated under `/tmp/u4-k1-coordinator-bl4zfcwn`;
PYTHONPATH/MYPYPATH/VIRTUAL_ENV/UARCH_HUMAN and inherited Rust flags/replay sink were cleared.
Raw local diagnostics are in that directory's receipt.json/logs, not runtime dependencies.

A's other two fault campaigns, cargo-deny executions and broader Python/static receipts
remain inherited; the coordinator did not rerun them. No full Python suite, native image,
hosted CI, server work or performance measurement was run. No CI was polled.

## Remaining coordination

A stays at its K1 handoff for bounded corrections. B already owns the real Linux builder,
offline cache, actual target/test inventory, replay/fault controls and CI reconciliation.
A's published test names, replay prefix and fault anchors now supply the requested inputs.
B's published local Docker-unavailable observation is a construction dependency, not proof
that the kernel fails. Any needed host/distribution decision must be concrete and respect
the existing release; no new authority is inferred here.

The live workflow still has the documented unconditional rejection of numbered patches
and unpinned cargo-deny installation. B owns their correction; they have not been silently
waived or credited as qualifying CI. M installation/selected-policy migration and public
K2 remain separate from K1 local evidence. No new prompt, policy or protected edit was made.
