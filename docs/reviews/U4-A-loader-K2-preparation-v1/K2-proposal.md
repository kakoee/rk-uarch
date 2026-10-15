# Concrete K2 construction proposal — unapplied

This is Lane A preparation against published baseline `4f3be8f` and the installed M
carriers/K1 library. It is not a public binary, accepted host record, completed result,
native run or first-use release. No native source, protected path, Cargo dependency,
feature, lock or image is changed by this package. All public tests below are **not_run**.

## Python writer, process and parser interfaces

The implemented loader APIs in `rkuarch.workload.mapped` are:

```python
loads_fixed_delay_job(data: str | bytes, *, trusted_registry_hash: str,
                     trusted_profile_hash: str,
                     expected_engine: NativeEngineIdentity) -> MappedEngineJob
load_fixed_delay_job(path: Path, *, trusted_registry_hash: str,
                    trusted_profile_hash: str,
                    expected_engine: NativeEngineIdentity) -> MappedEngineJob
export_fixed_delay_job(job: MappedEngineJob, path: Path, *, trusted_registry_hash: str,
                       trusted_profile_hash: str,
                       expected_engine: NativeEngineIdentity) -> None
```

All three require host arguments; none discovers trust from JSON, cwd, environment,
paths or flags. `validate_job(invocation="test", checkpoint="K2")` calls installed `admit`.
A complete embedded MappedBundle, selected point, assumptions, hardware projection,
registry, profile, clock setup, seed and expected engine must agree. Export reparses
current model data before opening a new exclusive destination. It does not reseal hashes.
A returned model is input data, not a persistent authorization token; nested dictionaries
are mutable, so a later writer must revalidate. No producer, mapper or native launcher
is imported. There is no separate bundle format: the exact installed job embeds the
entire saved-input closure. Bare bundles and old analytic jobs refuse here.

Proposed `rkuarch.engines.native.runner` signatures after release:

```python
encode_request(job: MappedEngineJob, *, host: AcceptedHostBinding) -> bytes
parse_response(stdout: bytes, stderr: bytes, returncode: int,
               *, request_bytes: bytes, host: AcceptedHostBinding) -> MappedEngineResult
run_fixed_delay(saved: Path, *, host: AcceptedHostBinding,
                limits: OperationalLimits) -> tuple[MappedEngineResult, RunReceipt]
```

`AcceptedHostBinding` is a host-internal configuration object built by a reviewed
resolver from the exact published human acceptance record, never deserialized from
workload JSON or constructed by a CLI `--approved` option. It carries that Git commit,
record path/blob digest, loader identity, accepted registry/profile hashes, exact expected
engine identity, build receipt and permitted executable digests. No such record or
resolver is delivered here. A fixture self-hash cannot instantiate qualifying authority.
`OperationalLimits` holds explicitly chosen timeout/output caps, not claimed performance
budgets; freeze their values with the actual first-use corpus. No proposed 5 s/512 MiB
performance limit is silently adopted.

The writer reuses strict parsing and the implemented loader, then emits `canonical_json`
UTF-8 bytes of the entire installed MappedEngineJob, without a new envelope or newline.
One process handles one job. stdin closes at EOF; no persistent stream, newline framing,
length prefix, shell, model building or mapping. Arbitrary JSON whitespace is acceptable
on direct Rust input; exactly one object must consume the stream. Concatenated documents,
duplicate keys at any depth, non-finite values, bad UTF-8 and trailing junk refuse.

Proposed invocation: host-resolved absolute executable, no PATH lookup, argument vector
`[verified_executable, "--protocol", "uarch-engine/3"]`, shell=False, private cwd,
explicit minimal environment. Trust is installed in the immutable build separately from
stdin; the flag selects a protocol and cannot select authority. stdout/stderr are drained
concurrently with bounded buffers; exceeding a declared limit or timeout terminates and
reaps the child and records a failed invocation. Never parse partial stdout as success.
The stdout length limit must admit every mandatory observation in the frozen cases.

| Exit/status | stdout | stderr and host behavior |
| --- | --- | --- |
| 0 | Exactly one complete canonical MappedEngineResult, no newline/banner | Empty; strict parse, canonical-byte equality and installed `validate_result` against a freshly revalidated request are mandatory |
| 2 | Empty | One canonical operational error object with exact keys `code`, `message`, `pointer`; strings only, pointer string or null; no result identity/completion claim |
| 1 | Empty | Internal/I/O failure; operational diagnostic, never a qualifying semantic refusal |
| Signal, timeout, cap, spawn failure | Discard any partial output | Distinct host operational failure, retained receipt |
| Any other status, stderr on success, result on refusal, malformed/duplicate error keys | Refuse | `ProtocolViolation`, no result returned |

