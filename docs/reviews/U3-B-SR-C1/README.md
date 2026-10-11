# Lane B SR-C1 correction and execution handoff

This is the author's bounded correction for
[coordinator reconciliation](../U3-schema-report-reconciliation-v1/README.md), not an
independent U-REVIEW verdict. Scope is `validation/reporting/` and its owned tests/docs.
Javid is acting human decision-maker. No protected or production path, support rule,
dependency, profile/corpus definition, external pin, reduction or eligibility rule changes.
The original reports retain their `eab89e0` identities and bytes.

## Correction

`Recorder.invoke` now initializes the retained value before attempting serialization,
catches return-conversion/validation errors and builds an encodable diagnostic before
emitting `call_finished` and raising `EngineStopped`. The error call retains its job,
null result and non-null diagnostic; the case is `ENGINE_ERROR`/not_run. Ordinary engine
exceptions and malformed result identities retain their previous handling. No error is
a valid example, candidate counterexample or killed mutant.

Serializable malformed JSON retains its exact canonical JSON value in `output`, including
`{}` and stale-identity outputs. If that is impossible, the diagnostic uses
`output_representation={format: "invalid-engine-output/1", value: <tagged tree>}`.
This is explicitly diagnostic data, never repaired EngineResult JSON:

- Each node names its Python type. Nonfinite floats use `encoding=nonfinite` and
  `nan`, `+infinity` or `-infinity`; these are labels, not invented finite numbers.
- Built-in dict/list/tuple structure and representable scalar content are retained.
  Dict entries are sorted by their canonical diagnostic bytes; strings use reversible
  `unicode_escape` encoding, including otherwise unencodable surrogates. Very large
  integers use hexadecimal text to avoid the interpreter's decimal conversion limit.
- Opaque objects retain type and explicit `unavailable=unsupported_python_value`.
  No opaque repr, address, property walk or fabricated object contents enter the fallback.
  Cycles and depth beyond 64 are explicitly unavailable, not silently dropped. This is a
  diagnostic description, not a lossless serialization of arbitrary Python objects.
- Tracebacks remain operational; stable diagnostics do not include their host details.

The saved coordinator probe was run from repo root with `PYTHONPATH=.:src:contract`.
Before correction, `{}` retained 14/14 call finishes and validated; NaN and object each
had 14 missing diagnostics/finish events and public validation raised TypeError. After
correction, **all three have 14 starts, 14 finishes, zero missing diagnostics and accepted
public validation**, with partial/not_run reductions. These are illustrative injected
failures, not qualifying real-engine reports or positive verification claims.

## Tests first and production-revert discrimination

Six full-path cases were authored first: `{}` control, NaN, positive/negative infinity,
object and nested object/NaN. Before implementation: **5 failed / 1 passed**. A separate
cycle/opaque/serializer-exception diagnostic test also failed before implementation.
The full-path tests freeze plan/corpus expectations before replay, call public validation,
check every ledger and finish event, require zero valid examples/no mutant kills, and
also replay with the healthy engine without erasing the discovery errors.

[production_revert.py](production_revert.py) extracts only the original `Recorder.invoke`
method from `7454ececbdc03cddd83194ac756a41cd06d99392` into scratch process memory. It
restores that method for the selected tests and restores the fixed method in `finally`.
No live source edit, branch, checkpoint directory or repository copy is made. The revert
run produced **6 failed / 3 passed / 34 deselected**: all five failure probes and the
explicit-representation check failed, while JSON, ordinary engine-exception and malformed
identity controls passed. Two pytest plugin assertion-rewrite warnings are incidental to
invoking pytest after importing the runner. With the fix restored, the same selection
passed **9 tests / 34 deselected** (92.50 s).

Commands, from the Lane B root using its existing locked environment:

