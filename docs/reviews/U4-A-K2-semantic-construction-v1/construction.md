# Disposable construction plan and permission boundary

Nothing in this document has been executed. No network construction is authorized in this
follow-up. The exact request is recorded in construction-plan.json; candidates remain
metadata, not a Cargo-resolved closure. Existing K1 tools/licences retain their acceptance.
The new dependency/feature set requires separate acceptance even when licences overlap.

## Smallest first permission: C1 only

Request a **single disposable dependency-resolution and fetch experiment** from this
published addendum: private /tmp Git export, private CARGO_HOME and CARGO_TARGET_DIR,
accepted pinned Rust/Cargo tools, target x86_64-unknown-linux-gnu. Permit registry-index
metadata and archive downloads only from `index.crates.io` and `static.crates.io/crates`
for the exact permitted packages below plus unavoidable index/config metadata. No Git
dependency, credential, apt, rustup update, cargo install, engine compilation/execution,
image build/publication or live lock/cache change. Copying accepted cache material into
the private CARGO_HOME is permitted only after digest checks and without mutating its
source. Save network request/digest inventory; fail on another package/source/version.

The source-side scratch edit is exactly:

```toml
serde = { version = "=1.0.229", default-features = false, features = ["derive", "std"] }
serde_json = { version = "=1.0.154", default-features = false,
               features = ["std", "float_roundtrip", "arbitrary_precision"] }
sha2 = { version = "=0.10.9", default-features = false, features = ["std", "force-soft"] }
# dev only, unchanged
proptest = { version = "=1.12.0", default-features = false, features = ["std"] }
```

TOML layout above is explanatory; keep each inline table on one line in an actual Cargo
manifest. Do not change the live manifest/lock. Start from the published current lock,
request a targeted update of the path root, then use `cargo update -p NAME --precise VERSION`
for each proposed new package if necessary. Archive every intermediate resolver output.
Do not use a broad update, nightly/minimal-versions, hand-built lock entries or a dummy
constraint crate that changes the production feature graph. The final allowed graph is
an allowlist predicate, not a promise that resolution will succeed. If Cargo cannot meet
all exact pins while retaining existing packages, return the actual conflict and stop.
No alternative version becomes approved because the resolver prefers it.

New exact package candidates: sha2=0.10.9; digest=0.10.7; block-buffer=0.10.4;
crypto-common=0.1.6; generic-array=0.14.7; typenum=1.19.0; version_check=0.9.5;
cpufeatures=0.2.17. Their upstream crates.io sources, package checksums and licence strings
are bound in the **retained** A dependency-candidates.json and repeated as constraints in
construction-plan.json. Generic-array is MIT; the others are MIT OR Apache-2.0 (the
version_check metadata spells this `MIT/Apache-2.0`). Inspect actual archive licence files;
metadata alone is not a licence audit. Existing cfg-if=1.0.5/libc=0.2.190 may satisfy the
new branches if resolution confirms it; cpufeatures0.2.17 must coexist with the accepted
0.3.1, not replace it. No sha2-asm, optional crypto RNG/MAC/OID/zeroize/scale-info package
is allowed. No existing package version/checksum/source may drift, including dev and
other-target entries. Record full and target-filtered graphs, not target-filtered evidence
alone. The exact accepted old lock is hashed and enumerated in the machine plan.

C1 commands, executed only after permission, use the private paths:

1. Record tool paths, `rustc -vV`, `cargo -vV`, accepted image/tool receipt and starting
   source/lock hashes. Make the exact scratch manifest edit; retain its diff.
2. Resolve with the pinned Cargo and targeted root/new-package updates. Compare all
   versions/checksums/sources against construction-plan.json. Any extra is a refusal,
   not an implicit widening of permission.
3. `cargo metadata --locked --format-version 1` and the same with
   `--filter-platform x86_64-unknown-linux-gnu`; `cargo tree --locked -e features`;
   `cargo fetch --locked --target x86_64-unknown-linux-gnu`. Full metadata may need permitted
   non-target packages; do not build them. Retain requested vs selected features per node.
4. Switch networking off and repeat metadata/fetch with `--offline --locked`. Audit
   archives against lock checksums, extracted source hashes, licences/notices and existing
   allow-list using accepted cargo-deny. Record tools/command/exit/stdout/stderr and every
   actual read/network request. The scratch lock is a **candidate artifact**, not installed.

Required C1 return artifacts: source diff; starting and resolved Cargo.lock; full and Linux
metadata JSON; feature graph; package/source/checksum comparison; archive SHA256 inventory;
licence text paths/digests/expression and cargo-deny result; cache path/digest inventory;
actual tool identities; complete command/network/error logs; no-engine/no-live-change
preservation receipt. The smallest dependency decision is then acceptance/rejection of
those **actual** candidate bytes. No final image digest may be invented.

