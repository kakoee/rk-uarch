# U5 prediction archive

**All 52 accepted predictions and 104 archives are complete.** They are frozen together
with the inventory in the `FROZEN PREDICTIONS:` commit carrying this guide. See the
[handoff](../../../../docs/reviews/U5-prediction-freeze-v1/README.md).

The 52 predictions use the unchanged, human-accepted suite and the installed reference
preparation, native /5 and retained U-C0 APIs. The operative agreement is committed in
[SUITE.md](../SUITE.md) before generation. The model is
[src/rkuarch/workload/tpu_v5e.json](../../../../src/rkuarch/workload/tpu_v5e.json),
not the absent legacy HardwareSpec YAML. The exact hardware is embedded in every saved job.

Each `predictions/<id>.json` is a compact comparison record. Its `artifacts` references
SHA-256-bound, deterministic gzip files containing the complete canonical prepared job
and native simulator output. These files are **simulator predictions**, not measurements.
The job includes source operators, coefficients/page indices, complete mapped TaskGraph,
producer/mapping versions, hardware, assumptions, admission, seed and priming state.
The native output retains every observation, count and diagnostic exposed by the engine.
All files are committed together. Never edit the JSON, compressed inputs or outputs after
that commit; changed inputs or software require a new prediction identity and commit.

`provenance.image_digest` is the actual local Docker **build image ID**, explicitly
identified as such; it is not a registry digest or a claim that execution ran in a container.
Generation uses the fresh committed export and its release executable on the local Linux/WSL
host. Module origins, package versions, source commit, generator hash and host identity are
recorded. U0024 remote/native/nightly and controlled-host obligations remain pending.

The intended family scope is **few large systolic cores**, limited to domains supported
by future comparisons. **Mesh-shaped architectures are outside this reference's scope.**
The [proposed U0009](../../../../docs/reviews/U5-prediction-freeze-v1/proposed-U0009.md)
records those limits for human installation under the repository's protected-ADR workflow.

## Reading the three predictions

`native.duration_ps` is the admitted R interval model/3 prediction. U-C0 `aggregate`
uses the maximum of total compute and total logical-memory service; `per_op` sums each
operator's maximum. Exact rational ps accompany float display values. Their `ops` map
retains the individual analytic durations and work. These are distinct abstractions;
U-C0 does not execute the mapped graph or represent native setup/padding/staging/latency.

`predicted_flops` uses source-level useful mathematical work: FMA=2 and scalar arithmetic
or special functions=1. Cast, broadcast, comparison/select and integer index work are
excluded and retained separately in primitive/native counters. Raw INT8 dot operations
are `predicted_integer_ops`, not FLOPs. This explicit reporting convention is not an
assertion that XLA's FLOP analysis uses the same convention. Native useful/issued/semantic
counters are preserved verbatim; mathematical work is not claimed as an independent device
observation. `predicted_bytes` means HBM payload read+write for native and logical operand
bytes for U-C0; native VMEM bytes remain separate. Physical transaction counts are unavailable.

No compiler or device counts have been observed. Their numeric fields are null. Lane B
records those independently, preserves exact compiler/event/materialization/state
correspondence, and labels unmatched envelopes incomparable. The fixed 16/32-token gathers
support only consumers using those page sizes; rk-sim has no universal fixed block size.
F3/F6 diagnostics cannot establish physical causes. F4 remains a /4 refusal-code limitation;
F5's serialized gather/attention/activation staging and all numerical STUB priors are retained.

## Replay without preparation

Use the recorded package/model versions and a compatible installed native executable.
From the repository root:

```sh
python validation/L3_silicon/tpu-v5e/freeze/freeze.py replay \
  validation/L3_silicon/tpu-v5e/predictions/launch-minimal.json
```

This verifies archive hashes, validates the saved job and output through the installed
consumer, and recomputes U-C0 from the saved source. It imports no preparation/mapping
producer. Add `--executable /path/to/uarch-engine` to execute that exact saved job and
require byte-identical native output. Moving the archive together preserves identity.
Neither replay mode re-prepares, retunes, or overwrites a prediction.
`replay_without_producers.py` accepts the same prediction/executable arguments and rejects
imports of the two reference producers, making the producer-disabled check reproducible.

`prepare` and `predict` are explicit generation commands, documented by `--help`; they
create new files exclusively. They are not replay fallback paths. A new freeze must first
establish its prospective agreement and prediction-before-measurement status. The current
52 identities must never be regenerated in place after commitment.

Run `python validation/L3_silicon/check_ordering.py` with full Git history. The existing CI
ordering job checks strict ancestry and immutable prediction/result bytes; acceptance tests
also bind compressed artifacts to the immutable JSON hashes. History cannot prove absence
of private measurements; this session neither acquired nor read device measurements.

## Crash recovery and host-cost records

The 47 surviving records retain the historical `freeze.py` generator and original
build origins. Five completed recovery records use `recovery.py`, with its own generator hash and
`freeze.py` helper hash. Both use the same committed engine/model/source and original
local build image. Recovery changes object lifetimes and streaming archive writes;
complete canonical inputs, outputs, checks and diagnostic content are preserved.
See the [recovery record](../../../../docs/reviews/U5-prediction-freeze-v1/recovery/README.md)
for exact environment reconstruction, failed-attempt inspection, equality/refusal checks,
and resource guards. Developer wall times/RSS are stored there, separately from predictions.
B32 also identifies the external retry sampler and the original saved-input preparation
generator; it does not claim that reused preparation was performed again.
They are not chip timings or a simulator-performance qualification.

The recovery CLI takes an explicit source export, native executable, provenance file,
work directory, output directory and telemetry journal. `--help` lists the arguments.
Cases run sequentially; existing outputs and nonempty attempt directories refuse.
The utility never falls back from replay to preparation. The historical replay command
above remains valid, but large complete jobs/results require substantial Python memory;
use the recorded headroom/phase observations when planning a large replay.