```sh
PYTHONPATH=.:src:contract uv run --no-sync python docs/reviews/U3-schema-report-reconciliation-v1/probe_invalid_output.py
uv run --no-sync pytest -q validation/reporting/test_analytic_report.py -k invalid_return_full --junitxml=/tmp/u3-b-src1-before.xml
uv run --no-sync pytest -q validation/reporting/test_analytic_report.py -k diagnostic_is_deterministic
PYTHONPATH=.:src:contract uv run --no-sync python docs/reviews/U3-B-SR-C1/production_revert.py --junitxml=/tmp/u3-b-src1-revert.xml
uv run --no-sync pytest -q validation/reporting/test_analytic_report.py -k 'invalid_return_full or diagnostic_is_deterministic or all_calls_and_errors or malformed_result' --junitxml=/tmp/u3-b-src1-focused.xml
uv run --no-sync pytest -q validation/reporting/test_analytic_report.py --junitxml=/tmp/u3-b-src1-report-tests.xml
uv run --no-sync ruff check .
uv run --no-sync mypy src contract/uarch_contract scripts
uv run --no-sync mypy --no-explicit-package-bases contract/tests
uv run --no-sync lint-imports
uv run --no-sync python -m uarch_contract.generate --check
uv run --no-sync python scripts/vendor_rk.py --check
```

The complete focused report suite passed **43 tests, zero skipped**, in 188.92 s.
[Regression receipts](regressions/) retain the before/after probes, expected failing
revert results and successful corrected test runs.

Ruff, both current CI mypy commands (68/28 files), both import contracts, schema freshness
and strict vendor/support currentness passed. Static checks used no PYTHONPATH override.
The full project suite is not repeated for this bounded standalone recorder correction;
the earlier 1,456 passed / 29 skipped result remains the prior run, not this run.

## Remaining boundary

U2 physical-resolved/1 accounts for its captured operator graph. It excludes RoPE
rotation/conversion work and coefficient traffic; its vector/byte counts and timing
are not complete RoPE-equipped decoder work. This does not change historical numbers,
nominal compatibility outcomes, parameter counts or the matrix-count convention.

STUB, unknown error and unverified energy remain. No production attachment, source/review/
card admission, v2 execution, candidate simulator run, support-rule change or independent
review is authorized by this correction. Runner registration/manual nightly remain pending
with Reza; local receipts do not satisfy that gate. Tool selection, instrumentation,
fallback, U0005/200-second limit and G2 verdict remain pending. Stop after publication for
coordinator reconciliation; no later implementation or sprint closure follows automatically.

## Commits and new qualifying execution

- `cbaa1632a00e12ac8469a146707a4e02ea33b2d7`: tested SR-C1 implementation, seven
  added tests, scratch revert harness and regression receipts.
- `85a5ad29820bc1c8638d844e192c6e4d778c107b`: normal merge preserving coordinator
  approval/installer documents through `df4caf81969c5aafa90ea183dfc8d9e69334d9f0`.
  No execution dependencies changed in this merge. **Both new suites and reports bind
  this clean committed implementation**, after the tests and fix were committed.

Each generator ran once with the unchanged model-v1 profile definitions. Each froze its
new concrete corpus before two sequential qualifying replays in one process. All four
reports passed internal validation; both external validator commands exited 0 and both
literal `cmp` commands exited 0. No favorable-run selection or additional discovery occurred.

```sh
uv run --no-sync python -m validation.reporting.analytic_report generate --profile analytic-l0 --output /tmp/u3-b-src1-l0 > /tmp/u3-b-src1-l0.stdout 2> /tmp/u3-b-src1-l0.stderr
uv run --no-sync python -m validation.reporting.analytic_report generate --profile analytic-l0m --output /tmp/u3-b-src1-l0m > /tmp/u3-b-src1-l0m.stdout 2> /tmp/u3-b-src1-l0m.stderr
cmp /tmp/u3-b-src1-l0/report-1.json /tmp/u3-b-src1-l0/report-2.json
cmp /tmp/u3-b-src1-l0m/report-1.json /tmp/u3-b-src1-l0m/report-2.json
uv run --no-sync python -m validation.reporting.analytic_report validate --report /tmp/u3-b-src1-l0/report-1.json --expected-plan /tmp/u3-b-src1-l0/plan.json --expected-corpus /tmp/u3-b-src1-l0/corpus.json --expected-implementation 85a5ad29820bc1c8638d844e192c6e4d778c107b > /tmp/u3-b-src1-l0.validate.stdout 2> /tmp/u3-b-src1-l0.validate.stderr
uv run --no-sync python -m validation.reporting.analytic_report validate --report /tmp/u3-b-src1-l0m/report-1.json --expected-plan /tmp/u3-b-src1-l0m/plan.json --expected-corpus /tmp/u3-b-src1-l0m/corpus.json --expected-implementation 85a5ad29820bc1c8638d844e192c6e4d778c107b > /tmp/u3-b-src1-l0m.validate.stdout 2> /tmp/u3-b-src1-l0m.validate.stderr
```

