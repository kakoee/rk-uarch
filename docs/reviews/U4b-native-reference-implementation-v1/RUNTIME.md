# Local runtime breakdown and regression selection

Other local verification/build work could overlap these observations; this was not an
isolated timing experiment. These are local host wall times and resident-memory observations from the completed
implementation campaign, not simulated TPU durations or controlled-host performance
qualification. Timing began during the b8 layer after the user requested it. Completed
cases were not restarted. The original full campaign kept its native binary throughout;
final admission-only checks were verified separately. No observations were removed and
no broad optimization was undertaken.

## Measured large cases

All times below are seconds. A range is a sampled process bound, not statistical uncertainty.

| Unit | Preparation | Release process, each of 3 | Debug process | Ordinary replay total |
| --- | ---: | ---: | ---: | ---: |
| `layer-b8-s1` | 246.2–246.7 | 15.2–17.1 | 111.4–111.9 | 165.3 |
| `layer-b32-s1` | 453.6 | 46.4–48.6 | 263.7–264.2 | 339.8 |
| `layer-b1-s128` | 156.6 | 13.7–15.4 | 106.1–106.6 | 123.5 |

Replay components (already included in replay total):

| Unit | Input schema validation, both calls | Output parsing | Output schema validation | Independent checker | Canonical input/output serialization |
| --- | ---: | ---: | ---: | ---: | ---: |
| `layer-b8-s1` | 114.1 | 10.3 | 12.0 | 8.4 | 16.8 |
| `layer-b32-s1` | 204.6 | 28.4 | 32.5 | 21.3 | 42.4 |
| `layer-b1-s128` | 77.8 | 10.3 | 12.6 | 7.3 | 13.6 |

Peak resident memory (GiB):

| Unit | Preparation | Release native, observed lower bound | Replay worker |
| --- | ---: | ---: | ---: |
| `layer-b8-s1` | ≥ 7.21 | ≥ 4.30 | 7.51 |
| `layer-b32-s1` | 11.55 | ≥ 11.71 | 11.04 |
| `layer-b1-s128` | 6.73 | ≥ 4.03 | 6.65 |

For B32, preparation took 453.6 s: mapping/bundle validation 132.1 s, job assembly/
validation 209.8 s, and the other preparation work together 111.8 s. Replay took 339.8 s;
its largest measured component was repeated input/schema validation (204.6 s). The
independent checker took 21.3 s. The replay worker took 368.4 s in total, including
imports and convergence hashing in addition to ordinary replay. These numbers identify preparation
and validation as the dominant costs for this case; they do not isolate native event
execution from native admission/serialization.

B32 second-prime preparation took 52.3 s and the final normalized observation comparison
61.2 s; the separate two-prime native process is retained in the machine-readable summary.
No first-pass checking was skipped: the comparison requires equality of all remaining
result content after checking the new identity/bindings and excluding only the legitimate
identity and prime-count differences.

Raw records: [worker phases](evidence/runtime-workers.jsonl),
[process samples](evidence/runtime-processes.jsonl),
[summary](evidence/runtime-summary.json), and the
[read-only observer source as executed](evidence/runtime-observer.py.txt).

## Measurement boundaries

`runtime-workers.jsonl` contains exact `perf_counter` wall intervals from newly launched
workers and Linux `getrusage(RUSAGE_SELF).ru_maxrss` process-lifetime high-water marks.
Preparation includes mapping, repeated carrier validation, hashing and saved serialization.
Replay includes input loading/admission, output parsing/schema checks, the independent
checker, canonical-byte checking and returned result construction. Its subphase totals
are inclusive where named: **do not add replay total to its components**, or input admission
total to input schema/parse times. The check-worker total additionally includes convergence
hashing after replay and process imports.

