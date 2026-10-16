# Actual bounded diagnostic execution and read interpretation

Approval and exact acquired payload are reverified in preflight.json. The approved
private strace6.1/libunwind bytes ran via the inspected loader's tracer-only library
path, in image e9f69f4…0523, UID1000, networknone, cap-dropALL, no-new-privileges,
unchanged default seccomp, readonly original inputs and private outputs. No install,
new package, image/security change or host attachment occurred. Notices remain private
with the acquired payload. Historical acquisition receipts remain unchanged.

The monitor and finite canary are independently controlled. Canary completed under
30s/16MiB:5 process logs/304 parsed syscalls; the alias→sentinel read via inherited fd,
failed lookup, directory enumeration, exec and mapped image file were observed. Removing
the actual sentinel read or an observed child log from analysis refuses coverage;
restoring the original logs passes. The monitor's four host tests cover limits and
output-symlink refusal, required security arguments and missing-tail/child detection.
No missing/truncated/limited trace was credited as a pass.

Cold corrected-probe builds bind c678dedd47e639f7e7f0ac55f48a8775fe524708 and source
SHA a4129c184bb04e4dedcbe518c593c47c5ecc27154debd3ff558ccba67c86153c.
Actual metadata verified the sole probe target and accepted dependency resolve graph.
Both traced builds completed under10min/512MiB, ~7.8s and42.7/36.6MB owned outputs.
Every observed child had a log and terminal record; debug653/release584 processes.
The actual binaries equal the previously ordinary-built exact source:

- debug53af189a49175417f12d3e3ea2fd00b5041cb4f99261c7be83297c4ffb083ff3
- releasec2eb867ad1f8f6a03eba5b9ae8e97b6521797b511444d03f034ce6293485067f

This equality is newly measured. The previous full C2 vector/fault suite is inherited,
not rerun. No K2 candidate binary identity follows from these probe identities.

## What the read evidence supports

Raw per-PID logs, exact command/env files, fd/cwd/symlink paths, failed lookups, generated
files, mmap/exec and child relations remain under `/tmp/u4-b-read-trace-v1`. Compact
bindings and actual commands are published. `read_trace_inventory.py` reproduces path
classification; v2 additionally classifies `/work` and `/cargo-home` directory roots
correctly (historical v1 remains untouched). Paths are observations, not a list of
semantic dependencies:26 source-associated query paths include only4 actual source
files. All4 file bytes match the frozen probe workspace. The648 cache paths include
queries/directories, not648 independent crate dependencies. Registry content is bound
by the1719-entry preserved private cache and accepted lock/checksums.

Both traces have37 successful cwd changes, each in a process without inherited
CLONE_FS and before that process created children. This resolves the concrete shared-cwd
interpretation concern for these traces. Decoded `-yy` file descriptors distinguish
resolved targets from query names; failed lookups retain their missing-file/config
premises. Cargo checked `.cargo/config[.toml]` at work/ancestor/cache roots and optional
build.rs/readmes/lib/main/examples/tests/benches; their absence is part of this exact
workspace. Do not infer absence in another export or unseen environment.

All45 compiler-wrapper environment records per mode were checked. Cargo generated its
normal `/target/...` and accepted toolchain library paths; none contained `/diagnostics`.
No child exec argv/env mentions diagnostic input paths. The initial clean environment
contains no LD_LIBRARY_PATH; the inspected loader path applies to the tracer only.
This is distinct from claiming Cargo never sets its own library environment.

## Explicit limits and remaining gate

File-access tracing does not prove semantic use, every byte of an mmap, complete env
variable use, IPC/anonymous-memory effects or universal reproducibility. Buffer contents
may be abbreviated even when path/argv records are complete. Generated/transient final
hashes do not reconstruct all historical versions. Tracer's own pre-child loader/DSO
reads are statically bound, outside the traced descendant tree. Directory enumeration,
failed config reads, image OS/tool files and dynamic proc/sys/device reads remain distinct
classes; no fixed56 support quota governs them. Parent cwd/thread interpretation must be
rechecked for each changed candidate; this probe conclusion is not inherited blindly.

The final candidate gate requires actual A source/identity-generator/commands and clean
candidate debug/release traces, actual read-class and generated-identity reconciliation,
strict source currentness and compatible ordinary/diagnostic identity evidence. That
source is still blocked by the published field mismatches and unfinished build generator
at the reviewed cd70fca interface. A final BuildReceipt/read-completion assertion is
therefore pending. No separate permission is needed to continue those approved traces
once the corrected pinned candidate exists, and no broader tool/environment claim is made.

Post-run preservation.json rehashes all1719 original/cache entries (original mtimes too),
22 acquired regular files,4 original diagnostic symlinks, the executed private diagnostic
copy and all4 probe source files. All remain unchanged. No acquired executable/library
is distributed by these documentation receipts.
