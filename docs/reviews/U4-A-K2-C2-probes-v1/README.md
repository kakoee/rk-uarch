# A C2 probes — typed mismatches and release SIMD require reconciliation

The approved standalone debug/release experiment ran against the exact accepted C1 inputs.
**It is not a complete parity or no-SIMD pass.** Each mode matched20,955 of20,965 frozen
expectations and retained the same ten typed-carrier mismatches. Both raw result streams
are byte-identical. A separate three-case registry/profile identity supplement passes.
Six standalone Rust unit tests pass in each mode; six host comparison negative controls
passed before native execution. Stop for coordinator/B reconciliation.

[Summary](summary.json), [all comparisons](comparison-debug.json),
[exact counterexample inputs](counterexample-inputs.json), and
[bounded next decisions](next-decision.md) carry the findings. Dependency acceptance and
this C2 run were already approved; no repeated dependency or C2 vote was requested.

## Authorization and exact construction

[Input receipt](inputs.json) verifies both SHA256 bindings in the published
[approval](../U4-K2-approved-C2-release-v1/acceptance.json), plus all five accepted C1 inputs
and B's licence review. Historical pending proposal text is unchanged. Published main was
received normally; its actual commit is recorded separately from C1's0718955 experiment pin.
The current source includes the installed human K2 semantic carriers.

The accepted lock SHA256 remains
`cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be`;
the crate manifest remains
`60299ba9498e506010a5c908ef8017beb2279d1aedab409a7fc21601d3b35ee0`.
[Workspace](workspace.Cargo.toml) and [crate manifest](probe.Cargo.toml) are byte copies.
The root package retains `uarch-engine` identity solely so the accepted lock works unchanged.
The fresh private crate contains only `src/bin/c2-probe.rs`, published as [probe.rs](probe.rs).
No original engine source, library target, mapped workload execution or MappedEngineResult
is present. Exact full resolution/features/dependency edges match C1; target metadata
changes only to describe the standalone binary. The first `cargo rustc` invocation refused
the virtual workspace; selecting `-p uarch-engine` fixed invocation, with no lock/layout edit.

The existing image e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523 and actual
Rust/Cargo1.99.0, cargo-deny0.20.2, rustfmt/clippy were reverified. Every container used
`--pull never --network none --read-only`, user1000, no capabilities and an empty environment
with explicit paths. All1,719 accepted cache files were verified before copying; the copy
was mounted **read-only**. Source was read-only, target private. No resolution update,
fetch, install, image construction or network activity occurred.

[Build inputs](build-inputs.json) and [commands](commands.json) bind every command, exit,
stdout/stderr and input digest. Builds used locked/offline Cargo and explicit standalone
package/target. Flags were exactly `-C debuginfo=1 -C linker=/controls/linker.sh`;
the linker wrapper delegates to the image's `/usr/bin/cc`. Root-only link arguments write
the debug/release maps. No target-cpu=native or explicit acceleration was supplied.

## Frozen matrix and actual outcomes

[Freeze receipt](freeze.json) binds the original21,604,245 vector bytes, generated before
Rust execution from the pinned Python export with `-I -S`, explicit site-packages and
asserted reference module origins. It records the actual interpreter executable/version,
Pydantic version, uv.lock, imported file digests, input fixture digests and normalization.
No editable project checkout, mapper, producer or oracle workflow was imported.

[Original vectors](vectors.jsonl.gz) are lossless gzip. Their uncompressed SHA256 is
`8dae6586c54462debbf1dad28ff963099a1a89d7b2daa213ba2908c7e46c7e9e`.
The finite sweep uses seed0x5534433250524f42 and Python MT19937 getrandbits(64), rejecting
nonfinite/duplicate patterns. The corpus includes both signs at every finite binary exponent
boundary and adjacent mantissas, decimal exponent boundaries, specified notation cutovers,
subnormals, extremes and halfway decimal tokens. No failure was removed or reformatted.

| Coverage | Actual disposition, both modes |
| --- | --- |
| Two installed canonical records, ten M fixtures,113 B bundles | canonical bytes/hash parity on Python-normalized values |
|488 original fixture identity cases | top-level-only exclusions and declared identities agree |
|4,096 finite patterns; all boundary/halfway cases | bytes and SHA256 agree |
| Generic integers through u128 max; direct rational/u128 carriers | positive cases agree; direct u128 rejects integer token `-0`, which Python normalizes to0 |
| Seven rational-valued NumericLeaf cases | serde untagged union refuses all seven, including0/1 and u128_max/1; Python accepts |
| Typed SourcedValue normalization/defaults | six numeric-spelling cases agree; Python's legacy float field accepts boolean/string while derived Rust f64 refuses two cases |
| Unicode/control/UTF-8/surrogates, duplicates, unknown keys, nonfinite | acceptance/refusal disposition agrees; exact refusal layers remain recorded |
| Reserved numeric-marker objects, including escaped/nested keys | explicit caller-marker guard refuses; generic Python object behavior is separately recorded, not relabelled as a numeric parser refusal |
| Nested self hashes; stale, version and self-reference mutations | expected identity refusals agree |
| SHA empty, abc, multiblock and million-a | known-answer hashes agree through the actual non-inlined sha2 boundary |

