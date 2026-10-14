# U4 A — immutable K1 toolchain and licence proposal

**Proposed, not accepted or installed.** This package resolves K1 prerequisites only.
No native kernel was implemented, built or executed; no shared toolchain, image or host
was installed. Temporary Cargo metadata/lock resolution and licence inspection ran inside
the Lane A clone. Local installed Rust was an inspection tool, not selection authority.

## Exact recommendation

- Rust **1.99.0**, released 2026-10-01, target **x86_64-unknown-linux-gnu**, minimal profile
  plus rustfmt/clippy. [pins.json](pins.json) records full compiler commit, upstream manifest
  hash, component versions and both archive formats/checksums. The manifest digest was
  independently compared with its upstream `.sha256`. [Primary release announcement](https://blog.rust-lang.org/2026/10/01/Rust-1.99.0/).
- Exact direct requirements: serde **=1.0.229** (`derive,std`, no defaults), serde_json
  **=1.0.154** (`std,float_roundtrip`, no defaults), dev-only proptest **=1.12.0** (`std`,
  no defaults). No fork, timeout, bit-set, preserve_order/indexmap, SIMD, cxx or loom feature.
  `float_roundtrip` supports parsing; it does not prove Python canonical float spelling or
  duplicate-key rejection. K2 must test those independently.
- [Cargo.lock](Cargo.lock) locks all **27 external crates**, including target-conditional
  packages. [crate-closure.json](crate-closure.json) records versions, checksum, resolved
  features, repository and inspected notice-file hashes; [crate-notices.json](crate-notices.json)
  contains those notices. Resolution used crates.io primary registry metadata/archives.
  Select MIT where available; unicode-ident additionally requires Unicode-3.0. No licence
  is inferred from a package name. Target-conditional `r-efi` permits MIT, so LGPL is not
  selected. memchr permits MIT, so Unlicense is not selected.
- cargo-deny **0.20.2**, official x86_64 Linux musl binary. [cargo-deny.json](cargo-deny.json)
  records URL/checksum, matched against GitHub's asset digest. The separate tool's upstream
  [Cargo.lock](cargo-deny-Cargo.lock), MIT/Apache notices and source URLs are retained.
  It is run as a tool, not linked into the engine. This pin has a **global** `--config`
  option before `check`; B's CI must use the tested invocation below.
- Container base is official Rust **1.99.0-slim-bookworm**, immutable Linux amd64 manifest
  `sha256:ba81bc3eaa4422af576c0262515d96b0111a628a6ccc2c86557cf55c9a4bbee0`.
  [container.json](container.json) also pins the index, config, layers, source revision and
  upstream build history. Every layer was downloaded and its digest verified for read-only
  package/copyright inspection; no container was run. [os-packages.json](os-packages.json)
  lists the actual 131 installed packages, including GCC12 and glibc; [os-copyrights.json](os-copyrights.json)
  preserves 113 installed copyright files, with hashes. Copyright symlinks/share-common
  arrangements explain why these counts differ; they are not a claim of 131 unique licences.

[Dockerfile.engine.proposed](Dockerfile.engine.proposed) inherits those exact OS bytes
without apt operations and adds checksum-bound gzip rustfmt/clippy archives and cargo-deny.
Thus no moving OS repository or guessed package version enters the proposed build. The
[upstream recipe](upstream-Dockerfile) and its exact source URL/digest are in
[upstream-sources.json](upstream-sources.json). Upstream used Debian bookworm and rustup
1.29.1; those bytes are fixed by the image digest. Rebuilding the upstream tag from its
historical apt commands is not this recipe. Future image refreshes need new pins/inventory.
The proposed recipe has **not** been built: building it and testing rustfmt/clippy discovery
inside it is the first post-acceptance environment check, not a claimed passing control.

## Licence decision and observed controls

[proposed-ADR.md](proposed-ADR.md) gives exact prospective text. Unicode-3.0 is outside the
installed allow-list; it appears in `(MIT OR Apache-2.0) AND Unicode-3.0` for unicode-ident
1.0.27, so selecting MIT does not remove it. This is a specific exception, not a new global
permission. It reaches serde derive via proc-macro2/syn. The crate includes its Unicode
notice. The run-only OS/tool scope also needs explicit treatment: GCC/binutils, glibc,
Debian utilities and embedded tool components include GPL/LGPL and other licences outside
the engine-crate allow-list. cargo-deny does not audit an OS image or compiler distribution.
No permissive-only-container claim, modified-library distribution, static glibc linking,
public image publication or proprietary licence reclassification is proposed.

Temporary commands (CARGO_HOME pointed inside the disposable resolution directory):

```sh
cargo generate-lockfile --manifest-path pin-resolution/Cargo.toml
cargo metadata --manifest-path pin-resolution/Cargo.toml --format-version 1 --locked
cargo-deny --manifest-path pin-resolution/Cargo.toml --config deny-current.toml check licenses
cargo-deny --manifest-path pin-resolution/Cargo.toml --config deny-proposed.toml check licenses
```

[current-policy control](license-current.txt): **fails for Unicode-3.0**.
[proposed-policy control](license-proposed.txt): **licenses ok**, with unused-allowance
warnings. Both explicitly ignore only unpublished first-party workspace licence declaration
(`publish=false`); every registry dependency is checked. The repository has no project
licence to invent for the new private crate. This exact private-workspace setting is also
part of the proposed decision. An earlier CLI-order error and initial unlicensed-workspace
failure were corrected before these recorded controls; neither was treated as the Unicode
refusal. No advisory/security pass, compiler reproducibility or native test pass is claimed.

## Decision, installation and next task

Smallest K1 decision: Javid accepts the pins/feature closure and exact scoped licence text
at the final published package commit. No M installation or performance-budget decision is
required for private K1 coding. B owns CI and must reconcile its actual workflow commands
with these pins before K1 CI evidence counts.

After acceptance, in order:

1. Human installs the prospective U0011 tool/licence addendum (number remains coordinator
   owned); A adds the accepted register entries to third_party/LICENSES.md.
2. A installs `workspace.Cargo.toml` as `native/Cargo.toml`, `Cargo.toml.proposed` as
   `native/crates/uarch-engine/Cargo.toml`, the committed lock/toolchain and proposed deny
   config as `native/{Cargo.lock,rust-toolchain.toml,deny.toml}`. The package's metadata-only
   scratch target is not delivered as a native implementation; K1 authors the real crate.
3. A installs the accepted container recipe; build it in an approved environment and verify
   exact rustc/cargo versions, target, rustfmt/clippy and cargo-deny availability. No shared
   server installation is required. Fetch the accepted lock once, then build with
   `cargo build --locked --offline --target x86_64-unknown-linux-gnu`.
4. B installs its independently owned CI proposal after reconciliation. Execute fmt,
   clippy `--all-targets -- -D warnings`, debug/release tests, exact license check and
   determinism cases on real K1 source. Cargo commands must fail on missing kernel source,
   not turn an empty workspace into successful native evidence.

The next A task is K1's private time/event/arena/wheel/owner/fixed-delay implementation with
U-P11a acceptance 1/1a/2/3/5 written first, including owner-granted zero transitions.
Public protocol, serde fixtures and subprocess work wait for K2. No model, measurement,
performance ceiling, native CI pass or sprint closure is supplied here.

## Reconciliation with published B CI

B `f42e169b10a25ab3dd8bb05b54d3783fbbeddbc2` is integrated. Its exact offline/all-features
cargo-deny license/bans/sources command passes the proposed policy in
[ci-command-control.txt](ci-command-control.txt); no native target was built. All27 downloaded
crate archives were also independently SHA256-compared with Cargo.lock checksums.
[version-receipts](version-receipts/) records read-only outputs from the existing matching
1.99.0 tools and the checksum-verified temporary cargo-deny binary. These match the selected
upstream compiler commit; they are **not** observations from a built proposed container.
The container must reproduce them after acceptance.

The base image plus recipe does not contain Python3 for B's guard or an offline Cargo cache.
It cannot fill `__A_LINUX_AMD64_IMAGE_AT_SHA256__` as a final builder yet. B must place its
stdlib guard on the hosted runner outside the container, or separately propose/pin its
Python OS layer; the locked cache and final builder digest follow accepted environment
construction. A publishes no guessed final image digest or test-name list. Required K1
names come from real implementation, before the CI guard is frozen. B owns these workflow
changes; A has not edited its template. See the M package's
[peer reconciliation](../U4-A-M-package-v1/peer-reconciliation.md) for exact remaining ownership
and revised effort. This environment-completion work does not require reopening S-CI or
waiting for self-hosted runner registration.

[native-inputs.sha256](native-inputs.sha256) is the concrete checksum file for the proposed
installation layout, used from `native/`. It binds workspace/crate manifests, lock,
toolchain and deny configuration; it intentionally does not guess future kernel source.
The exact register additions are in [register-additions.md](register-additions.md).

The completed [OS copyright map](os-copyright-map.json) resolves **all131 installed
packages** to an exact copyright file/hash, including explicit directory-symlink chains;
no package is unresolved. [os-common-licenses.json](os-common-licenses.json) retains the
image's referenced common licence texts, and [image-tool-notices.json](image-tool-notices.json)
retains compiler distribution notices found in the pinned layers. These are licence
provenance artifacts, not an installation or a second source snapshot system.
