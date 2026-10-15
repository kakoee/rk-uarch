# Observed B checks and remaining construction evidence

Final B local source subject is 892b9ee00c485718082e8ea9a765578cbd64d684, with the same
native source as A's 357dea8ee43ae098c284c672a44e6a6cf8482d27. Earlier successful controls
at ba948995 were superseded by the final-source run after A added the stdout replay sink.
These are B executions, independently of A's retained local receipts. No hosted CI result
or native qualification is inferred.

## Exact accepted image — newly observed B execution

The earlier runtime dependency was resolved by starting the already installed Docker Desktop
application. The exact accepted recipe plus unchanged cache fragment built successfully.
Final local image ID is `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`;
local tag `rk-uarch-k1-builder:u4-b-e9f69f414983`. [Inspection](image-inspection.json),
[construction](image-construction.json), [external commands](image-command-receipts.json),
[inspect-stage command receipts](image-inner-receipts.json), [tool paths](image-tool-paths.txt)
and [actual native binary hashes](image-tool-binaries.sha256) bind the execution environment.

- Full rustc/cargo/rustfmt/clippy/cargo-deny receipts match the accepted versions. Rustup
  component and installed-target discovery pass; no recipe correction or additional package.
- All 27 cache archives/notices and both full/selected metadata graphs pass. All verification
  containers use --network none and source mounts are readonly. [Cache proof](image-cache-results.json).
- 131 installed OS packages match A's immutable-base inventory; all 113 retained copyright
  files match. The first unfiltered dpkg query included removed wget's residual config record;
  checking installed status resolved the count without any image change. [OS/tool result](image-os-tool-results.json).
- Actual 19/19 debug and 19/19 release tests pass; all six fresh-process canonical payloads
  have SHA256 30c1e07014f238784ba570a367db1584847134280b2e4190c91761b9b179094a.
  [Verification](image-verified.json), [six payload receipts](image-replays.json).
- Real missing-source, compile/test, selection, cache/toolchain and current-policy controls
  refuse as intended. A's three semantic faults fail in both modes and six targeted restorations
  pass; full restored suites pass. The actual release-only byte mutation is rejected and
  restored output equals baseline. [Fault completion](image-fault-controls.json),
  [replay refusal](image-replay-refusal.json).
- The exact corrected native-container.sh inspect/checks stages, both metadata guards and
  the full nonempty results guard pass in a separate source export. [Template result](template-results.json),
  [template commands](template-command-receipts.json). The registry-pull host wrapper remains
  unexecuted because private publication/access has not been authorized.

Two image-control attempts were correctly refused and retained in
[retry receipts](image-control-retries.json). First, the Docker daemon disconnected; it was
not a native failure. During recovery Docker/Desktop reported a different transport version;
no update/settings command was issued, and the image ID/layers were reverified unchanged.
[Start/recovery](image-desktop-start-and-recovery.json) records the unknown cause explicitly.
Second, restoring source mtimes left a mutated artifact in the old Cargo target directory.
The unexpected test failure was not credited. Selection controls now use the separately
verified restored target; the complete corrected image fault sequence passes. No compiler,
feature, model or dependency substitution was needed.

All 59 source-export files are unchanged after image verification and exactly restored after
faults; the template export's 60 files are also unchanged. [Isolation](image-isolation.json)
and template/fault receipts record those assertions. Filesystem scratch trees, tools and
target/cache directories are removed. The named local image and Docker-managed build cache
remain; no global prune was run. These are local Linux-image executions, not hosted CI,
independent review, native qualification or a K1/G3a/U4 closure verdict.

## Existing-host execution — not a constructed image

[46 exact command/status/stdout/stderr receipts](local-command-receipts.json) record the
final run. [Environment](environment.json) binds actual tool paths and binary SHA256s,
full accepted-version equality, source commit and WSL kernel. The explicit existing
`stable` alias resolved to Rust 1.99.0/full b940084d7eb6a299eb4bfeb8e34901bc051e7ac4;
no alias movement, installation or different compiler was accepted. The native toolchain
file remains the exact accepted 1.99.0 pin. The [cargo-deny archive and extracted binary](deny-tool.json)
were checksum/version verified in the disposable work directory, never installed on the host.

