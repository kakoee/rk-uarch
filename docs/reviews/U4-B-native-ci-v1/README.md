# U4 B native Linux CI proposal

**Follow-up:** the concrete replacement template and host/container placement are in
[final CI reconciliation](../U4-B-final-reconciliation-v1/ci-reconciliation.md).
This first-checkpoint proposal and its original checks remain historical.

Status: concrete job template and tested nonempty guards, **not installed or native-ready**.
At starting main `f58e07828fa7a953b06800b227b948d7e9e71a88`, native/Cargo.toml has
members=[]; no native tests ran. A's immutable pin package was not yet published.
[Template](native-job.yml.in) replaces only jobs.native after separate acceptance/release.
The live .github/workflows/ci.yml and classifier are unchanged: preserve needs:scope,
Markdown-only skip and `docs_only != 'true'` full fallback. Non-Markdown proposal files
in this handoff correctly select full existing CI; its source-empty native skip is no
new evidence. Contract/licence jobs retain their existing unconditional checks.

S-CI ownership and hosted Linux correctness are already accepted. This is not another
runner-policy vote. Registration, controlled-host performance and an executed self-hosted
nightly remain separate; no readiness assertion follows from a configured job.

The template pins checkout to `11bd71901bbe5b1630ceea73d27597364c9af683` (v4.2.2,
resolved using `git ls-remote https://github.com/actions/checkout.git refs/tags/v4.2.2`
on2026-10-14). It uses a digest-bound Linux amd64 image containing approved Rust,
rustfmt, clippy, cargo-deny, Python and the offline dependency cache/vendor inputs.
The hosted VM label is operational, not an immutable OS or a performance environment;
the compiler/userland recipe and image digest supply the accepted build identity.
No cargo install latest, rustup stable, dependency resolution update or licence acceptance
runs in CI. Pinned cargo-deny checks licenses, bans and sources offline; advisory database
freshness is a separate prospective policy, not silently downloaded by this job.
Cargo-deny does not audit the compiler, OS packages or all build-tool licences.

Only A-package-dependent fields remain unresolved:

| Template field / exact input | Required A publication and reconciliation |
| --- | --- |
| __A_LINUX_AMD64_IMAGE_AT_SHA256__ | Immutable image digest, architecture, base digest, OS package snapshot/recipe and tool/dependency cache; licence inventory |
| __A_EXACT_RUST_RELEASE__ and version receipt paths | Rust release/commit/target x86_64-unknown-linux-gnu, checksums, exact rustc/cargo/rustfmt/clippy outputs; no moving channel |
| __A_RELATIVE_CHECKSUM_FILE__ | Exact native Cargo.toml/Cargo.lock/feature graph, toolchain and deny-config hashes; approved integrity list limited to build inputs, not a source-wide manifest |
| __A_DENY_VERSION_RECEIPT__, __A_DENY_CONFIG__ | Exact cargo-deny release/build digest and allow-list/config; human resolution of every exception, including Unicode if present |
| __A_REQUIRED_NATIVE_TEST_NAMES_JSON__ | Nonempty exact K1 test names/multiplicities and required target/features; later K2 adds actual public-boundary selections |

The intended invocation is workspace/all-targets/all-features at the accepted first-stage
serde/serde_json/dev-proptest graph. If A publishes another feature/target selection,
reconcile the literal flags and lock/licence closure before installation; never quietly
remove a target to pass. If A publishes a base image rather than a complete builder image,
the exact checksum-verified compiler/deny/offline-cache build recipe and resultant digest
must be completed first. No placeholder is a pin. No `ready to install` claim until each
field, target and tool CLI is checked against A's exact package and human acceptance.

[ci_guard.py](ci_guard.py) checks real Cargo metadata members, local nonempty test target
sources, complete frozen test-list equality, actual named successes and Rust summary
counts. Empty, ignored-only, filtered, failed, missing, changed or incomplete runs refuse.
Both debug/release commands use pipefail; failing cargo cannot be hidden by tee. Four
[guard tests](test_ci_guard.py) exercise synthetic logs/temp files only. These establish
checker behavior, not actual Rust formatting, clippy, licence or test outcomes.

Required future CI refusal controls: remove source/workspace member; empty required list;
ignored-only/filter all tests; deliberate Rust failing assertion; wrong rustc/deny/lock
pin; release step absent; disallowed licence; network absent with complete offline cache.
Run each in a disposable checkout with original/restored controls and receipts on the
approved Linux image. Guard unit tests do not establish these end-to-end controls. K1
must also publish canonical semantic output and compare debug/release bytes; the job's
two passing suites alone do not establish replay equality. Three fresh process, saved
producer-disabled/public K2 and observation controls remain their own required tests.

Record checkout SHA, accepted pin-package SHA, tool outputs/image digest, exact command
statuses, test counts and log identities in the operational receipt. CI result is observed
asynchronously; never report push success as a hosted pass. No workflow, tool, native
source, lock, licence policy or protected path is installed by this proposal.

Local guard invocation:

```sh
python3 -B -m unittest discover -s docs/reviews/U4-B-native-ci-v1 -p 'test_*.py' -v
```