## C2 is separate: offline software/canonical probe construction

Only after C1 returns and receives the necessary dependency/probe permission: mount the
candidate cache into the accepted local image read-only, source a separate private probe
workspace, and use a private target dir with networking disabled. This standalone test
probe may exercise serde numeric handling, canonical formatting and sha2; it does not
contain the native engine binary, launch mapped work or emit MappedEngineResult. Scope
includes debug/release builds and execution of this bounded probe only, not public K2.
Request no image rebuild for C2: readonly cache mount suffices. A distributable cache/image
extension, its recipe/layer closure, actual digest and publication/access destination are
separate C3 actions after exact dependency acceptance; none is requested or executed here.
No image pull/update or live dependency installation is implied by scratch construction.

`force-soft` is a requested feature, **not current proof of scalar code**. C2 must return:

- Actual unified features and selected target cfg, rustc verbose commands, RUSTFLAGS,
  target CPU/features and build-script environment/output. Ban target-cpu=native and
  explicit SIMD/crypto acceleration features; record all defaults rather than assuming.
- Exact sha2 archive/source and cfg path showing force-soft selects scalar compression;
  inspect dependencies too. Presence of cpufeatures in the graph does not prove execution
  of hardware intrinsics. No asm, architecture intrinsics or assembly digest backend.
- A non-inlined probe boundary around the real digest path; link/map/symbol evidence and
  disassembly of both debug/release reachable hash/compression call graphs. Demonstrate
  that the scalar implementation actually handles the known-answer vectors. If optimized
  scalar Rust is auto-vectorized, record it and return a decision; do not claim “no SIMD”
  from a source feature name. Propose exact compiler flags for a repeat only if needed;
  flags enter the candidate build inputs and require review.
- Distinguish scalar **hash path** from incidental baseline ABI register moves or vectorized
  libc copies and unrelated linked code. If the intended no-SIMD rule forbids every SIMD
  instruction in the process, the existing x86_64 toolchain/stdlib must also be audited and
  that stronger rule reconciled; do not imply this narrower path inspection proves it.

No substitute SHA implementation or unapproved checksum executable is allowed. Python's
installed hashlib and canonical_json serve as the existing reference. Test SHA standard
empty/abc/multiblock messages plus exact canonical bytes. This proposal adds no Rust code.

## Canonicalization matrix to freeze before C2

Use the installed Python interpreter/lock and record its exact version/origin; use the
accepted Rust toolchain and candidate lock/features. Compare bytes and hashes, not only
parsed numerical equality. No JCS substitution or normalization of strings/arrays.

| Family | Exact mandatory sample/domain | Required decision/control |
| --- | --- | --- |
| Installed | both canonical-vectors.json records; all installed M input fixtures and B113 saved inputs | identical normalized JSON and field-specific hashes |
| Integer | 0,1,2^53−1,2^53,2^53+1,u64_max,u128_max; negative typed refusal | lossless generic value and typed conversion; bool/string/float token refused for integers |
| Float | ±0; nextafter neighbors around1e−4,1e−5,1e15,1e16; ±1e−7,1e20; max/min normal/subnormal f64; exact halfway cases | Python repr/exponent sign/zero padding/integral .0 and zero normalization |
| Finite sweep | 4096 fixed seeded finite f64 bit patterns, frozen before probe, plus every exponent boundary and adjacent mantissas | byte equality, no opportunistic sample removal |
| Nonfinite | NaN,+Inf,−Inf, JSON overflow1e999 | refuse, not stringify or emit null |
| Strings | μ,astral character, U+2028, quote, slash, backslash, every U+0000..001F control | UTF-8/escape parity; no Unicode normalization |
| Malformed Unicode | invalid UTF-8, lone escaped surrogates | exact shared refusal; characterize Python canonical UTF-8 failure without calling it an accepted value |
| Objects | all key-order permutations of a small object; duplicate top/nested keys; unknown keys | canonical key ordering, duplicates/unknowns refuse before hashing |
| Closure | nested self hashes; omit only the declared own top-level field | stale/cross-version/hash-cycle mutation refuses |
| Typed normalization | equivalent legal float spellings and required/default fields | normalize through exact carrier; no integer/float token coercion outside declared float fields |

Retain all mismatches and refusal-layer differences. `arbitrary_precision` alone does not
establish u128 union parsing or float parity; serde_json private numeric-marker handling
must not permit a caller object to masquerade as a number. Probe its reserved marker-shaped
object as an explicit refusal. If the proposed formatter cannot match Python, return the
counterexample and an exact bounded dependency/algorithm proposal. Never hash a different
representation to make tests green. C1/C2 results cannot confer final first-use authority.
