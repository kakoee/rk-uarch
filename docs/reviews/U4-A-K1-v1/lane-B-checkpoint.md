# Actual K1 target and CI joins

A's real target is the `uarch_engine` library (`kind=[lib]`, crate_types=[lib], test=true)
in package `uarch-engine`. Private unit tests compile under cfg(test); there is no public
binary, JSON input parser or subprocess wiring before K2. The 19 authored test names can
be discovered with `cargo test --locked --offline --all-features --target
x86_64-unknown-linux-gnu --lib -- --list`; each has multiplicity one. Final discovery and
replay receipts follow. No zero doc-test suite counts as native evidence.

The five accepted installation mappings and Dockerfile are installed unchanged from
83a9a14. Local alias `stable` reports exactly the accepted 1.99.0 release/commit and
components; it is explicitly local evidence, never the immutable B builder identity.
B's actual environment is not yet published at the consumed main ab7d9e0. No builder
RepoDigest is invented. A keeps B's CI scripts and workflow untouched.

Two concrete existing enforcement joins need B's CI reconciliation:

1. `third_party/patches/0001-u4-k1-register.patch` is the numbered register change
   required by CLAUDE. It applies to ab7d9e0 and reverse-applies to the installed register.
   Current ci.yml's patches step unconditionally fails if *any* patch exists. Replace
   that placeholder with a real application/postimage check under B's ownership.
2. Current native job installs an unpinned cargo-deny and omits pinned environment,
   release/replay and test inventory checks. It is not qualifying K1 CI. Use B's accepted
   environment workflow once constructed, preserving the documentation-only path.

The ordinary third-party unit check now allows only the exact accepted Unicode tuple
(component, version+archive hash, expression); negative controls cover altered component,
version and licence. The global allow-list is unchanged. No vendor policy or protected
source is changed.

Consumed B's subsequent environment coordination at
07eb628d8478f9c0d753eb9d42b9931108501ccd. Its actual Docker availability failures leave
real Linux environment execution pending; A does not change that host. The private replay
test is `tests::canonical_replay_private_bytes`, invoked with `--exact --nocapture`.
It emits exactly one line prefixed `UARCH_K1_REPLAY_V1=`; the remainder is the canonical
internal JSON. This test is discoverable in both modes, as is the conditional owner test.
