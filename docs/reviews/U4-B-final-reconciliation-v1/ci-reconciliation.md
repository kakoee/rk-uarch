# Concrete CI/tool reconciliation — no image or native execution

This proposal supersedes the early B native-job template, preserving the live workflow
unchanged. Its [replacement job](native-job.yml.in), [host script](native-host.sh),
[container script](native-container.sh) and [host guard](ci_host_guard.py) are reviewable
inputs now. No native source, tool, licence policy, cache, image or workflow is installed.
A's tool subject is 83a9a14fd76a00b7858ddd140cc0e0589f80a267. No fresh external verification
was needed: B checked retained bytes and internal joins; A's primary-source/archive checks
remain inherited evidence, not B observations or licence acceptance.

## Pins and actual installation paths

Rust 1.99.0, full commit b940084d7eb6a299eb4bfeb8e34901bc051e7ac4,
x86_64-unknown-linux-gnu; minimal+rustfmt/clippy. The precise versions are compared bytewise
to A's five version-receipts inside the container. serde=1.0.229 (derive,std),
serde_json=1.0.154 (std,float_roundtrip), dev-only proptest=1.12.0 (std), defaults disabled.
B verified all 27 external Cargo.lock checksums against crate-closure, direct feature/pin
joins, 17 package.sha256 entries and all five native-inputs.sha256 source mappings:

| Native installation | Exact A proposed source |
| --- | --- |
| native/Cargo.toml | workspace.Cargo.toml |
| native/crates/uarch-engine/Cargo.toml | Cargo.toml.proposed |
| native/Cargo.lock | Cargo.lock |
| native/rust-toolchain.toml | rust-toolchain.toml |
| native/deny.toml | deny-proposed.toml |

Metadata checks bind the mounted native path, exact workspace member/manifest, actual test
targets and external package/version/features against the retained closure. The target is
explicit on clippy/test commands and deny's graph. --all-features selects the workspace's
actual declared features; it is not permission to activate all optional features of every
dependency. Any graph mismatch at construction/discovery refuses and returns for review.

cargo-deny 0.20.2 binary archive SHA256:
9f12ed4c49936e09b48bf862b595cde2fe64fcbd9d74dfacac6131ca824c8d5f.
This differs deliberately from the cargo-deny *crate* archive checksum in pins.json; do
not substitute the latter for the installed binary. Command, from native/:

```sh
cargo deny --locked --offline --all-features --config deny.toml check licenses bans sources
```

A's retained ci-command-control.txt observes bans/licenses/sources success only with the
proposed policy; B does not rerun it or claim native correctness. `--config` is global,
before check. B verified the current→proposed config delta is solely Unicode-3.0 for exact
unicode-ident 1.0.27. MIT selection does not remove that AND requirement. The private
publish=false workspace exclusion is explicit; no project licence is invented. Javid must
accept that narrow exception and run-only compiler/cargo-deny/OS scope separately from M.
GPL/LGPL and other OS/tool obligations remain in A's 131-package notice map; cargo-deny
is not an OS licence audit. No public image distribution or licence acceptance is inferred.

## Host/container placement and durable logs

Hosted ubuntu-24.04 runs checkout at immutable 11bd71901bbe5b1630ceea73d27597364c9af683,
Docker transport and **Python 3 ≥ 3.11 stdlib guards only**. No Python layer is added to A's
native image. Host Python executable/version/SHA, guard SHA, runner image labels, Docker
version and checkout SHA are recorded. The hosted image label is operational, not an
immutable compiler environment or controlled performance host.

The native container uses the eventual final repository@sha256 and linux/amd64; image
inspection must match the exact RepoDigest, OS and architecture. A's base digest
ba81bc3eaa4422af576c0262515d96b0111a628a6ccc2c86557cf55c9a4bbee0 is **not** that final
image. No host cargo/rustc or ambient host Cargo cache is used. Container paths are
CARGO_HOME=/usr/local/cargo, RUSTUP_HOME=/usr/local/rustup and the exact 1.99.0 target
suffix. Inspect logs command paths, rustup's resolved tools, versions and installed target;
construction must demonstrate rustfmt/clippy discovery after A's direct archive installs.

