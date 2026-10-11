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
