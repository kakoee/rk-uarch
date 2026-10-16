# B diagnostic acquisition and static-inspection receipt

The approved two-package acquisition and static inspection is complete. The authenticated
strace executable is SHA256
`aebaf212ce84a12208c5fa25f08c892029e6f6949b778da55e071ac145404a1e`.
Its interpreter, six reachable DSOs and required strong symbols/version definitions are
accounted for by the two approved packages and the existing accepted image. **No acquired
executable or library ran.** Runtime compatibility, ptrace permission and read coverage
remain untested. This supports coordinator review of a separate execution decision.

Started at `f6072ac3c6084abe303dd94f0dcea9563ba6f995`; integrated published main normally
to `ef751b57ae164d2719baf3c228b9ea0822d79419`. Verified both hashes in the subsequent
[Javid acceptance](../U4-read-diagnostic-approved-acquisition-v1/acceptance.json), plus the
exact proposal candidate/acquisition hashes. Historical pending wording and all prior
packages remain unchanged. [authentication.json](authentication.json) records these
bindings, exact HTTP responses, signed-chain identities and both complete package stanzas.

## Acquisition and authentication actually executed

Private root: `/tmp/u4-b-tracer-inspect.1q11e0q8`. Only the four approved endpoint objects
were acquired; all returned HTTP 200 without redirects. No fallback, source archive,
new key, additional package, apt operation or dependency resolution was used.

| Object | Bytes | SHA256 |
| --- | ---: | --- |
| InRelease | 151075 | `77737fa4b34f2693e982cc9ee35736816c35a7778fc2d326cc1bbf5b301fe1aa` |
| Packages.xz | 8790396 | `9e0b5aabb2465b3d2e7a7fe27f9913846277833f7a2826e7767acccff5b588c5` |
| strace_6.1-0.1_amd64.deb | 1313880 | `1942d086a6244a1a9643489d3b0aa604ac44b88991d6c69217a63a193671bd4f` |
| libunwind8_1.6.2-3_amd64.deb | 51172 | `7b297868682836e4c87be349f17e4a56bc287586e3576503e84a5cb5485ce925` |

`gpgv` exited 0 with three valid signatures under the existing image keyring; fingerprints
and raw [status](signature.status)/[diagnostics](signature.log) are retained. The signed
Release identifies bookworm/oldstable 12.15, dated **2026-07-11 10:16:37 UTC**. It is not
future-dated. **Valid-Until is absent**, so no signed expiry/freshness bound was established.
No expiry was invented or authentication bypassed. The authenticated SHA256/size entry
matched Packages.xz; bounded decompression produced 50,060,337 bytes, below 128 MiB.
Unique amd64 stanzas matched the exact versions, filenames, sizes, digests and dependencies
before either .deb was requested. This is a Release→index→payload authentication chain,
not a claim of individually signed .deb files.

## Static payload and runtime closure

Image identity was freshly verified as Linux/amd64
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
All inspection containers used networking disabled, `--pull never`, read-only image and
download mounts, UID 1000:1000, all capabilities dropped, no-new-privileges and unchanged
default seccomp. Only private extraction/output directories and tmpfs were writable.

Before extraction, existing image dpkg-deb/tar listed all four archives: 18/3 strace
data/control entries and 19/5 libunwind8 entries. Names, types, permissions, duplicates,
parents and all four symlink targets passed the bounded path checks. No special device,
escaping link, absolute/traversal path or set-ID entry was admitted. Extraction used
`dpkg-deb --control/--extract`, without package installation. No maintainer scripts were
present; libunwind8's `activate-noawait ldconfig` trigger was read as data and never run.
All 16 package-listed regular data files matched control md5sums (secondary extraction
check); authenticated package SHA256 remains the primary integrity binding. All 22
regular data/control files and four symlinks have identities in [identities.json](identities.json).

| Acquired ELF | SHA256 | Relation to strace |
| --- | --- | --- |
| usr/bin/strace | `aebaf212ce84a12208c5fa25f08c892029e6f6949b778da55e071ac145404a1e` | PIE executable, 2,034,104 bytes |
| libunwind-ptrace.so.0.0.0 | `cb8ab3f0e63b0fa826c1002a91ba3d7f055940b0be3f4092e24834b3cadba020` | Direct DT_NEEDED |
| libunwind-x86_64.so.8.0.1 | `04bd8928ff2105c4c86f01755b9cfbe5414f16115d6f1f3b3c98ec3d9aa8ccb2` | Direct DT_NEEDED |
| libunwind.so.8.0.1 | `c66c0e877d919d0cea417cb58372884c00e529f13a9ddf78b9760a16a887dba0` | Transitive DT_NEEDED |
| libunwind-coredump.so.0.0.0 | `d35e471e7060eab70dc00d3d8368d19e7d821e7428ae98cc607e66a481bdf248` | Packaged, not reachable by strace DT_NEEDED |

The actual interpreter is `/lib64/ld-linux-x86-64.so.2`. Remaining reachable image files
are libc.so.6 and liblzma.so.5 plus that loader; their hashes equal the earlier proposal's
observations. glibc is `2.36-9+deb12u14`, liblzma5 `5.4.1-1+deb12u2`. Every inspected ELF
is x86_64/ELF64 with no RPATH/RUNPATH. No new runtime package is needed by this **static**
graph. [static-closure.json](static-closure.json) enumerates exact edges, version needs,
provider definitions and explicit unresolved weak imports. The reachable group supplies
302 strong undefined-symbol requirements; the unused coredump object has another 31
available in that group, but standalone coredump loading is not claimed.

These are symbol-availability checks, not loader execution/emulation, IFUNC/constructor
execution, optional dlopen discovery or proof of runtime compatibility. Runtime-reported
strace version remains null; `6.1-0.1` is the authenticated package/control identity.
The ancillary strace-log-merge script is separately hashed, inspected as text and unused.
[licences.md](licences.md) records actual notices/applicability without granting an exception.

## Checks, limitations and next decision

Newly executed: authentication, package/path/control inspection, static ELF and image-byte
checks, notice inspection, post-inspection download hashes, and the owned helper's positive,
four negative and restored-positive checks. [commands.json](commands.json) retains exact
container argv/environment/exit bindings; [private-receipts.json](private-receipts.json)
locates and hashes the preserved raw outputs. Packages, extraction trees, full index and
bulk readelf/symbol outputs remain private. [validation.json](validation.json) records checks.

Two preliminary optional-tool lookups exited 127: Python and the xz CLI are absent in the
image. No tools were added. Existing host Python stdlib interpreted metadata/listings;
all signature, archive, ELF and image-library inspections used existing tools in the image.
Existing dpkg-deb successfully decompressed both packages internally. The expected failures
are preserved. Initial helper formatting failures were fixed; final lint/format checks pass.
No project modules were imported, and no C1/C2 native or runtime suites were rerun.

Coordinator may now review permission to use these exact diagnostic bytes privately under
the unchanged security settings, starting with the separately proposed bounded canary;
licence/use acceptance and execution remain distinct from this completed possession/static
inspection. Stop if the loader or ptrace denies execution; no security relaxation follows.
The subsequent build-trace subject/commands require binding after A's correction review.
This receipt does not activate the historical future-commands proposal or release a build.

Existing C2 evidence remains usable within its original limits. Complete file-access/read
closure, semantic dependency/environment-use claims and final host authority remain open.
No installation, ldd, strace --version, tracer/canary/build, image/security change,
public K2, C3, qualification or U0024 deferral change occurred. Stop for coordinator.
