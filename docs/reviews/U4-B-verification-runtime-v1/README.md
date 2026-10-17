# Verification runtime and existing Python CI — bounded B handoff

Implementation: `5a9232e` (parents `9450e87`, `29f7402`). Baseline: `6208968`.
All 11 integrated stages passed on a clean checkout of that exact implementation.
Publication also preserves the later human component installation at `3949b10` and coordinator
main `149fc32` through merge `23c26c2`; the optimization postimages are byte-identical.
The timing comparison is **pre-installation**, not a full-suite result on that later merge.
Focused post-merge integration checks are separately recorded below.
This is ordinary verification/CI engineering, not simulator, native release or sprint evidence.

## Installed change

- Report validation prepares identical jobs once within one synchronous validation call.
  The bounded 64-entry cache keys the complete current bundle, assumptions and engine bytes;
  deep copies isolate consumers. Every new public validation starts empty. Object, input,
  domain, result, call-order and report checks still run. Discovery and replay are unchanged.
- Existing Python CI selects `tests validation`; its strict contract job alone selects
  `contract/tests --require-vendor`. All 758 overlapping baseline identities were compared
  under actual flags. Strict vendor currentness and schema freshness remain separate steps.
  A real subprocess collection regression proves disjointness and equality to the configured
  default selection. Docs classification and required job names remain unchanged.
- Existing setup-uv v3 dependency caching keys `uv.lock` and `pyproject.toml`. Every job still
  installs with `uv sync --locked --extra dev` and executes current checks. No test verdict,
  host token, `.venv` or executable runtime is cached. Hosted cache savings are unmeasured.
- Opt-in pytest JSONL reports selected/deselected nodes, live starts, setup/call/teardown,
  failures/skips and final exit/counts. CI adds durations, explicit skip reasons and a final
  machine-readable log summary. The sequential local stage runner streams separate logs,
  heartbeats and exact expected-failure identities, records not-run stages, and runs declared
  restorations after a failure. Incomplete runs cannot supply a passing summary.

See [usage and limitations](../../../.github/verification-guide.md), [cost inventory](inventory.md),
[production proposals](production-proposals.md), and the evidence archive/manifest below.

## Measurement protocol

One complete baseline used the old Python CI marker selection, including contract tests.
One complete final integrated run uses the partitioned Python selection plus the unchanged
strict contract selection, followed by existing static/currentness/schema/licence/patch checks.
Both use `/usr/bin/time -v`, JUnit and `--durations=0`; final adds phase telemetry. Exact argv,
node outcomes, package versions, load, cache state and source pins are retained in the archive.

Machine: WSL2 Linux 6.6.87.2, Intel Core Ultra 7 255H, 16 visible CPUs, about 15.3 GiB RAM;
one worker. Python 3.12.14, pytest 9.1.1, uv 0.12.9, pydantic 2.13.5/core 2.46.5.
Lock SHA256 `b6152bd0a0f81e910a69fd5d9d2c1523a0698fe53d57aa06e5a545f0ba30cbab`.
Both complete measurements start in fresh clones/venvs with fresh pytest/Hypothesis caches
and a warm uv package cache; OS page cache and host scheduling are uncontrolled. Hypothesis
report strategies use their existing deterministic settings and no example database. A single
0.446 s collection-only overlap audit ran during the baseline; no concurrent heavy benchmarks.

The focused cProfile run took 59.92 s elapsed, 59.87 CPU s and 172,292 KiB peak RSS for three
recorded nodes. Profiling overhead is substantial; it is not compared as a speed benchmark.
The affected 85-check iteration passed in 145.54 s elapsed, 145.43 CPU s, 101,184 KiB peak RSS.
That selection includes new tests and other tools and is not a direct whole-suite comparison.

An attempted final run was stopped after 45.42 s when telemetry exposed that `--ignore`
does not exclude an explicit configured pytest root. Its interrupted evidence is preserved
under `aborted-overlap/`; it is not a pass or a second complete benchmark. A new collection
regression failed on that command and passed after explicit roots were installed. The final
measurement restarted in another fresh checkout. The fault run also exposed an ambiguous
stage timestamp; overall and per-stage elapsed fields are now distinct and regression-tested.

## Final measured result and coverage

