# U-P9 handoff — complete 52-unit prediction freeze

All **52 accepted predictions, 104 compressed canonical artifacts and the final STUB
inventory** were frozen together in
[`d366a7e40b3493337d6be8e89af972a23f6ab2c5`](https://github.com/kakoee/rk-uarch/commit/d366a7e40b3493337d6be8e89af972a23f6ab2c5),
`FROZEN PREDICTIONS: TPU v5e accepted 52-unit reference suite`. The agreement/source commit is
`4961e945bfd13cd6b91ddf7f8895af7727676803`, preceding all prediction generation. No TPU,
compiler or device timing/counter measurements were read, requested or run. No engine,
model, hardware, mapping, contract or accepted workload changed.

## Archive and provenance

The original 47 records and 94 artifacts remain byte-identical. Recovery completed only
`layer-b32-s1`, `layer-b1-s128`, `gather-p16-c2048`, `gather-p32-c2048` and `launch-minimal`,
sequentially. All 51 records and 102 artifacts present before the final B32 retry remain
byte-identical to [the pre-retry snapshot](recovery/pre-retry-survivors.json).
The [final audit](recovery/final-archive-audit.json) verifies all compressed/uncompressed
hashes, exactly 52 accepted IDs, 104 referenced artifacts and no unreferenced artifact.
The [acceptance log](recovery/final-acceptance.log) records metadata and cross-binding checks.

The [inventory](../../../validation/L3_silicon/tpu-v5e/predictions/UNKNOWNS.md) lists all
**17 unchanged numerical STUB claims**, including the 16 reported consumed across the
52 predictions. Counts include admission/normalization reads and do not prove sensitivity
or timing contribution. `barrier_latency_ps` is parsed/validated but no explicit mapped
barrier consumes it. Nine fact leaves and all nominal values remain unchanged.

Original records retain their historical `freeze.py` hash and `/tmp` origins. The five
recovered records identify `recovery.py` and its original helper hash. B32 additionally
identifies its external diagnostic sampler and the original generator of its reused input;
it does not claim fresh preparation. The original utility remains byte-identical. The
[archive guide](../../../validation/L3_silicon/tpu-v5e/freeze/README.md) explains canonical
content, full diagnostics, work/traffic conventions and producer-disabled replay.

## Recovery and observed resource cost

The [recovery record](recovery/README.md) documents the original Docker image, source export,
locked Python environment, release executable and source/build verification. The wrapper
removes overlapping large object lifetimes, separates eight phases into short-lived
processes and streams archive writes while preserving installed validation, independent
checking, canonical content and required diagnostics. No dependencies were added.

The original WSL headroom safely stopped three B32 attempts. Their journals and exact
superseded wrapper versions are retained; none is labelled an OS OOM kill. After the user
increased WSL's budget and restarted it, the new boot and actual resources were verified:
23.47 GiB total RAM, about 20.6 GiB available, 12 GiB unused swap, and no observed effective
cgroup/rlimit cap. The assistant did not change host/WSL settings or stop unrelated processes.
The complete saved input was hash-checked, reused with honest provenance and fully revalidated.
Earlier partial attempts were preserved; a new attempt directory was used.

The **single authorized retry completed** in 482.59 s inclusive. Native invocation took
41.40 s; peak RSS was 9.12 GiB for Python and 11.71 GiB for native. Approximate sampled
combined RSS peaked at 11.96 GiB; shared pages may be counted twice and peaks can be missed.
Sampled available RAM stayed at least 8.68 GiB and swap use stayed zero. The live 2 GiB
reserve remained active. Native and CLI exited zero; no supervisor stop occurred.
Input compressed from 192,935,120 to 10,581,579 bytes; output from 467,173,575 to 54,141,287.

[Runtime/memory observations](recovery/performance-summary.md) separate host cost from
simulated chip durations, and inclusive totals from separate stage timings. Incremental,
fsynced records retain completed stages. Python validation/revalidation and analytic
resolution dominate much of the observed host time. Native internal parsing/admission,
simulation and output construction remain unmeasured; external RSS cannot distinguish them.
Potential follow-ups are a separately scoped native memory profile, less duplication of
validated Python representations with checks preserved, and reduced short-worker polling
overhead. These are options, not automatic work or new acceptance requirements.

## Acceptance and publication procedure

- Final local acceptance: **58 passed, 2 native equality tests deselected**. This covers
  the full 52-record metadata/archive/cross-binding checks, producer-disabled replay,
  affected refusals, 18 synthetic ordering cases, and documentation/prompt/CI-scope checks.
  Unaffected native cases were not repeated solely for telemetry.
- Earlier focused wrapper verification: 24 passes; preparation-lifetime split: 4 passes;
  final consumer-phase split: 4 passes; saved-input hash refusal: 1 pass. These compare
  exact existing BF16/INT8 canonical input/output and compact prediction content, retaining
  all checks and documenting changed provenance/compression. They are not new campaign units.
- All 141 original survivor files and all 153 pre-retry files are unchanged. Complete
  compressed/uncompressed hash audits pass, with no missing or unreferenced artifacts.
- Scoped Ruff and whitespace checks pass; all 30 local links resolve. Duplicate retry
  refusal also passed without launching a worker or changing the journal. Existing
  full-history CI ordering is retained, and its checker now treats nested compressed
  artifacts and the inventory as immutable prediction evidence. Synthetic histories
  reject early/same-commit results and changes later restored to their original bytes.

All 157 prediction-namespace files were committed together using the installed standard
ownership/frozen-prediction hooks. The [committed history check](recovery/final-history-check.log)
verified ordering and immutable history for all 157 evidence files. Publication targets
`origin/main` with a normal fast-forward push; the remote was rechecked at
`68844bb08bf4c9d0494d52fb517cbf68b2db7cc4` before commitment. No hook bypass or
human-override flag was used. No prediction byte may change after the freeze commit. Remote CI/native/nightly and controlled-host performance evidence
remain deferred under U0024; local checks do not claim those passes or final qualification.

## Lane B handoff and claim limits

The operative comparison remains compiler-chosen/steady at each agreed unit boundary,
calibration stub, error unknown and energy unverified: admitted R / C1-ceiling native plus
U-C0 aggregate/per-op. Compiler-reported FLOPs/bytes remain null until independently observed.
Preserve the exact compiler/event/materialization/precision/state correspondence; unmatched
envelopes are incomparable. Do not revise predictions or tune priors using later timing.
F3/F4/F5/F6 limitations remain disclosed; diagnostics cannot establish physical causes.

The [proposed U0009](proposed-U0009.md) limits the reference to few-large-systolic-core
families and excludes mesh-shaped architectures. It remains a human-installation proposal:
[CLAUDE.md](../../../CLAUDE.md) says “Agents propose and stop on contract/,
tests/golden/expected/, CLAUDE.md, docs/decisions/.” No protected ADR was installed.
This completes prediction preparation/freezing; it authorizes no measurement campaign,
paid hardware, broad optimization or accuracy badge.