| Check | Newly observed B result |
| --- | --- |
| Installed manifests/lock/toolchain/deny | All five accepted installation hashes pass before execution |
| Cache and notices | Fresh scoped CARGO_HOME, locked fetch, all 27 archive checksums and retained notice hashes pass; [cache receipt](cache-results.json) |
| Full/target metadata | 27 full-lock crates, 26 Linux-selected crates; exact features and registry/path/source checks pass; [metadata receipt](metadata-results.json) |
| fmt, clippy, cargo-deny | fmt check, all-target/all-feature clippy -D warnings, accepted pinned deny licences/bans/sources pass; only unused licence allowance warnings |
| Discovery and tests | uarch_engine library, 19 names each once in debug and release; 19/19 pass in each; no ignored tests or empty doc-test credit |
| Fresh-process replay | Three processes per mode, all six exact private payloads equal; [six hashes](replays.json), [one exact payload](canonical-private.json) |
| Empty/ignored/filtered selection | Cargo exits 0, but the frozen-name/multiplicity guard rejects each incomplete execution |
| Missing source, compiler error, failing test | Actual Cargo exits 101 with intended diagnostics; exported source restored |
| Absent cache/toolchain | Empty CARGO_HOME under offline mode exits 101; nonexistent toolchain with auto-install disabled exits 1 |
| Licence negative control | Exact unexcepted policy exits 4 for Unicode-3.0; accepted policy remains passing |
| Three A semantic faults | Rounded period, insertion-before-target ordering, zero work bypassing owner; six actual faults (both modes) exit 101 with A's diagnostic anchors; six targeted restorations pass |
| Release-only byte drift | Actual changed Rust serializer still passes its replay test, but the six-payload comparison rejects its release-only extra byte; exact restored payload passes |
| Final restoration | Full 19/19 debug and 19/19 release suites pass after faults; all 59 exported file bytes/mtimes restored |

The canonical payload SHA256 is
`30c1e07014f238784ba570a367db1584847134280b2e4190c91761b9b179094a`, matching A's published
private result. [Native completion](local-results.json), [source isolation](local-isolation.json)
and [real replay mismatch refusal](fault-release-replay-guard.json) record the boundaries.
A's three exact fault anchors are consumed by path/hash in [fault-inputs.json](fault-inputs.json),
not read from A's uncommitted tree. [Release-only fault](replay-mutation.json) is B's bounded
extra control. These mutations never reach live native sources. Proptests use their normal
local configuration; B does not claim A's separately recorded seed for these runs.

The first local attempt stopped at the old B metadata guard, which compared the 26 selected
crates to all 27 locked entries. [Correction receipt](metadata-correction.json) records that
actual refusal. The corrected run checks both exact graphs rather than exempting arbitrary
missing packages. One mistyped full revision was also refused by Git before any source
export or native execution; the final run uses Git's resolved published commit.

## Ordinary checks and live CI scope

[Ordinary checks](ordinary-checks.json): **58 passed** in 1.18s with explicit pyproject.toml,
root, no pytest/bytecode cache and external temporary directory. They cover patch identity,
unknown/missing patches, postimage/preimage drift, actual temporary reverse/forward apply,
image/base identity, cache/notice drift, six-replay equality, failure receipt preservation,
mutation rollback, old/new host guards, third-party scope, prompt sync and CI classification.
They do not execute a Docker/native image or count synthetic parser controls as native tests.

Repository ruff, strict typecheck of the new patch checker, bash syntax checks, the live
isolated patch checker and **strict vendor currentness all pass**. The vendor module origin
is the authorized B clone. Compared live file bytes and modification times remained unchanged
through the test batch; counts and assertion are in the receipt, not a source-wide manifest.
All filesystem scratch exports, downloaded host tool/crate archives and Cargo build directories
were removed before publication; the verified local image/Docker build cache remain. Driver identities are retained in [drivers.json](drivers.json).

The only installed workflow edit replaces the unconditional numbered-patch failure with
`.github/check_third_party_patches.py`. Its [identity record](register-identity.json) binds
A's final patch bytes, approved base register and installed postimage. It adds no broad
artifact-support Python module under scripts/, and strict source/artifact currentness stays
intact. The existing native job remains the historical unpinned job and is **not qualifying**;
no new native job or placeholder workflow was installed. Markdown classification is unchanged.

## Still unobserved or unauthorized

Registry publication/RepoDigest, authorized hosted pull/access, qualifying hosted correctness,
independent review and K1 acceptance remain pending. The existing-host results above remain
separate from the later image results; A's upstream/archive evidence is inherited, while B's
image/runtime/cache/native receipts are new. A read-only proposed-package API probe returned
404, which does not establish that a private package is absent. No registry mutation occurred.

[Construction/access](construction.md) names the exact verified publication subject, private
GHCR destination and main-only secret access proposal. It deliberately avoids granting this
public repository general package access, which GitHub warns can extend to forks. No credential,
environment, publication, paid provisioning or billing change is authorized or performed.
M installation/policy migration/generation/adoption and human-adoption skip resolution remain
outside this work. Full later B/human L1 and runner registration keep their existing boundaries.