| Comparable command | Elapsed s (GNU time) | User + system CPU s | Peak RSS KiB |
| --- | ---: | ---: | ---: |
| Baseline Python selection, including contract | 921.33 | 906.79 + 13.63 = 920.42 | 570,184 |
| Final Python job, `tests validation` | 901.26 | 887.65 + 13.20 = 900.85 | 573,496 |
| Final strict contract job | 8.62 | 8.17 + 0.45 = 8.62 | 98,024 |
| Final sequential union | 909.88 | 909.47 | 573,496 (maximum, not sum) |

The observed Python-job reduction is **20.07 s (2.18%)**. Including the separate strict
contract execution, the observed reduction is **11.45 s (1.24%)** and **10.95 CPU s**.
Peak RSS increased by 3,312 KiB (0.58%). These small single-pair differences do not establish
a statistically reliable speedup or hosted critical-path improvement. The old Python job's
758 duplicated contract cases consumed 14.451 test seconds locally; their removal is exact,
but startup/cache/order effects mean that number is not a guaranteed wall-clock saving.
Do not add it again to the measured reductions above.

All **2,154 original identities** retain their outcomes: 2,123 passed and 31 skipped.
The final union adds 13 passing regressions, yielding **2,136 passed, 31 skipped**;
Python retains the original 277 marker deselections. All skip reasons match exactly,
including 29 analytic capability/premise cases and two absent human L1 inputs. Final Python
is 1,378 passed/31 skipped; strict contract is 758 passed. No failures, missing cases or
identity overlap remain. Original per-test JUnit time sums decrease from 916.112 to
894.541 s; the 13 new checks add 9.999 s. Whole-command figures above include collection,
telemetry and process overhead and are the primary elapsed measurements.

Report validation's group total is **206.474 → 202.141 s**, with one added public activation
regression. The earlier focused iteration's 145.54 s is much lower, but has different suite
context and is **not** a valid claim of a 60-second optimization. Most whole-suite cost remains.
Largest final groups: report validation 202.141 s, companion CLI 78.507 s, B companions
72.924 s, stage2 cards 72.217 s, refresh 66.744 s, support policy 40.562 s. Guard/fixture
lifetime and repeated validation in a long-lived test process warrant future focused study;
this run does not attribute their contribution or weaken them.

The final integrated runner also passed Ruff, both mandatory mypy commands, new-tool mypy,
import-linter, strict vendor currentness, schema freshness, licences and third-party patch
checks. All 11 stages completed in 915.957 monotonic seconds. The runner's monotonic stage
measurements differ slightly from GNU time's wall measurements on this WSL2 host; both raw
records are preserved. Fresh-venv installation from the warm uv cache took 0.23 s elapsed,
0.40 CPU s, 41,216 KiB RSS. Hosted cache benefits remain unmeasured.

## Faults, restoration and focused regression mapping

The isolated fault campaign at `29f7402` completed 11 stages in 35.616 s, 35.306 CPU s,
71,660 KiB child high-water RSS: one four-test positive selection, five discriminating
negative runs and five restored positives. Each mutant exited 1 at the named assertion;
restoration hash-checked exact preimages in `finally`. The disposable clone ended clean.
Later commits change only telemetry/tests/workflow; the faulted source preimages are unchanged.

| Fault | Exact regression (file prefix shortened only in this table) | Required result |
| --- | --- | --- |
| Trust claimed bundle hash after input mutation | `test_preparation_reuse.py::test_preparation_reuse_returns_isolated_equal_jobs_and_rejects_drift` | Changed bytes must reach the real factory and refuse |
| Return shared prepared objects | Same regression | A consumer's nested-dict mutation must not contaminate later jobs |
| Ignore changed assumptions/engine context | `test_preparation_reuse.py::test_current_assumptions_and_engine_are_part_of_preparation_key` | Bad assumptions refuse; current engine is reflected; restored context passes |
| Bypass preparation reuse | `test_analytic_report.py::test_public_validation_reuses_only_preparation_within_one_call` | Real public validation activates reuse and prepares afresh on the next call |
| Treat executable docs as prose | `test_ci_scope.py::test_non_markdown_or_unknown_paths_keep_full_suite[docs/reviews/probe.py]` | Full CI required |

`fault_controls.py` and `fault-plan.json` contain complete identities and exact replacements.
The mandatory repetition/order regression compares real prepared jobs for all 14 active smoke
cells, including four calls for repeat/saved-replay cells. No public boundary is replaced by a
mock. Observing wrappers call the real factory. Existing analytic fault/retention tests remain
part of final coverage. Telemetry tests also exercise failed, skipped, interrupted and empty
runs, incorrect fault identity, restoration, and refusal to reuse an output directory.
This mapping is prospective tooling, not a replacement for mandated broad/independent checks.

