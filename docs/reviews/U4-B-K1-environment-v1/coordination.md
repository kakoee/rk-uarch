# Published B → A K1 environment interface

The human release ab7d9e0 is installed and its U0011 bytes match
f452e2263b9e64a837e0a9fccaae73c7a5b01bd601a5f7cee141e06a7ca23a8f. Exact tool and licence
acceptance is settled. B is working independently of M/policy migration.

At that published revision native/Cargo.toml still has members=[] and no Rust sources.
B will consume only A's published commits, never A's uncommitted clone or a synthetic seed
crate. Required A inputs are the five accepted native installation mappings, real source
and discriminating tests, and the installed notices. No dependency/manifest substitutions.

For discovery B will freeze the actual test target names/kinds and complete test-name
multiplicities from debug and release `cargo test --locked --offline --workspace
--all-targets --all-features --target x86_64-unknown-linux-gnu -- --list`. Empty selections,
ignored-only/filtered suites and mode drift refuse. Please keep any debug-specific owner
assertion test discoverable in both modes, with its conditional assertion inside the test;
if actual required inventories differ by mode, publish that fact for an explicit guard
reconciliation rather than silently omitting a test.

For U-P11a acceptance 3, identify an actual private fixed-delay replay test that prints its
canonical internal result bytes on one line with an unambiguous prefix. Publish its exact
fully qualified test name and prefix (neither is invented by B). B will invoke that test
alone in three fresh processes per mode and compare the six payloads byte for byte. This is
private K1 evidence, not a public K2 protocol. A's tests still establish the hand-derived
critical path and semantic coverage; an equality check alone does not.

For semantic fault controls, publish bounded source/test anchors when implementation exists:
original file SHA256, one unique before/after Rust replacement and the real discriminating
test/diagnostic. B's controller will mutate only its disposable source export, run the
required failure, restore exact bytes and rerun the positive. Missing source, deliberate
compile/test failure, empty/filtered selection, absent offline cache, tool identity and the
current Unicode-policy refusal are separate controls; none counts before actual execution.

The existing local Docker Desktop Linux daemon is unavailable, and WSL Docker integration
reports disabled. No daemon/settings/host installation is performed by B. Hosted Actions
exists in this public repository, but the production native CI job will remain unchanged
until the final image is accessible with authorized access and every placeholder is resolved.
No image is published. Final image/cache/discovery/native receipts remain construction
outputs, not inherited from the accepted base or A's host-tool observations.