The operational error grammar is a proposed stderr convention, not another workload IR.
Freeze the exact code table with B; installed contract error names retain their meanings.
Unknown status/code never satisfies an expected refusal. `parse_response` revalidates the
request and result binding; it cannot confer authority on an arbitrary caller-supplied job.
A request and result's hashes, scope, owners, engine/admission/profile, completed inventory,
observations and counts all remain checked by the installed result validator. Additional
causal checks may strengthen it; no validator condition is bypassed or weakened.

The operational receipt records launch/exit, source commit, manifest, compiler/image,
binary SHA256, resolved origin, build profile/target, stdout/stderr digests, elapsed host
time and RSS only when actually measured. Host metrics are not simulated time and do not
enter deterministic result hashes. Do not synthesize a result on refusal or receipt error.

## Rust binary and validation split

Proposed files under `native/crates/uarch-engine`: `src/main.rs`, `src/public/{mod,wire,
admission,canonical,accounting}.rs` and a deterministic identity generator/build input.
The workspace keeps the existing library and adds a `uarch-engine` binary. The binary
uses `#![forbid(unsafe_code)]` and the same clippy bans. No public implementation is
installed in this task. Interfaces:

```rust
// Names denote exact installed carriers, not a reduced public JSON format.
fn read_one_job<R: Read>(input: R) -> Result<MappedEngineJob, BoundaryError>;
fn validate_fixed_delay(job: MappedEngineJob, host: &BuildTrust)
    -> Result<ValidatedFixedDelay, BoundaryError>;
fn execute(job: &ValidatedFixedDelay) -> Result<OutcomeWithCausality, Error>;
fn result_from_execution(job: &ValidatedFixedDelay, outcome: OutcomeWithCausality)
    -> Result<MappedEngineResult, BoundaryError>;
fn write_result<W: Write>(out: W, result: &MappedEngineResult)
    -> Result<(), BoundaryError>;
```

`ValidatedFixedDelay` is a private adapter/capability holding the original validated
carrier and string-ID/index maps. It has no serialized schema. Sorted canonical job IDs
map bijectively to K1 u32 IDs; public owner IDs map bijectively to dense K1 owner indices
and map back on output. Range/allocation failure refuses, never truncates a u64. Preserve
supplied assignments, dependencies, order and resolved clocks. Reject unsupported scope
before invoking Simulation; do not infer component execution from a fixed-delay input.

Python owns filesystem capture, host acceptance-record resolution, binary-origin checks,
process lifecycle and final installed contract validation. Direct Rust callers still
receive the same duplicate-key/type/unknown-field/version/hash/closure, registry/profile,
clock/seed/engine and scope checks before execution. Rust cannot trust a Python
`validated=true`, request-supplied digest or its own advertised engine string as proof.
Serde derives alone are insufficient: recursive generic maps must reject duplicate keys,
all structs deny unknown fields, integer tokens reject bool/float/string, and every
nested identity follows the installed field-specific exclusion rule. Validate original
closure before reporting scope refusals where the installed contract requires it.

The build embeds an independently accepted trust set (registry/profile identities and
finite case selection) and its computed expected engine identity. Passing another profile
inside a direct-Rust job cannot replace these anchors. The final record joins the computed
identity to the executable; an identity handshake alone does not verify origin. Direct
Rust path/output tests must cover all applicable structural joins as well as Python tests.

## Canonical JSON and dependency decision

Python uses the installed `canonical_json`, `content_hash` and `strict_json_loads` with
existing dependencies. Framing needs std I/O only. The current Rust lock has no SHA-256
implementation. Do not handwrite one or call an unapproved external checksum tool.
Propose the following bounded extension, not installation:

```toml
sha2 = { version = "=0.10.9", default-features = false, features = ["std", "force-soft"] }
# Keep serde_json =1.0.154 and its current std/float_roundtrip features; additionally:
# features += ["arbitrary_precision"]
```