## Checks on the subsequently installed component main

After main advanced, merge `23c26c235f8e2918b569d017b867726ba2eb6b2b` preserved human
installation `3949b10`, coordinator tip `149fc32` and measured subject `5a9232e` as ancestors.
Its diff against published main contains only this task's 12 owned paths, with identical
optimization postimages. No installed component/protected byte was edited by this task.

All 11 post-merge stages passed in 44.406 s (a functional check, not a
replacement performance benchmark): **54 focused checks**, **843 strict contract tests**,
Ruff, both required mypy commands plus tool mypy, imports, strict currentness, schema,
licences and patches. The focused selection includes the actual CI partition regression,
progress tooling, preparation faults/public activation, installed identity/tamper tests and
the historical-selection join. Its collection receipt covers 1577 current Python nodes and
843 contract nodes, with disjoint union equal to the current default marker selection.

The full Python suite and broad component campaigns were **not rerun on this later source**.
Their earlier author/reviewer evidence remains separately pinned and inherited. This avoids
transferring the old benchmark or a full-suite verdict to the newly installed component code.
Exact commands, outcomes and collection receipts are in `postmerge-*` and `postmerge/`.

## Reconciliation, remaining work and limits

The separate main clone preserves peer commits `aa5428e` and `56c0871`, including component
installation joins, transient-lifetime tests, proposals and historical evidence. During the
measurement, main advanced through the approved human installation `3949b10` to `149fc32`.
A normal merge onto that published main preserves both histories and the measured commit.
The optimization diff against published main changes no component, production, protected,
generator-closure or sealed runtime file; the human installation remains its own commit.
The normal Lane B and coordinator checkouts were not used for edits or integration. Normal
human-owned/frozen-prediction hooks ran; no override or force push was used.

Largest remaining recurring groups include public table/artifact loading, stage2 cards,
companions and refresh/source-policy tests. Profiled A/protected hotspots and bounded proposals
are recorded separately. A consultation was requested through the coordinator; no A response
has been received yet, and no A-owned change depends on this handoff. No duplicate checks were
requested from A. Future protected regex/serialization work requires its own approval/review.

One worker remains the measured safe default. CPU time tracks elapsed time; the historical
11-worker native campaign cannot establish a Python pool size. No xdist/sharding dependency,
new hosted action or normative cadence change is installed. Full phase/JUnit files are local
runner files; only summaries are retained in hosted logs. Durable hosted artifact upload is a
separate dependency proposal. Hosted behavior and cache benefit were not polled or measured.

Inherited only: Stage 3 verdict, broad component proposal/installation campaigns, K2's 798 real calls
and 26 corruption controls, and saved replay with zero new calls. These were neither rerun nor
counted as fresh checks. Native CI, runners, registry, nightly and controlled-host performance
remain deferred under U0024. Existing golden/determinism/perf/ordering fixture guards have no
inputs and are recorded as such, not passes. All mandatory execution/replay obligations remain.

## Reproducible evidence

[Archive](evidence.tar.gz) and [per-file SHA256 manifest](evidence-manifest.json) contain the
exact argv/patch, environments, baseline/final XML and logs, phase streams, profile data,
fault positives/negatives/restores, development corrections, interrupted attempt and both
integrated-stage summaries. Archive members were read back and hash-verified before commit.
Archive SHA256: `b8cc2b4b7a161b7274ec110b38ec582f015445d1117b7f6e0cd85ba40d06b0f8` (918,063 bytes, 134 files).

Convenient summaries: [measurements](measurements.json), [coverage comparison](coverage-comparison.json),
[source pins](source-pins.json), [environment comparison](environment-comparison.json),
[restoration](restoration.json), [post-merge source](postmerge-source.json) and
[post-merge checks](postmerge-checks.json). `compare.py` inside the archive reproduces the
identity/outcome/skip reconciliation from the three full-run XML files. Performance receipts
remain pinned to the measured commit; future source or runtime changes need fresh applicable
validation and never inherit a cached acceptance or host token.

Publication reconciliation also preserves `3b5e030` (component development approval and lane
prompts only), which arrived during the first push attempt. It changes no runtime/test/CI
postimage; no additional test rerun or native activation is credited to this optimization.