The initial recursive identity selector omitted registry self-field coverage because it
looked for `profiles`; the actual carrier uses `test_only_specs`. The original corpus and
outcomes remain unchanged. A **separate**, three-case [supplement freeze](identity-supplement-freeze.json)
precedes its first execution and covers the installed registry plus B's registry/profile.
[Supplement vectors](identity-supplement.jsonl.gz) and both supplemental outcomes are retained.
This is a disclosed coverage completion, not a claim those three cases preceded the first run.

The formatter uses the accepted serializer's shortest digits and the already proposed
Python notation thresholds/sign/padding/integral .0 rules. It passed this finite corpus;
it is not a universal proof. Self-reference mutations fail the declared identity check; this is not a general graph-cycle
resolver. The probe's small typed carriers are experiments, not native
engine DTO implementation. Full installed carriers normalize in Python; Rust checks their
normalized canonical bytes/field hashes. Full native carrier validation remains outside C2.

[Raw outcomes](outcomes-debug.jsonl.gz) retain one lossless copy of the byte-identical
debug/release result streams; both command bindings remain separate. Host framing initially used text.splitlines and split literal
U+2028; byte-LF framing fixed only the comparison harness. Original output bytes were not
changed or rerun. [Host errors](host-errors.json) retains this and the invocation/coverage errors.

## Software path and actual binaries

The actual debug executable SHA256 is
`a36293c7e8778f7dab3403dc87d5aa1aa23e327c1f41c09272dea6b59b038c84`;
release is
`7bb89b3877a5a1931ccd16c4fb5a027e13df9a356e6c8dabab455a67270218f1`.
Both artifacts remain private. [Source selection](software-selection.json), symbols,
link maps, ELF relocations and disassembly bind the actual force-soft call path. The boundary
`c2_sha256_boundary` reaches `sha2::sha256::compress256`; release GOT slot0x9fb48 resolves
to0x4c9a0. Debug reaches the separate soft helper functions through digest/block-buffer.
This is conservative static direct-call/relocated-pointer reachability, not dynamic tracing
or exhaustive resolution of arbitrary indirect calls/libc internals.

[Debug hash-path assembly](debug-hash-path.asm.gz) and
[release hash-path assembly](release-hash-path.asm.gz) show no SIMD registers in the selected
compression functions. Release **hash output packing** in the non-inlined boundary does use
`punpckhbw`, `punpcklbw`, `pshuflw`, `pshufhw` and `packuswb`, e.g.0x33e3d–0x33e7d.
These compiler-generated packed transformations are distinct from incidental movups/movaps
copies and zeroing. No full-hash-path no-SIMD claim is made. Changed flags were not tried;
the exact bounded proposal is in next-decision.md. Public K2/software-path authority is absent.

## Reads, preservation and review artifacts

The accepted image has objdump/readelf/nm/cc/ld but no strace. Actual compiler/linker argv
and environments (138 invocations), Cargo verbose build-script invocations/outputs and96
compiler dep-info files are retained in compressed receipts. Necessary dependency build
scripts/procedural macros ran within the approved C2 scope. Declared rerun paths and dep-info
are **not an exhaustive filesystem-read trace**; arbitrary script/proc-macro reads remain
unobserved. No missing tool was installed and this limitation is not silently discharged.

[Preservation](preservation.json) verifies all7,110 files across the two original C1 workspaces
unchanged in bytes/size/mtime, the copied read-only cache unchanged, exact manifests/lock,
all ten human semantic postimages and unchanged live dependencies. Bulk cache/build trees
remain in `/tmp/u4-k2-c2.75eyx6ab`. [Private receipt inventory](private-receipts.json) binds
all raw origins. [Compressed-artifact bindings](compressed-artifacts.json) specify exact raw
and gzip digests; [Raw-output locations](raw-output-locations.json) map every command output to a public
compressed artifact or private bulk disassembly. command-outputs.tar.gz retains the remaining
exact stdout/stderr, including the failed invocation; repeated outcome bytes are stored once. Executed-controls.tar.gz preserves exact host
scripts/wrappers, including earlier failed attempts. No archive must be executed to inspect it.

[Read-only verifier](verify_receipts.py) checks approval/input hashes, source/vector bindings,
actual comparisons, negative controls, all command outputs, archive integrity and preservation.
[Validation](validation.json) records host lint/format/checks. No native tests are repeated by
this verifier. B's accepted C1 review is inherited; B has not reviewed this new C2 package.
No protected path, live dependency, artifact adoption, image distribution, host authority,
public K2 or qualification is released. U0024 remains unchanged.
