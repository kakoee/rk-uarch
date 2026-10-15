# Exact records, reads and C1 review

Reviewed A subject1a52fa8's six record models/mirrors, identity-and-reads.md and construction
plan4a5cbb16… . The nine new host checks reproduce all six schema files byte-for-byte,
exercise positive synthetic **in-memory metadata** shapes, identity/mode/self-reference
refusals, and lock-allowlist drift controls. They create no real HostRecord or authority.
Shapes are not a cross-file resolver. The future resolver behavior below remains unimplemented.

| Record | Binding and order reviewed | Executed shape versus pending behavior |
| --- | --- | --- |
| BuildTrust | Engine-free semantics/registry/profile/finite case/corpus inputs, construction-test-only. Profiles precede binary; no job/engine/binary/final record reference. | Unknown engine/authority fields refuse. Actual profile/registry content hashes, sorted unique case membership, source/spec/clock/seed/outcome joins require future resolver checks. |
| ToolInputs | K1 pins, compiler commit/release1.99.0, x86_64 Linux target, actual image, lock, full/target metadata/features/licences/checksums/linker/OS/flags. | Exact required shape and mirror checked. Actual files, accepted tool origin and dependency review remain future receipts, not inferred from schema literals. |
| BuildInputs | Source commit and sorted unique path/digest/role inputs, trust/tool hashes and file bindings, model subset, both modes, output paths and declared environment. | Duplicate/output-input collision and unknown model path/mode faults refuse. Actual immutable source commit, paths/symlink confinement, reached reads and canonical content hashes still require implementation. |
| BuildReceipt | Build-input hash=engine implementation hash, mode/target/image, executable, generated identity, actual read/env/compiler/build/origin/software-path receipts. | Hash mismatch refuses. A wrong image or compiler/tool join can still be shape-valid; resolver must compare actual ToolInputs, executable bytes and all receipts. |
| HostRecord | Engine implementation/compiler/model hashes match build/tool/model fields; separate debug/release executable+receipt bindings, exact profiles/registry/jobs/corpus, independent review and human decision. | Internal identity mismatch or duplicate modes refuse. A foreign registry/profile or identical dummy executable bindings remain shape-valid; no actual binary verification or approval is thereby established. |
| HostSelector | External human-installed repository/acceptance commit/path/record byte digest; record does not include its own containing commit. | Shape accepts a dummy selector; it never proves installation. Resolver must obtain it from independently controlled host configuration, reject caller overrides and verify exact committed blob. |

One order: reconciled semantics/source/tool inputs → engine-free profiles/registry/corpus →
BuildTrust and ToolInputs → BuildInputs → generated identity → actual debug/release binaries
and receipts → jobs and human/reviewer subjects → HostRecord → externally installed selector.
Implementation hash is content_hash(BuildInputs); compiler_lock_hash is content_hash(ToolInputs);
model hash is the sorted array of the selected SourceInput **objects**, including their byte
hashes, not filenames. The test changes a model byte hash and observes a different subset hash.
Generated identity outputs, binaries, jobs, receipts, BuildInputs itself and final HostRecord
are excluded from upstream source inputs. Decision/review files bind the upstream subject,
not the eventual record containing them. This avoids self-reference; actual read auditing
must enforce it. Equal logical identity across modes requires two separately verified real
executables. A library-only K1 source pin or advertised identity string cannot substitute.

Canonical record hashes and file-byte hashes have separate roles. Future resolver must check
both, canonical UTF-8, duplicate joins and inventory completeness, normalized confined paths,
source commit and actual source bytes, actual generated-output derivation, target/mode/image,
executable immutable origin through launch, exact loader/schema closure and finite decision
scope. Schema shape permits several deliberately tested cross-file mismatches; this is an
explicit construction obligation, not a claim that a working resolver currently refuses them.
No additional A schema revision is requested for behavior already assigned to that resolver.

## Existing closure and prospective edges

Three newly executed private audits cover unmodified A source, exact A patch and A+B guard.
Each imports26 local loader files, including package initializers, from its own export.
The only loader byte delta in the proposed exports is mapped.py. Each actual load opens only
its explicit saved job and takes separate synthetic unit anchors; no implicit authority read.
The selected generator-support map independently recomputes to56 and is byte-for-byte equal
to the installed selected map (hash676b1250…); there is **no56 quota**. Strict artifact currentness
and generated-schema freshness pass in all three exports. Counts/hashes/origins are in the
three audit receipts. No lifecycle is required by these tested proposal bytes alone.

