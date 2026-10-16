# Read-audit disposition and bounded diagnostic proposal

The approved C2 handoff asks for build-script reads/environment/output and explicitly says
to report missing tools rather than install them. A returned real partial evidence and the
limitation. B reproduces that limitation; it does not reinterpret dep-info as complete reads.
The returned C2 experiment can support this reconciliation, but its read-evidence item is
incomplete and cannot support a complete build/authority claim.

| Evidence | Actually observed | Remaining limit |
| --- | --- | --- |
| Read-only source/cache mounts and private target | Exact probe/manifests/lock/cache bytes; fresh targets; filesystem write boundaries | Read-only is not a read log. The image filesystem and generated target files remain available to subprocesses. |
| Rustc/linker wrappers | Actual argv and available environment for 139 B invocations; A had 138 | An extra B `rustc -vV` explains the count difference. Environment presence is not proof of which variables a script/macro read. |
| Cargo `-vv`, build output files | Compiler and build-script invocation text, rerun directives, cfg/link emissions | Script declarations can omit arbitrary reads, directory scans, symlink targets, failed-open fallbacks and subprocess reads. |
| 96 dep-info files | Compiler-emitted file dependencies | Not a complete script/proc-macro/loader/OS file-access inventory. No fixed file-count quota. |
| Link maps, ELF, symbols, disassembly | Selected object/symbol/layout/DSO evidence; actual binaries and inspected hash paths | Not all filesystem reads or arbitrary indirect execution; mapping a library is not tracing every access it makes. |
| B reference imports | Exact Python module origins and bytes from the pinned export; all expected vectors independently re-derived | This consumer/reference check is not native build tracing or a future identity-generator data-read audit. |

Actual metadata includes build-script targets for generic-array, getrandom, libc, num-traits,
proc-macro2, quote, serde, serde_core, serde_json, typenum and zmij, and a serde_derive proc-macro
target. Metadata declares available targets; actual emitted build output paths are separately
listed in preservation.json. Do not convert that metadata list into a claim every possible
script/path ran in each mode. Dependency build-script and macro execution was authorized
for the standalone probe; it was not executed during C1 source inspection.

Before a future ToolInputs/BuildInputs/BuildReceipt read-closure assertion, reconcile actual
reads against source/includes/macros, scripts/generators and their imports/data, Cargo configs,
registry sources, generated target files, compiler/sysroot/linker/OS files, environment and
trust inputs. Separate inherited tool/image files, declared source inputs and derived outputs;
never feed a generated identity, binary, job, receipt or final HostRecord back into its own
upstream identity. The later external HostSelector still requires human installation. This
review creates none of those records and does not discharge their read-audit gate.

## Available diagnostics and precise limitation

B queried the accepted image without installing anything. It has objdump/readelf/nm/cc/ld;
strace, perf, bpftrace, ltrace and gdb were not found on its explicit PATH. On this host,
`/usr/bin/perf` is only a launcher: `perf --version` exits **2**, reporting no tools for the
running `6.6.87.2-microsoft-standard-WSL2` kernel. That message is retained in host-perf.stderr;
it is not a recommendation or authorization to install the suggested kernel packages.

An already available **partial** route is GNU ld's `-t/--trace` (help says “Trace file opens”),
plus its existing maps and wrapper logs. It can help account for linker input files if a
later scoped diagnostic command is approved. B only read the help; no linker flag changed.
It cannot observe arbitrary build-script/proc-macro reads and cannot close the missing gate.
Running strace on the Docker client alone would not trace the daemon's container children.

## Diagnostic-only proposal, not authorization

If exhaustive native file-access observation is required for the next construction gate,
review one userspace tracer as a distinct diagnostic input. A concrete next proposal is:

1. Obtain an exact, independently reviewed Linux x86_64 **strace** executable and its runtime
   dependencies through a separately authorized route. Record actual version, file SHA256,
   licence/notices and loader/DSO closure first. None is available/pinned by this review;
   no version, checksum or download destination is invented. This unresolved identity prevents
   treating the following procedure as an executable approved plan.
2. Mount that exact diagnostic payload read-only at `/diagnostics` into the same accepted
   image. Keep source/cache read-only, fresh private target/output, no network, no image
   rebuild and the same probe source/dependencies/flags. Launch the owned child command
   under the tracer, following descendants; never attach to unrelated/shared processes.
3. Proposed trace selection: `strace -ff -yy -s 4096 -e
   trace=%file,%process,read,pread64,readv,getdents64,mmap -o /receipts/read-trace` preceding
   the exact approved Cargo probe command. Keep wrapper environment records too. Preflight
   on the existing unprivileged/no-capabilities/seccomp configuration; if ptrace is denied,
   stop and return the exact error. No SYS_PTRACE grant, security-policy removal, root access
   or host tracing is implicitly approved.
4. Verify descendant coverage, successful and failed opens, path/dirfd/symlink resolution,
   inherited descriptors, directory reads, mmap-backed input and subprocess execs; retain
   truncation/coverage failures. Before calling the trace complete, demonstrate discovery
   of a small separately approved canary read outside the declared source list. This is a
   tracer control, not an engine or performance test.
5. Return the actual read inventory and unexplained deltas. Preserve tool/sysroot/OS and
   generated-output classifications. A syscall trace still needs interpretation and is
   not by itself a proof of semantic dependency or environment-use completeness.

Do not broaden the current C2 review into tool acquisition. Coordinator may separately
release field compatibility and the compiler experiment with these limitations carried
forward; neither may claim exhaustive reads or final authority until the applicable gate
has real evidence. C3/remote infrastructure remains deferred under U0024.