`runtime-processes.jsonl` is read-only `/proc` sampling of the already running campaign's
children. Kernel process start ticks and the last-seen/first-absent observations bound wall
time, usually within 0.5 seconds. VmHWM observed while the process was alive is a measured
lower bound on final peak RSS; a brief higher final peak can be missed. Very short launch processes can fall between samples; no retrospective time is invented
for those calls. Their correctness receipt is complete. This also covers
b8 preparation that had started before instrumentation. Native process time includes
native input parsing/admission, simulation and complete result serialization; those internal
phases were not separately instrumented during the live run. There is no estimate presented
as a measured execution-only time. Debug and release runs are distinguished.

The reusable runner now records wall time for each native subprocess directly and worker
subphases separately. Instrumentation lives only in the validation harness. It neither
changes the ordinary production interface nor adds executable/build checks.

## Bounded follow-up opportunities

The current ordinary reference loader parses the saved input once to dispatch on protocol
and then parses the same bytes again in `load_reference_job`. Passing that already parsed
value through an internal dispatch seam can avoid the second parse while retaining strict
JSON and full carrier validation. This is a small candidate change, not implemented here.

Preparation validates the mapper-produced bundle, dumps and validates it again in
`prepare_job`, then embeds a dump in a newly validated job. Replay validates the saved job
and `consume_reference` revalidates a fresh dump before binding the output, then dumps it
again for the independent checker. The latter revalidation protects callers from mutable
nested data. It must remain at that public boundary; an internal immutable validated
snapshot could share the work without weakening that protection. A proposed follow-up
must prove refusal and mutation behavior, not simply delete validation calls.

Canonical input/output comparisons currently create a complete JSON string and encoded
bytes alongside the original bytes and structured models. The existing `blocks` serializer
provides a possible streaming byte-comparison seam with identical canonical semantics.
Sharing one admitted snapshot and streaming the comparison may reduce copying; exact byte
identity, duplicate-key refusal, local laws and every required observation must remain.
These are inspection-based opportunities, not measured speedup claims. No speedup estimate
is supplied. The independent checker remains independent and must still run on replay.

## Everyday versus milestone checks

For an ordinary local change, start with the relevant small tests. A useful common set is:

```sh
REFERENCE_NATIVE=/path/to/debug/uarch-engine ORDINARY_NATIVE=/path/to/debug/uarch-engine \
  pytest -q tests/reference tests/unit/test_ordinary_native.py \
  tests/native/test_ordinary_process.py -k 'not gather_2049'
```

The fresh published-source run completed this selection with 60 passed, 2 deliberately
deselected in 4.57 seconds on this host. That is a measured local result, not a portable
time budget. This keeps literal tails, BF16/INT8, vector/causal attention, memory/scalar, explicit spill,
resource limits, state, replay and discriminating fault controls. The two 2049-token gather
fixtures remain available for changes to paging, tails, layouts or state; excluding them
from this everyday selection does not remove them from the milestone evidence. Native
runtime changes should also run the existing Rust tests and the relevant static checks.

For a small ordinary installed/debug-release/replay smoke selection, use the same campaign
runner with these **existing** IDs:

```sh
--ids matrix-bf16-04 matrix-int8-01 \
  memory-read-1048576 memory-write-1048576 memory-copy-1048576 \
  operator-normalization-decode operator-activation-decode launch-minimal
```

The BF16 1024×1024×1024 choice covers K accumulation and all four MXU owners with a
small mapped graph; the raw INT8 choice covers its distinct output/service type.
Add the affected existing operator, page-size gather or layer when a change touches its
semantics. Tiny GQA/decoder and page-fault tests provide faster diagnosis before those
larger runs. This eight-unit smoke selection does not replace the approved 52-unit scope
or establish coverage of every benchmark class.

Reserve the full 52-unit campaign for an integrated milestone or a change that materially
affects cross-cutting mapping, arbitration, precision, state, serialization or replay laws.
It includes all four full layers, large streams, both gather page sizes, three fresh release
processes, debug equality, installed producer-disabled replay and one/two-prime convergence.
Reuse unaffected receipts for unrelated changes; no automatic full rerun is recommended.
