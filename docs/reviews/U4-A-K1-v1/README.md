# Lane A private K1 implementation

[Final handoff](handoff.md) · [actual test inventory](test-inventory.json) ·
[semantic fault anchors](fault-anchors.json) · [local checks](local-checks.json).

Implemented and locally checked; real accepted Linux execution and coordinator
reconciliation remain pending. No K1/G3a/U4 closure is asserted.

Authority: human-installed U0011 at ab7d9e0ab81be02a7294d18aeab8bca5591cfda6,
postimage f452e2263b9e64a837e0a9fccaae73c7a5b01bd601a5f7cee141e06a7ca23a8f.
Tool inputs are the accepted 83a9a14 package, installed byte-for-byte at its approved mappings.
This checkpoint is private K1 only. M/policy source and artifacts, public K2, subsystem
models and B-owned CI remain outside this change.

Tests were authored before kernel implementation. tests-first.log records compilation
refusing the missing kernel types/functions with the exact accepted dependencies resolved.
Command: RUSTUP_TOOLCHAIN=stable CARGO_HOME=$PWD/.u4-k1-local/cargo cargo test
--manifest-path native/Cargo.toml --locked --target x86_64-unknown-linux-gnu.
The existing local stable *alias* resolves to the accepted 1.99.0 compiler commit, cargo,
rustfmt and clippy versions; it is not the selected pin or a different release. Local
checks do not qualify B's future immutable environment or hosted Linux evidence.
