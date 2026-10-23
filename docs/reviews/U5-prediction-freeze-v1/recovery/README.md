# U5 crash recovery and developer performance

These records describe host execution cost, **not simulated chip durations or TPU
measurements**. They are outside the immutable prediction namespace. The original
`/tmp/u5-freeze` export/build/intermediates were lost in the WSL crash. Before retrying,
`survivors.json` recorded all 47 compact records and 94 archives; both compressed and
decompressed hashes matched, with no unreferenced archive or partial file to reuse.
The surviving records retain their original generator hash and original `/tmp` origins.

## Narrow wrapper change

The original `freeze.py` remains byte-identical. Its prediction path kept a complete
raw job, validated job and bundle while `ordinary.run()` loaded the same job again,
then kept that state alongside native output and analytic validation. It also constructed
whole canonical byte strings and whole gzip byte strings before writing them.

`recovery.py` separates mapping, preparation, input validation/revalidation, native
invocation, output validation, independent checking, analytic resolution and archive
writing into eight short-lived Python workers. The installed ordinary `load_job` and
bounded `_exchange` remain unchanged. The consumer's remaining checks are preserved:
`ReferenceJob.model_validate(job.model_dump(mode="json"))`, `_decode_envelope`,
`ReferenceResult.model_validate`, all four job/result identity bindings, canonical
result equality, and the full independent `check_reference`. Revalidation releases the
old model before constructing its replacement. Native invocation retains only serialized
input, not a validated Python graph. Output schema validation retains no job model.
The independent checker runs on the same canonical job/result dictionaries in a separate
worker. No check is disabled or replaced by native self-reporting.

The analytic worker passes the saved bundle dictionary through a small `model_dump`
adapter to the unchanged resolver, which still validates the entire `ReferenceBundle`.
This avoids retaining an original model alongside its dump and the resolver's new model;
no analytic formula is copied or changed. Source work accounting uses that same saved
source. Canonical result equality uses the existing contract `blocks` serializer,
compared incrementally against saved bytes. Native raw output is persisted after bounded
transport and archived verbatim only after validation and independent checking. Gzip
writing streams 1 MiB chunks. Gzip headers may differ from the historical one-shot
compressor; both hashes are recorded honestly. Complete canonical content and diagnostics
are retained.

Job preparation mirrors the installed `prepare_job` statements at the recorded source
commit: revalidate `ReferenceBundle`, construct/seal the same fields, then validate
`ReferenceJob`. It persists the canonical mapped bundle between workers and releases the
redundant bundle model before final job validation. Canonical small-case equality with
the original APIs is tested. No engine, model, hardware, mapping, workload size,
validation rule or timing law changed.

Every creation is exclusive. A nonempty attempt directory or existing destination causes
refusal; there is no automatic partial-file reuse or overwrite. Explicit `--prepared-job`
reuse requires the inspected file hash and original preparation-generator hash, records
both, and still runs complete input validation/revalidation in a new worker. An interrupted attempt
must be inspected and either independently validated or retained in a separate attempt
directory before resuming. This recovery found no surviving partial job for the five
remaining cases. Completed original cases are not regenerated into the archive.

## Environment and resource controls