The SHA-2 crate is MIT OR Apache-2.0; its published feature/dependency definitions are
[upstream package metadata](https://docs.rs/crate/sha2/0.10.9/source/Cargo.toml).
`force-soft` avoids SIMD/assembly dispatch; no asm feature is proposed. Exact candidate
transitive pins, licences, checksums and upstream dependency requirements are recorded
in `dependency-candidates.json`: digest 0.10.7, block-buffer 0.10.4, crypto-common 0.1.6,
generic-array 0.14.7, typenum 1.19.0, version_check 0.9.5 and cpufeatures 0.2.17.
Reuse accepted cfg-if 1.0.5 and libc 0.2.190 only if the prospective resolver/feature audit
confirms compatibility. cpufeatures 0.2.17 is additional to the installed 0.3.1, not an
implicit downgrade. No candidate is approved merely because its licence is familiar.
This is a pin proposal, not a claimed Cargo-resolved closure. Before implementation,
accept exact generated lock/feature/target/checksum closure and image-cache extension;
that prospective generation is a separate action. Existing K1 pins are not reopened.

`arbitrary_precision` is required for lossless generic numeric processing of the installed
u128 rational fields; schema-derived typed DTO validation must still distinguish integers
and floats. Do not parse the whole hardware object through f64. Preserve the existing
normalized model rules, compact separators, Unicode and negative-zero normalization,
lexicographic keys and top-level-only self-field exclusion. Emit finite f64 using Python's
shortest-roundtrip conventions, including `1e-07`, `1e+20` and integral `.0`; plain
serde_json output is not proven equivalent. A dedicated formatter using the existing
serializer's shortest digits and Python exponent/fixed notation rules is proposed,
subject to differential verification; **canonical parity is an open implementation gate**.
No new float-format crate is currently proposed. If the existing formatter cannot meet
parity, return with an exact additional dependency proposal rather than relaxing hashes.

Require both installed canonical vectors plus Unicode/control escaping, -0.0, all
float formatting cutovers, smallest/largest finite f64, tie-to-shortest cases, random
finite bit patterns, integer 2^53±1/u64 max/u128 max, reordered objects and all M input
fixtures. Compare Python and Rust canonical bytes and SHA256, normalized DTO defaults,
and refusal of duplicate/unknown fields and bool→integer coercion. Cross-version hashes
must fail; never substitute RFC8785/JCS or hash raw incoming whitespace.

## Acyclic identity, build origin and first-use lifecycle

Freeze a canonical build-input manifest with exact path/digest leaves: all Rust source
and reached modules; Cargo workspace/crate manifests, lock and selected features/target;
compiler commit/component pins; image/base recipe and tools/linker inputs; accepted
public schema/canonical rules; identity-generator source and build configuration; and
accepted trust-set content. Include the Python boundary/contract source manifest in the
host binding, and include any Python inputs actually used by build generation in the
build closure. Audit all actual reads rather than guessing a file quota.

Use this dependency order:

1. Accepted semantics/schema, source manifest, canonical format and tools/lock/features.
2. Profile/registry candidates containing only graph/point/spec/clock/seed/case identities;
   neither profile nor registry contains engine, job, binary or final receipt hashes.
3. Reviewed independent build trust set binds those candidates. Manifest hashes it as
   an input. Implementation identity is the canonical manifest content hash; model
   implementation hash covers the exact fixed-delay/accounting semantics source subset;
   compiler_lock_hash covers exact compiler/lock/features/target. Generated identity
   source is a deterministic function of this manifest plus generator source. It is a
   derived build output, not recursively included in its own input manifest.
4. Build debug/release in the accepted image from the exact source export, record actual
   files/environment read and generated identity output. Byte-verify generated output
   against its declared derivation. Final executable SHA256 and build profile are receipt
   outputs, not inputs to engine implementation identity. Same logical implementation
   identity may bind separate exact debug/release digests in the final host record.
5. Construct complete jobs using the actual engine identity; their hashes are outputs.
   Execute the released public suite only after acceptance of the exact final record
   binding profiles, registry, engine, binary digests, build receipt and loader identity.

The build record may cite a source Git commit for provenance but the implementation hash
must not hash the final commit containing its own generated record. No binary digest in
its own embedded identity; no job/profile/engine cycle; no placeholder expected engine in
an approved record. Profiles may be frozen before building, but acceptance of actual
engine/binary binding follows construction. Coordinator must explicitly separate a
bounded implementation/build release from final qualifying first-use approval.

Build into a private output directory, verify the intended Cargo target artifact from
fresh metadata, record its SHA256 and embedded manifest identity, and install into a
host-controlled immutable location. Resolve symlinks and verify location, regular-file
mode, ownership and digest immediately before launch. Execute that verified immutable
inode/path; refuse if the immutability/TOCTOU premise cannot be maintained. Reject PATH
shadowing, stale debug/release swaps and a different executable advertising the same
identity. Building a library or reading Cargo.toml is not testing a K2 executable.

Any change to accepted trust content, schemas, canonical code, source/tool/lock/features,
compiler or image repeats the affected audit/build/host-binding lifecycle. Registry and
profile self-rehash is never approval. Changes affecting selected generation inputs
trigger the bounded U0002 freeze/two-human-generation/audit/adoption proposal and withhold
the affected source from green main; no automatic regeneration or exclusion.
