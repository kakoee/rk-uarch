# Separate future observation proposal — not execution permission

After acquisition inspection and a separate coordinator/human release, create the new
private root `/tmp/u4-b-read-trace-v1` (refuse if it exists). Reconstruct/copy only the pinned
standalone C2 workspace, accepted cache, controls and frozen vectors from preserved inputs,
rehash them against candidate.json and the historical B command/preservation receipts.
Do not mount original evidence writable. The workspace contains the probe and manifests,
not engine sources. Debug and release each start with an empty independent target and
receipt directory. No agent edits to fields/flags/lock; corrected A inputs stay separate.

[future-commands.json](future-commands.json) contains exact argv and host environment for
these **unexecuted baseline build** observations. Only `/target`, `/receipts` and tmpfs
`/tmp` are writable inside the container; `/work`, `/cargo-home`, `/controls`, `/vectors`
and the inspected `/diagnostics` extraction are read-only. Keep `--pull never`, amd64,
`--network none`, read-only image, UID 1000:1000, `--cap-drop ALL`, no-new-privileges and
Docker's unchanged default seccomp. Do not mount the Docker socket inside the container.
No SYS_PTRACE, privileged mode, seccomp override, host PID namespace or `strace -p`.
If loading, ptrace or descendant tracing is denied, retain the exact failure and stop.

Launch the tracer with the image's glibc loader and a **tracer-only** `--library-path` for
the inspected libunwind extraction. No LD_LIBRARY_PATH is exported to Cargo/children.
The proposed prefix is:

```text
/lib64/ld-linux-x86-64.so.2 --library-path /diagnostics/usr/lib/x86_64-linux-gnu:/diagnostics/lib/x86_64-linux-gnu /diagnostics/usr/bin/strace -ff -ttt -yy -v -s 4096 -o /receipts/debug.trace
```

It precedes the inherited exact Cargo command (`rustc --locked --offline -p uarch-engine
--bin c2-probe -vv --message-format=json ...`), retaining rustc wrapper, linker wrapper and
`RUSTFLAGS=-C debuginfo=1 -C linker=/controls/linker.sh`. Release changes only the inherited
mode switch/tag/map filename. Full syscall selection avoids silently omitting fd, memory,
process or file operations. No stack unwinding (`-k`) or seccomp-bpf acceleration is requested.
Flag meanings are from [the packaged strace manual](https://manpages.debian.org/bookworm/strace/strace.1.en.html).
These are construction observations only, not performance measurements or modeled timing.

## Bounded canary first, under identical security settings

Before either build, create a separate read-only `/canary` mount from private synthetic
files: `sentinel` contains exactly `U4-read-canary-v1\n`; `alias` links to `sentinel` inside
that mount; `absent` does not exist. Inventory and hash them. This directory is deliberately
outside the declared build source/cache set; it is diagnostic data, never an accepted input.
Use the same tracer prefix with `/receipts/canary.trace` and this owned command:

```sh
/bin/sh -c 'exec 3</canary/alias; /bin/sh -c "/bin/cat <&3"; if /bin/cat /canary/absent; then exit 81; fi; /bin/ls -U /canary >/dev/null'
```

Require sentinel stdout exactly, absent-file ENOENT, root/child execs, open/read/close of
the inherited descriptor, directory enumeration and every child exit in raw trace. Resolve
the symlink using the frozen mount inventory; an open of a symlink need not issue readlink.
Account for executable/loader mmap observations separately from actual page consumption.
The inventory comparison must flag the sentinel as outside the declared source set; an
analysis-only negative copy with that event/child trace removed must refuse coverage.
An unexpected success on `absent`, missing sentinel, empty trace or missing child is failure.
This canary and its negative control are proposed, **not executed**.

## Coverage, limits and interpretation

- Launch only the owned child tree. Reconcile fork/vfork/clone/clone3 returned PIDs/TIDs,
  exec transitions, per-PID logs and terminal exits/signals with Cargo and wrapper records.
  Account for failed execs/opens, cwd/chdir, dirfd, inherited/duplicated/closed fds, symlinks,
  renamed/unlinked generated files, directory membership, pread/readv, mmap and kernel
  executable loads. Successful exec implies executable access even without a user open.
- Preserve unfinished/resumed pairs and raw order; do not resort into a fabricated trace.
  `-s 4096` may abbreviate data buffers; retain returned byte counts and explicitly mark
  unobserved content. Truncated paths/argv/environment, undecoded relevant pointers,
  unmatched calls, missing PID tails, tracer diagnostics or unknown fd/path provenance
  prevent a complete observation claim. Unsupported/async IO or reads through IPC remain
  explicit unresolved edges, not silently covered. Distinguish exited-by-signal from success.
- Bound each canary to 30 seconds/16 MiB and each build to 10 minutes/512 MiB total trace
  output. A supervising host process measures only this private output and named container;
  on any limit or tracing failure, stop that owned container and retain partial evidence as
  **incomplete**. Never discard excess records and report success. A monitor must be reviewed
  before execution; no current helper launches this plan. No host/shared-process attachment.
- For each observed path keep process/executable, operation/result, fd/cwd resolution and
  classification: pinned source/cache; tool/image/sysroot/OS; diagnostic payload; generated
  intermediate/output; configuration/trust input; failed lookup/directory membership;
  unresolved/dynamic (/proc,/sys,/dev/time/random/IPC). Hash stable inputs, track generated
  versions and pre/post source preservation; last-state hashes alone cannot recover transient
  contents. Compare all observations to declarations, with no fixed support-file quota.
- Preserve available environment snapshots and audit relevant source/configuration use;
  observing exec environment does not prove which variables were read. Classify accesses
  separately from semantic dependencies. No generated identity/binary/receipt/HostRecord is
  fed back into its own upstream identity. External final host selection remains human work.
- The tracer's own loader/DSO reads precede and sit outside its child trace. Bind them via
  the inspected diagnostic closure and image; never count this as tracing itself. The
  altered ptrace execution is diagnostic, not proof of all possible untraced behavior.

Return raw log hashes, ancestry/coverage reconciliation, actual build identity and unresolved
read/environment edges. This can inform the later gate, not manufacture authority or claim
C3, engine-build coverage, full qualification, human acceptance or a public K2 release.