Prospective edges remain: identity generator imports/includes/build scripts and their actual
Python initializers; Cargo configuration, lock/features/all-target metadata/archive sources;
canonical/schema/model semantic inputs; trust profile/registry/corpus file reads; generated
identity derivation; build environment/linker/OS inputs; host selector, exact committed
record/decision/review and executable reads. None was observed by this loader audit. If an
actual later reverse import or data dependency reaches the nominal-generator roots, recompute
support and hold dependent acceptance for the exact human freeze/generation/audit/adoption
lifecycle. Do not exclude an inconvenient dependency or regenerate during this task.

## C1: executable bounded experiment, not a resolved or accepted closure

**Disposition: the exact plan is sufficient for a separately authorized fail-closed C1
resolution/fetch experiment. No guarantee that its constraints resolve.** C1 can be decided
separately from the notification correction. It grants no C2 probes, K2 implementation,
live source/lock/cache change, new image, C3 publication or remote work.

The existing lock SHA256 is
`3df872c1e8c445b179dd8162430a5265fa770a62bcfa009009dae49d878bf084`.
The plan exactly retains its28 name/version/source/checksum tuples (27 registry packages
plus the workspace root). Eight only permitted additions are sha2 0.10.9, digest0.10.7,
block-buffer0.10.4, crypto-common0.1.6, generic-array0.14.7, typenum1.19.0, version_check0.9.5,
cpufeatures0.2.17; the old0.3.1 remains. All eight checksums/licence/source provenance match
the retained candidate metadata. Our synthetic lock-entry tests reject missing old/new,
extra/duplicate, changed version/checksum and Git-source entries, then restore the control.
They are allowlist tests, not a fabricated Cargo.lock or dependency graph.

The plan's direct changes are sha2=0.10.9 without defaults, std+force-soft, and
serde_json=1.0.154 adding arbitrary_precision to std+float_roundtrip. serde1.0.229 and dev
proptest1.12.0 remain pinned with their accepted features. Check full unified features against
the existing baseline plus the declared candidate feature lists; no optional asm/OID/MAC/RNG/
zeroize/scale-info branch. Existing old dependencies/features are not erroneously banned merely
because a word appears in forbidden_new_features. The licence field's crates.io API URL is
provenance, not permission for another network endpoint: actual retrieval stays restricted to
index.crates.io and static.crates.io/crates, with canonical Cargo registry source identity.

Operational sequence after C1 permission, using accepted local tools only:

1. Verify actual tool paths/full versions/image against the accepted K1 receipts. Existing
   imagee9f69f41… and Rust/Cargo1.99.0/cargo-deny0.20.2 remain inherited tool inputs here;
   no Docker or Cargo command was run to reassert availability. If absent/mismatched, stop.
   Use a fresh pinned export and private CARGO_HOME/CARGO_TARGET_DIR. Copy an accepted cache
   only after digest checks; no writable live cache mount, credentials or global config.
2. Make only the plan's scratch manifest change. Use targeted path-root update and precise
   new-package updates; retain every intermediate lock/error. Index exploration is not
   package acceptance. Inspect final full lock against the exact retained/additional tuple
   predicate **before metadata/fetch can download archives**. No broad update or synthetic
   constraint crate. Unsatisfied pins or a required out-of-allowlist package stops C1;
   no version widening or unapproved archive download.
3. Capture actual `cargo metadata --locked --format-version 1`, then with
   `--filter-platform x86_64-unknown-linux-gnu`; retain both full and target graphs, complete
   feature tree and requested/selected features. Use the private target and cache. Fetch
   only locked allowlisted archives, with no compile/build-script execution. Full metadata
   may require permitted old non-target packages; a Linux-only report cannot hide drift.
4. Disable networking and repeat both metadata views and fetch with `--locked --offline`.
   Inspect actual archive SHA256, extracted source, licence/notice files and expressions.
   The existing accepted cargo-deny pattern is `--locked --offline --all-features --config
   deny.toml check licenses bans sources`; verify the candidate workspace feature graph is
   the declared one and archive its output. Do not enable advisory/network fetch implicitly.
5. Return exact source diff, starting/candidate locks, both metadata views/features, archives/
   licences/cache/tool/command/network/error receipts and preservation. Any checksum/source/
   feature/version or offline-availability failure is a refusal, not permission to install.

Actual source/licence contents and graph satisfiability were not independently obtained here.
C2 remains separately authorized offline standalone canonical/hash probes, including4096
frozen finite floats, exact Unicode/u128/canonical parity, reserved numeric marker refusal,
real scalar backend/cfg/link/disassembly evidence and auto-vectorization findings. force-soft
alone proves none of that. C3 remains a separate image/distribution decision under U0024;
C1 does not reopen existing K1 votes or resume deferred infrastructure.
