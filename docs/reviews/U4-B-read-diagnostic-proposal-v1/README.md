# B read-diagnostic acquisition proposal

Recommend **acquisition and static inspection first** of Debian bookworm amd64
`strace 6.1-0.1` and its missing runtime package `libunwind8 1.6.2-3`, using the exact
endpoints, sizes and package hashes in [candidate.json](candidate.json). Return the
executable/DSO identities and licence review before separately authorizing a canary
or build trace. No acquired code runs in the first step; no package installation,
image modification, additional dependency resolution or security relaxation is proposed.

This continues the coordinator's [bounded release](../U4-K2-C2-followup-release-v1/README.md)
at `c277ddd28d1c4fdc4e799a3b32764874295a3e95`, integrated normally from starting B
`41150f291b0b9bec0ce80812b4974e2f3bc35f8a`. The original A review remains pinned to
`3faa3e9dbe785f43c51e26ad886eeb6bc3b00398`; reference source is
`ce732f5bedccdde629edcf278fa76ea772d0ea82`. The subsequent `9ee9917` hashing scope
clarification remains in force. A's field/comparator correction review is separate.
Earlier packages, counterexamples, native results and read-audit.md are unchanged.

## Gate and observation claim

The incomplete item is evidence supporting **future ToolInputs/BuildInputs/BuildReceipt
read closure and the later authority binding**, before asserting that their inputs account
for actual construction reads. A standalone probe trace can test the diagnostic route and
account for that particular build; it cannot discharge a later engine/identity-generator
build without observing and auditing that exact construction. No whole-sprint stop follows.

Existing C2 binary identities, canonical/hash comparisons and their ten counterexamples,
six tests per mode, source/cache bindings, compiler/linker argv and environment snapshots,
Cargo output, dep-info and link maps remain usable within their recorded scope. These are
inherited from A/B, **not rerun here**. A's bounded compatibility work can continue.
Neither dep-info nor linker tracing establishes exhaustive reads.

The proposed observation is the file-related syscall activity of one launched Cargo process
and its owned descendants in a pinned container, from exec through exit, for each recorded
build mode. A file open/stat/failed lookup can affect behavior without reading bytes;
read/mmap activity is not proof that bytes semantically influence the result. Memory-mapped
page consumption, getenv calls, nondeterministic input influence and alternative unexecuted
paths are not established by syscall tracing. Environment snapshots record availability,
not complete use. Source review/declared environment contracts and separate interpretation
remain necessary; unresolved edges stay unresolved rather than becoming a closure assertion.

## One concrete route

| Payload | Package SHA256 | Bytes |
| --- | --- | ---: |
| strace_6.1-0.1_amd64.deb | `1942d086a6244a1a9643489d3b0aa604ac44b88991d6c69217a63a193671bd4f` | 1313880 |
| libunwind8_1.6.2-3_amd64.deb | `7b297868682836e4c87be349f17e4a56bc287586e3576503e84a5cb5485ce925` | 51172 |

These are published **package** digests, read from Debian's
[strace metadata](https://packages.debian.org/bookworm/amd64/strace/download) and
[libunwind metadata](https://packages.debian.org/bookworm/amd64/libunwind8/download).
They are not executable hashes or locally verified payload hashes. The HTTPS metadata
responses have their own hashes/private paths in candidate.json; no .deb or source archive
was downloaded. Executable hash, actual reported version, ELF interpreter, direct/transitive
DT_NEEDED names and symbol-version compatibility remain unknown pending inspection.

The [strace package](https://packages.debian.org/bookworm/strace) declares libc6 >=2.34
and libunwind8. The [libunwind package](https://packages.debian.org/bookworm/libunwind8)
declares libc6 >=2.34 and liblzma5 >=5.1.1alpha+20110809 on amd64 (its libgcc-s1 dependency
is for armel/armhf). Fresh [image inspection](image-inspection.json) found libc6
`2.36-9+deb12u14`, liblzma5 `5.4.1-1+deb12u2`, the x86_64 glibc loader and their hashes;
libunwind8 and strace are absent. Thus **two** payloads, not a tracer-only mount, are the
smallest concrete route identified here. Package metadata suggests existing dependencies
suffice; only actual ELF inspection can confirm this. Any extra requirement stops the plan.
The host's available Ubuntu strace metadata requires glibc >=2.38 and is not this route.

[Debian's strace copyright](https://metadata.ftp-master.debian.org/changelogs/main/s/strace/strace_6.1-0.1_copyright)
identifies LGPL-2.1-or-later for strace and GPL-2.0-or-later for its test suite.
[Libunwind copyright](https://metadata.ftp-master.debian.org/changelogs/main/libu/libunwind/libunwind_1.6.2-3_copyright)
identifies Expat for upstream files and GPL-2.0-or-later for debian/*.
Preserve package notices and inspect actual payload applicability; this proposal makes no
new diagnostic licence acceptance and does not reopen accepted Rust dependency choices.
There is no proposed distribution or linkage into the simulator.

## Exact next permission

Authorize only the [acquisition/inspection procedure](acquisition.md): HTTPS GET of the two
exact packages above plus the named Debian signed-index metadata into a new private `/tmp`
directory; authenticate, extract without installing or running maintainer scripts, inspect
ELF/licences with existing tools, and return hashes and unresolved requirements. Stop on
version/checksum/source drift, signature failure, missing dependency or unexpected payload.
Do not substitute a newer version, add packages, execute strace/DSOs, or rebuild anything.
This is the next permission requested for coordinator/human consideration, **not granted**.

After that receipt, a distinct decision can authorize the bounded canary and the two
standalone baseline build observations in [trace-plan.md](trace-plan.md) and
[future-commands.json](future-commands.json). These argv arrays are proposed, not executed
commands or a runnable job. They retain accepted source/cache/compiler/flags and isolate
private outputs. New corrected A bytes require their separate review/binding first.

New work here: read-only local/image metadata, Debian description/digest/licence metadata,
proposal consistency checks and normal Git hooks. No tracer, compilation, probe, full
runtime suite, acquisition or installation ran. [validation.json](validation.json) records
exact checks and preservation. U0024, C3, final authority and public K2 remain unreleased.
Stop for coordinator reconciliation.