The source is a fresh `git archive` of `4961e945bfd13cd6b91ddf7f8895af7727676803`,
under the ignored `.u5-recovery-work/source`. `uv sync --offline --locked --extra dev`
restored its Python environment from the existing cache. `environment.json` records the
actual imported paths, package/tool versions, native executable hash and original image ID.
The local image is `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
The image's cache lacked `sha2`; the old external cache had disappeared. Cargo fetched
only existing locked dependencies into `.u5-recovery-work/cargo-home`; the final build
used `cargo build --release --locked --offline --target x86_64-unknown-linux-gnu` inside
that same image. Source was mounted read-only at `/work`, private cache at `/cargo-home`,
private build output at `/target`, and `/tmp` was a temporary mount. Container network
was disabled, root filesystem read-only, capabilities dropped and no-new-privileges set.
The workspace owner's UID/GID was used for output permissions. No image pull or host/WSL
setting change was needed. `build.log` and `dependency-restore.log` retain the receipts.
Native execution uses the ordinary selected local Linux executable, not a container runtime.

Large cases are sequential. Preflight requires 10 GiB `MemAvailable` and no more than
1 GiB swap used. At one-second intervals the supervisor stops its own worker/native
process tree if available memory drops below 2 GiB or swap use exceeds 1 GiB. These are
operational safeguards, not simulated hardware constraints or qualification thresholds.
They cannot guarantee survival of an abrupt host/VM failure between samples. Native
transport keeps the installed 600 s / 256 MiB input / 512 MiB output / 1 MiB stderr caps.

## Reading telemetry

`performance.jsonl` is append-only and flushed/fsynced after each event. Start/end markers
retain completed stages if a later stage or VM fails. A start without a matching end means
interruption/unknown completion, not success. A guard interruption has an explicit record.
Worker stdout/stderr and intermediate canonical files are retained in the ignored work
folder, while concise failure details and durable timing/status records live here.

- `stage_end.wall_s`: separate preparation, input validation, native invocation, output
  validation and independent checking, serialization, analytic input decoding/resolution
  and compression.
  Preparation includes its own internal validation. Native invocation includes transport
  and startup. The final wrapper measures output validation and independent checking separately; the
  earlier wrappers combined them. Native-internal validation and serialization are
  unmeasured within invocation. `output_serialization_check` measures streamed Python
  serialization plus comparison; `native_output_persistence` measures saving native bytes.
- `worker_end.wall_s` and `case_end.wall_s` are **inclusive**. Do not add nested stage times
  to these totals. Imports, summary/hash I/O and supervision account for some residual time.
- `python_worker_rss.peak_rss_bytes` uses Linux `RUSAGE_SELF`, separately for each Python
  worker, excluding the native subprocess. Stage SELF high-water marks are cumulative
  over that worker's lifetime, not independent stage peaks. Interrupted workers may have
  only their last completed stage's high-water mark; a final exact peak is then unmeasured.
- `native_rss.peak_rss_bytes` uses `RUSAGE_CHILDREN` in the fresh native worker with exactly
  one native child. It covers the process lifetime, including launch footprint. Aggregate
  `worker_wait4_peak_rss_bytes` may include reaped-child high-water marks and must not be
  mistaken for Python-only RSS.
- `memory_sample.combined_rss_bytes_approx` and the corresponding worker peak sum active
  process-tree `/proc` RSS. They are **approximate**: shared pages can be counted more than
  once, and sub-second peaks can be missed. Samples include `MemAvailable` and swap used;
  each case also records before/after memory and completion/failure status.
- `artifact_sizes` records exact input/output byte sizes before and after gzip compression.
  Earlier 47-case runtime details were lost and are unmeasured here; no historical values
  have been inferred from simulation durations.

The focused check log (24 passes), preparation-split and final phase-split logs (4 passes each), and
documentation/scope check log (33 passes) cover existing BF16/INT8 input/output equality, all compact
prediction fields except changed provenance/compression, producer-disabled replay,
input/output canonical refusals, rehashed count corruption through the independent
checker, native refusal propagation, exclusive-create and low-headroom refusal, plus
archive corruption and Git ordering controls. This is local verification under U0024,
not controlled-host simulator-performance qualification.

## Safely interrupted first recovery attempt

The first wrapper still called `prepare_job(map_reference(...))` in one worker.
B32 hit the 2 GiB reserve at 217.4 s: sampled tree RSS 10,459,377,664 bytes,
MemAvailable 1,985,155,072 bytes, swap use zero. The supervisor stopped only its
own worker; available memory recovered to 12,427,730,944 bytes. The attempt folder
contained only `prepare.log`, no prepared input or archive to reuse. Its exact wrapper
source is retained in `attempt1-recovery.py.txt`, matching the first journal hash.
The subsequent attempt separates mapping and job construction as described above;
this is a changed lifetime arrangement, not a retry of the failed configuration.

## Second attempt and saved-input reuse

The second attempt completed mapping (129.05 s), bundle serialization (14.88 s),
job preparation (205.98 s), input serialization (15.27 s), and ordinary input validation
(121.80 s). Mapping/preparation Python peaks were 9,294,426,112 and 9,597,386,752 bytes.
During native invocation, the retained Python job plus Rust process reached an
approximate combined 11,282,403,328 bytes; MemAvailable fell to 1,228,574,720 bytes.
The guard stopped that process tree at case wall time 516.82 s. About 4.5 MiB swap was
used. Native invocation had no completed output to reuse. The exact second wrapper is
`attempt2-recovery.py.txt`; completed input inspection is in `reused-input-inspection.json`.
The final phase split removes this measured Python/native overlap. The third attempt
reuses the inspected complete input, with its old preparation-generator hash, and runs
all subsequent validation/checking. Its preparation time is **unmeasured in that attempt**;
the completed second-attempt times remain available and must not be counted twice.

## Historical native-only resource blocker (before the user restart)

The third B32 attempt completed isolated input validation (116.96 s) and mutable-job
revalidation (97.85 s), with Python peak 9,791,193,088 bytes. That worker exited before
native invocation. The remaining native process plus lightweight transport worker still
reached sampled combined RSS 10,713,477,120 bytes, while MemAvailable fell to
1,761,058,816 bytes. The guard interrupted native invocation after about 30.4 s; there
was no completed native output. Whole-attempt wall time was 246.45 s. Native exact peak
RSS is unmeasured because its supervising worker was killed; sampled combined RSS is a
lower bound on the observed process-tree peak, not an exact native peak or a completed-run
memory requirement. Swap use stayed about 4.5 MiB.

This established a resource blocker beyond retained Python job models: the isolated
native invocation did not fit that safe headroom. The WSL instance then had
16,450,244,608 bytes total memory and roughly 12.5 GB available before cases, with a 2 GiB
operational reserve. The final native peak remains unknown. Do not repeat this resource
configuration; obtain materially more available memory or a separately authorized
engine-memory task. No engine changes, reduced workloads, disabled checks, process kills
outside the task, or host/WSL setting changes are authorized by this recovery.

## Final bounded retry and completion

After the user increased the WSL memory budget and restarted it, the boot ID changed to
`68791309-c325-4b96-9e75-bd9a73de2d00`. Actual memory was 25,199,566,848 bytes total,
22,147,567,616 bytes available at preflight, and 12,884,901,888 bytes of unused swap.
The effective init.scope limits were unlimited; root-cgroup metrics unavailable to this
process are null, and address-space/data rlimits were unlimited. No assistant changed
host/WSL settings or stopped unrelated processes. The 13.5 GiB start threshold was an
operational safeguard, not a measured requirement or success guarantee. The live 2 GiB
RAM reserve remained enabled.

The durable environment survived the restart. All 495 source/build-input files matched
the committed export; Python module origins and locked package versions, native executable
hash, and saved input hash were reverified. All 51 completed records and 102 archives
were snapshotted in [pre-retry-survivors.json](pre-retry-survivors.json). The saved input
was copied to the new `cases-v4/layer-b32-s1` attempt, retaining its original preparation
generator hash and all subsequent validation. Earlier failed attempts were preserved.

`retry_diagnostics.py` launches the existing recovery CLI unchanged, once, and uses only
standard-library/Linux facilities. It refuses an existing diagnostic file or attempt
directory. About every second it records elapsed time, each process's RSS/HWM, separately
identified native RSS/HWM, approximate process-tree RSS, memory/swap and file sizes without
rereading large files. It records limits and identities before/after, explicit native/CLI
status, guard evidence and any supervisor stop. It does not infer an OS OOM kill from a
signal or label internal native phases as measured. Records are incremental and fsynced.
The [preflight](b32-retry-preflight.json), [retry environment](retry-environment.json),
[diagnostics](b32-retry-diagnostics.jsonl), and [summary](b32-retry-summary.json) retain the
receipts. The external sampler hash is honest additional provenance for B32; the preceding
51 prediction records and all existing generator identities are unchanged.

The single retry **completed**, including input validation/revalidation, native invocation,
output validation/canonical equality, independent checking, U-C0 resolution and streaming
compression. Both native and CLI exited zero; no resource guard fired and swap stayed zero.
Case wall time was 482.59 s, native invocation 41.40 s. Peak Python/native RSS was
9.12/11.71 GiB; approximate sampled combined RSS was 11.96 GiB; sampled available memory
never fell below 8.68 GiB. See [performance-summary.md](performance-summary.md) for separate
stage times, byte sizes, historical failed attempts and potential follow-ups.

All **52 predictions and 104 archives** now pass the [final audit](final-archive-audit.json).
All 153 pre-retry files, including the original 141 survivor files, remain byte-identical.
The earlier `archive-audit.json` and `.log` are historical 51-case receipts, superseded by
`final-archive-audit.json` and `.log`. `current-history-check.log` is the earlier
infrastructure-only result before the freeze commit; history must be checked again on the
committed freeze. The final inventory counts all 17 unchanged numerical
STUBs and the 16 actually reported consumed. Final acceptance is recorded separately in
[final-acceptance.log](final-acceptance.log). The existing native small-case equality tests
were not rerun solely to obtain telemetry; earlier equality/replay/refusal verification
remains recorded above. No unaffected campaign case was regenerated.