The checkout mounts read-only at its *same absolute GITHUB_WORKSPACE path*. Thus metadata's
source/manifest paths can be checked on the host without rewriting or silently accepting
another installation. /receipts binds a fresh mktemp directory under RUNNER_TEMP; /target
is ephemeral and shared by debug/release within the checks invocation. No egress in native
containers (`--network none`); root filesystem/cache writes are disposable, never host
source writes. Package and installed-layout checks run in both inspect and checks stages.

Inspect executes versions/metadata only. Host source/target/feature guard must pass before
the checks container runs fmt, clippy-D warnings, deny and debug/release list+execution.
Each command writes <name>.log (stdout), <name>.stderr and <name>.exit. No tee hides a
status; the logger returns the exact code, set-e stops the script, Docker status propagates
to its separate stage receipt and the host. The host requires every expected exit=0,
container tool receipt equality and both complete nonempty named-test inventories. Missing,
filtered, ignored-only, wrong-target, failed or empty suites cannot pass. Stale log reuse
is avoided by a new receipt directory on every run.

The always() job step prints all receipt files into retained GitHub job logs even after
failure. No upload action with a floating pin is introduced. For later structured artifact
retention, add a separately pinned approved upload step; it is not assumed here. Source
checkout status is checked before/after. No native completion is claimed if scope skips:
needs:scope and docs_only != 'true' remain exact; uncertainty uses existing full fallback.
All other Python/contract/licence/ordering jobs and classifier remain unchanged.

## Post-acceptance construction and test discovery, explicitly not run

After exact tool/licence and environment release, install the five accepted native inputs
and the real K1 target, then construct the final image. The following reviewable commands
use A's checksum-bound recipe plus [offline-cache.fragment](offline-cache.fragment).
The fragment copies only native build inputs, verifies installed-layout hashes, runs
`cargo fetch --locked` for the complete locked graph (all targets), and removes the seed.
It adds no new dependency/tool, no stub native implementation, and does not compile.
Use a build context excluding native/target and local caches; no unreviewed apt step.

```sh
# Future authorized construction only; never executed by this preparation task.
cat docs/reviews/U4-A-toolchain-v1/Dockerfile.engine.proposed \
    docs/reviews/U4-B-final-reconciliation-v1/offline-cache.fragment > "$RUNNER_TEMP/Dockerfile.u4"
docker build --platform linux/amd64 --iidfile "$RUNNER_TEMP/u4-builder.id" \
    -f "$RUNNER_TEMP/Dockerfile.u4" .
```

Capture actual build logs/image ID, archive/cache inventory and checksums tied to A's lock.
Verify all 27 crate identities/notices and the resolved features with the final image,
run the inspect stage and prove offline fmt/clippy/deny/test discovery works with network
disabled. Decide authorized private immutable image distribution and capture its actual
RepoDigest; freeze that exact value in the job. Do not publish the image publicly under
this proposal, substitute its base digest or claim Dockerfile bytes are a built image.
Any additional tool/OS layer needed by these discovery checks returns as an exact delta.

A and B freeze actual K1 test names **after A writes the tests** and before qualification,
at a reviewed path chosen for K1 (proposed `.github/native-k1-tests.json`). Required fields:
format=uarch-k1-ci-tests/1, checkpoint=K1, tool_package_commit=83a9a14..., target as above,
modes=[debug,release], all_features=true, nonempty workspace_targets (actual names/kinds),
and test_names retaining actual multiplicities. No such plan/test-name list is fabricated
here. Discovery receipts must come from both modes of the real accepted crate. Review the
names against U-P11a1/1a/2/3/5, fixed delays/zero grants/edges/ordering/arena/ownership and
canonical debug-release semantic output comparisons; counts alone do not verify meaning.
A's accepted private tests can proceed without M or complete later human L1/B profiles.

Future end-to-end controls, in scratch original/fault/restored checkouts: remove source;
empty/ignore/filter the required selection; deliberate Rust failure; wrong rustc/deny/lock
or image; missing release; disallowed licence under current policy; missing offline cache;
semantic debug/release mismatch. Synthetic host tests here verify log/status/identity guards,
not these future native controls. Three-process semantic replay remains a real test task.
Final builder digest/cache/discovery/real debug-release execution are explicit remaining
construction outputs, not reasons to leave the present command/recipe proposal vague.
