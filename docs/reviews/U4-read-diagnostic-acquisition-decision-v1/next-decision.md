# U4-read-diagnostic-acquisition-v1

Status: proposed to Javid; acquisition not authorized yet.
Recommend the bounded acquisition/static inspection step below. A's C2 compatibility
work continues independently.

Reviewed B proposal: `f6072ac3c6084abe303dd94f0dcea9563ba6f995`,
[handoff](../U4-B-read-diagnostic-proposal-v1/README.md).
Exact candidate.json SHA256:
`2c922a0cf36adbbd4d8e6c0a8a629b1f23ddaa918cb7a7ccb1bdccd101ce5ff2`.
Exact acquisition.md SHA256:
`f81e6aabb06eb09c0e847969e6fbf9a7033350b4141b1ad1218e943c8d0171b7`.

## Requested decision

Authorize B to acquire, authenticate and statically inspect exactly these amd64 binary
packages using [the seven-step procedure](../U4-B-read-diagnostic-proposal-v1/acquisition.md):

| Package | Bytes | Package SHA256 |
| --- | ---: | --- |
| strace 6.1-0.1 | 1313880 | `1942d086a6244a1a9643489d3b0aa604ac44b88991d6c69217a63a193671bd4f` |
| libunwind8 1.6.2-3 | 51172 | `7b297868682836e4c87be349f17e4a56bc287586e3576503e84a5cb5485ce925` |

Download only the two exact `deb.debian.org` package endpoints in candidate.json and
these metadata endpoints needed for authentication:

- `https://deb.debian.org/debian/dists/bookworm/InRelease`
- `https://deb.debian.org/debian/dists/bookworm/main/binary-amd64/Packages.xz`

The package payloads total 1,365,052 bytes; metadata downloads are additional, bounded
by 256 KiB for InRelease and 32 MiB for Packages.xz (128 MiB decompressed). Require
HTTPS, HTTP 200 and no cross-origin redirect. Use a new private directory; retain
request/response/identity evidence. Authenticate the Release/index/package chain with
only the existing image keyring before accepting payloads. Record dates/expiry; reject
invalid, expired or future-dated metadata. Missing Valid-Until must be disclosed rather
than invented. Missing/drifting package stanzas or signature failure stops the action;
no alternative version, mirror/archive route or new key is implicitly approved.

Use the existing accepted image, offline and unprivileged, for static inspection with
already available tools. Verify its identity and keyring against the B receipt. Inspect
archive paths/links before extracting into isolated roots. Read package control/licence
files and actual ELF headers, interpreter, required libraries and symbol versions.
Map the complete static loader/DSO closure using only these two payloads and existing
image libraries; hash executable and DSO bytes separately from package bytes.

No apt/dpkg installation, package database change, maintainer script, acquired executable
or library execution (including strace --version or ldd), tracing, canary, build, image
change, root/shared-host action or security relaxation is authorized. No third package
may be acquired. Return unexpected dependencies or payloads without expanding scope.

This permits possession and static examination of the diagnostic packages/notices;
it is not a new licence exception, distribution permission or linkage into rk-uarch.
The GPL/LGPL/Expat applicability must be recorded from actual package contents before
any later execution/licence decision. Existing Rust dependency acceptance is unchanged.

Return the authenticated package identities, actual executable/DSO hashes and closure,
licence/notice applicability, observations and unresolved limits. Runtime compatibility
and ability to trace under the existing security settings remain untested. Separate
permission is required before running the acquired tracer or a build under it.
No public K2, C3, final authority or qualification follows; U0024 is unchanged.

## Coordinator review

Verified all seven published inventory entries and five saved metadata response hashes;
both saved Debian download pages contain the proposed package sizes and hashes. No
package was downloaded, signed index authenticated or executable inspected here.
B's existing-image inspection is inherited, not rerun by the coordinator.

A fresh read of [Debian's libunwind download page](https://packages.debian.org/bookworm/amd64/libunwind8/download)
confirmed its size/hash. Debian's [archive authentication documentation](https://manpages.debian.org/bookworm/apt/apt-secure.8.en.html)
supports the proposed signed Release → index checksum → package checksum chain; it
is not an individual .deb signature or executable audit. The web tool could not open
strace's download and copyright pages; their saved B response identities were checked
instead. Actual signed-chain authentication remains mandatory during acquisition.

The deferred trace command is not approved by this decision; its precise subject will
need binding after inspection and the A correction review. Existing C2 evidence remains
usable within its scope, and no claim of exhaustive reads is granted.

[Prepared B handoff](lane-B-after-approval.txt) is conditional on Javid's approval.