[New execution artifacts](execution/) contain one lossless gzip of the canonical report
per identical pair, exact external plan/corpus pins, original combined two-attempt receipts,
call journals and captured stdout/stderr. Empty stderr files are retained. No code snapshots
or broad manifests are added. Reports retain all inputs/results/counterexamples; journals
retain the actual two replay attempts separately. Stable report bytes exclude operational
host/timing/stdout/stderr. Gzip uses mtime=0; source hashes refer to decompressed bytes.

| New observation | L0 | L0m |
| --- | ---: | ---: |
| Distinct frozen cases / discovery entries | 336 / 336 | 238 / 240 |
| Candidate / mutant cases per replay | 336 / 384 | 238 / 96 |
| Discovery calls | 864 | 768 |
| Candidate / mutant calls per replay | 864 / 960 | 760 / 384 |
| Actual calls: discovery once + two replays | 4,512 | 3,056 |
| Journal call starts / finishes | 4,512 / 4,512 | 3,056 / 3,056 |
| Relations pass / skip / not_run | 14 / 14 / 0 | 9 / 13 / 5 |
| Mutant records killed, per replay | 8 | 2 |
| Whole-rung coverage / outcome | partial / not_run | partial / not_run |

All five named mutants were rejected by their target assertions in both modes, with
24 matched valid control and 24 fault cases per mutant/mode per replay. Candidate errors
are not used as kills. L0 duration-purpose passes; its other purposes remain not_run.
L0m duration-purpose remains not_run. Its aggregate-clock cell has **22/24 distinct
admitted cases** from 24 observed bodies; two repeated inputs are retained in discovery.
The other four not_run cells remain the deferred unused-stipulation and DRAM-bound-clock
pairs. No budget was lowered or cases added to hide the shortfall. This fresh discovery
is distinct from the historical 21/24 corpus, whose bytes/identity are unchanged. Profile
definitions and the verification scope have not been expanded.

| Canonical source binding | L0 | L0m |
| --- | --- | --- |
| Raw bytes | 14,830,926 | 30,699,048 |
| Raw SHA256 | `694682267f0d8d6fe30f150815313e1a00a36c35e565ac54ad2e9eea5d92b7e7` | `2a57c5033aaf748087320cdad56ffd7f1a8a5a47118afaf3feb3f63baab79c84` |
| Plan SHA256 | `82a4f2aa8ca8f52b7c4c18720f73621f44d53efe9ec3050df046f0a94f1f177d` | `75c23ff5ac02957511aaa7a1f9e363d54f6834c7f173014f81c3824c8e577886` |
| Corpus SHA256 | `524d66e5da316f3e6b1e5ef5abf05358e5457b1cc572eca6c420c7c12676fcad` | `a7264c772a5151eef82150145ee9033da7848222829952d98fc816e7aa646533` |

To validate retained L0 bytes, decompress `execution/L0-report.json.gz` to a temporary
JSON file and use that file with `execution/L0-plan.json`, `execution/L0-corpus.json`
and the full `85a5ad2` implementation pin above; use L0m counterparts for L0m. These
pins must come from the reviewed publication, not be inferred from an untrusted report.
A different checkout cannot reuse the same version string to evade implementation checks.
No hash depends on the later artifact-publication commit.

Operational receipts record nightly=not_run, no operational errors, and local generator
elapsed times of 461.64 s / 441.65 s. These overlapping validation workloads are not
simulator benchmarks or evidence for U0005/200 seconds. Original model-v1 engine,
assumptions and toolchain identities remain in the source; no accepted review, measurement
authority, model-card hash, designated-host execution or U-P6 completion is fabricated.

## Publication reconciliation

New report evidence was committed as `ca43d887f6ee1138ea7765517d77d0770886ef79`.
Final fetch found coordinator `d141f8e0cd2a903be6caed2c2b70d8ac51333a13`, recording
A's human installation in A's local clone. It was inspected and preserved by ordinary
merge `29eb63d8865b1af926a19538ae4244aaf2bd26a6`. Only coordination documents arrived;
the protected installation/runtime commits were not merged into this clone. Strict vendor
verification and the actual-report implementation guard against `85a5ad2` passed after
integration. Historical `U3-B-standalone-report-execution/` bytes are unchanged. No focused
or full suite was repeated for this documentation-only merge or evidence publication.
