# Worker and evidence model

The parent verifies the original approved immutable runtime/candidate and the exact new
helper manifest, checks the separately placed parallel release, then calls the **unchanged
public resolver** once for debug and once for release. It never constructs AcceptedHostBinding,
bypasses __post_init__, serializes a token or calls the private resolver. The original authority
and final source hashes remain the authority source. Every native call still opens, checks and
hashes its exact executable descriptor through that real binding.

All forks precede dispatch. The parent refuses active Python/kernel threads, active child
workers or an open candidate executable descriptor. multiprocessing's explicit fork Process
and byte pipes are used, not a Pool, Queue feeder, thread executor or pickled host object.
Children close inherited unrelated pipe endpoints and create their own sessions. No live
admission context is inherited. Immutable authority/literal/file-binding setup is inherited
by fork; baseline path callers still fully admit each request. Each worker owns one case at a
time, loops debug0/1/2 then release0/1/2, and returns a small completion record. The parent
assigns the next case only after collecting the complete group. Results never authorize inputs.

Resource selection intersects actual sched_getaffinity with all visible cgroup-v2 cpu.max
ancestors, floors fractional CPU capacity and accounts for the lesser of MemAvailable and
visible memory.max minus memory.current. Unknown/missing cgroup support, less than one
whole CPU or insufficient memory stops; no unlimited assumption or resource setting change.
The one-worker path uses this same supervisor in the diagnostic. Per-case deadline600s,
startup30s and full supervision7200s are bounded operational limits. Each native launch retains
production30s/64MiB input/64MiB stdout/1MiB stderr limits. They are not modelled picoseconds.

Only one worker can own each of the133 task IDs. Slot names are unique mode/repetition/case
identities, independent of completion order. Raw transport is saved before semantic checking;
a wrong positive/refusal leaves transport without a checked slot. A shared flock protects a
conservative2GiB byte reservation ledger. Blob writes compare existing bytes, reserve before
writing, fsync a unique temporary file, then publish with no-overwrite hardlink and fsync the
directory. The temporary name is removed only after publication. Identical concurrent blobs
coalesce; different bytes or duplicate unique receipts refuse. No rename can overwrite an
existing checked slot. An interrupted reservation is not refunded or silently retried.

The parent requires all case completions and798 unique returned slots. Both calls/ and
transport/ must have exact file membership. It assembles the original mode/repetition/case
order, verifies each saved stream hash/expected request/binary/status, checks transport and
checked receipts agree, and compares all six results/refusals per case. Missing, extra,
duplicate, foreign or changed records fail. campaign.json is published last, after workers
exit cleanly, full original/new input snapshots match and all byte budgets pass. A partial
or failed run can never create a completed campaign receipt. Fresh output directories are
mandatory; the stopped88-call run is never resumed or overwritten.

Worker exceptions, EOF, early exit, foreign result, startup/task/global deadline and budget
failures stop dispatch. SIGTERM raises in each owned worker so the unchanged runner's finally
block can kill/reap its fresh native process group. A stuck worker receives SIGKILL. The
supervisor is deployed only as the entrypoint of its **dedicated container**: on fatal exit,
container teardown reaps remaining descendants. The outer launcher additionally kills only
that uniquely named container on its time/byte limits and reaps its own Docker client. No
shared-host process search/kill, capability change or privileged fallback exists. Host-only
unit workers do not launch native children; production transport cleanup evidence is reused.

Before/after snapshots cover all bounded mounted source/data/runtime/helper/authority entries,
including the installed HostRecord/decision, original preflight/release and external selector,
not just generator-support members. Snapshot lists remain private; receipts publish compact
hashes/counts. The original imported module origins remain private and pinned. Root ownership
plus readonly mounts relies on a trusted human/Docker administrator preventing writable aliases
through the execution interval; it is not a claim of protection against privileged host mutation.

Replay remains the original actual-result parser/checker control: verify all798 receipts,
then K06-02 and S08-zero-bridge in fresh private layouts, producers and subprocesses prohibited,
with saved corruption/refusal/restoration checks. New full input snapshots also surround replay.
No schema-positive synthetic object, saved replay or toy scheduler task counts as a fresh
native invocation. Public observations and V01–V28 boundaries remain the original approved
validation.md; private Wheel/Arena, human L1, components and performance stay separate.
