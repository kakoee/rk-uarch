# Proposed first action: acquire/authenticate/inspect, then stop

No command in this document has been executed. Work in a newly created private directory
(e.g. `mktemp -d /tmp/u4-b-tracer-inspect.XXXXXXXX`) with private downloads and extraction
roots. No apt update/install, dpkg -i, shell sourcing, maintainer-script execution, loader
execution, ldd, strace --version or tracer use. Existing dpkg-deb/readelf/sha256sum/gpgv
suffice for static inspection; tool availability in the accepted image is recorded.

1. Fetch only these metadata objects over HTTPS into that directory:
   - `https://deb.debian.org/debian/dists/bookworm/InRelease`
   - `https://deb.debian.org/debian/dists/bookworm/main/binary-amd64/Packages.xz`
   Require HTTP 200, bounded sizes (256 KiB and 32 MiB respectively), and no redirect to
   another origin. Save response headers, URL, time, size and SHA256. This is a proposal
   for metadata acquisition too; the signed objects were not fetched/verified here.
2. Mount downloads read-only and a private inspection-output directory writable into the
   accepted image, offline, with the same UID/capability/seccomp restrictions as trace-plan.
   Verify InRelease using the already present keyring:
   `gpgv --status-fd 1 --keyring /usr/share/keyrings/debian-archive-keyring.gpg --output /inspection/Release /downloads/InRelease`.
   Keyring package: `2023.3+deb12u2`; file SHA256
   `506b815cbb32d9b6066b4a2aa524071e071761e7e7f68c3ac74f3061ba852017`.
   Record actual valid signing fingerprint(s), Release date/expiry and codename bookworm;
   reject expired/invalid/future-dated metadata. If no Valid-Until is present, report that
   missing freshness bound explicitly; do not invent one. No new key or trust configuration.
3. Match Packages.xz size/SHA256 against authenticated Release before decompressing the
   metadata (cap decompressed size at 128 MiB). Parse complete unique amd64 stanzas for
   strace 6.1-0.1 and libunwind8 1.6.2-3. Require Filename/Size/SHA256 equal candidate.json,
   plus declared dependency fields. Stop if missing, changed or ambiguous. Retain those
   two small stanzas and signed-chain identities, not a repository-wide manifest in Git.
4. Only after successful metadata authentication, GET exactly:
   - `https://deb.debian.org/debian/pool/main/s/strace/strace_6.1-0.1_amd64.deb`
   - `https://deb.debian.org/debian/pool/main/libu/libunwind/libunwind8_1.6.2-3_amd64.deb`
   Same HTTP/origin controls, exact sizes and SHA256 from candidate.json; no resolution,
   alternatives, third package or source archive. Save both payloads privately, not in Git.
5. Use `dpkg-deb --info`, `--contents`, `--control` and `--extract` on each exact file in
   private inspection roots. Inspect entries first: reject absolute/traversing paths,
   escaping links and special devices. Extract as the existing unprivileged UID, not root;
   never execute maintainer scripts or change package databases. Preserve copyright,
   changelog, symlinks and declared licence texts. Hash `/usr/bin/strace` separately from
   its .deb and every extracted DSO. Examine `readelf -h -l -d -V` on these files:
   ELF64/x86_64, PT_INTERP, NEEDED/RPATH/RUNPATH, symbol versions and resolved symlink paths.
6. Recursively map those actual DT_NEEDED entries against only the extracted libunwind8
   payload and existing image libraries. Hash existing loader/DSOs and verify required
   symbol versions statically. Proposed loader `/lib64/ld-linux-x86-64.so.2` is observed
   in the image, but matching the tracer's PT_INTERP is still a prerequisite. No arbitrary
   host libraries, dependency acquisition or LD_PRELOAD. If the declared two-package route
   cannot supply the complete diagnostic runtime, stop and return the precise missing edge.
7. Return package authentication, executable/DSO identities, notices/licence applicability,
   static loader closure and all limitations. Actual runtime version/compatibility and
   ptrace permission remain untested until a **separate execution decision**. Do not infer
   successful loading or tracing from ELF shape or package dependency satisfaction.

Debian's [archive authentication model](https://manpages.debian.org/bookworm/apt/apt-secure.8.en.html)
binds signed Release → Packages checksum → package checksum. No individual .deb signature
has been established here; upstream tarball signatures would not authenticate the Debian
binary executable. HTTPS page hashes are useful provenance, not a verified signature chain.
The exact future Release/index digests and signer fingerprints must be recorded from the
actual acquisition; they are deliberately not fabricated in candidate.json.
