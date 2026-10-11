# U3 CI illustration portability correction

The hosted Python job failed on the frozen skipped-only illustration test. In
[run 38178529600](https://github.com/kakoee/rk-uarch/actions/runs/38178529600), `uv sync`
selected system CPython **3.12.3**; the immutable illustrative payload records **3.12.14**.
Both environments used Hypothesis 6.168.3 and pytest 9.1.1. `.python-version` requests
3.12, not one specific patch release. Local checks used 3.12.14, so they missed this.
The coordinator reproduced the exact Toolchain identity mismatch by substituting the
hosted version into the runtime observation before running the original test.

The fix is confined to `validation/reporting/test_analytic_report.py`. The frozen example's
illustration-boundary test now explicitly supplies its recorded toolchain as its controlled
unit-test environment. It still validates the unchanged payload and refuses actual-run
promotion, default actual-only admission and an invented passing reduction. This is a
historical illustrative fixture, not new execution evidence or an environment claim.

Four separate tests establish that a differing Python, Hypothesis, pytest or lock identity
is refused. Each has a matching-environment positive control. Removing only the unchanged
production toolchain guard in process memory makes all four fail with DID NOT RAISE;
restoring the guard leaves all five selected tests passing. The five tests also passed
with the observed Python version set to the hosted 3.12.3 value. Scoped Ruff and whitespace
checks passed. Early simulated-environment tests emitted only pytest assertion-rewrite
warnings because the harness imported the report before invoking pytest.

No production validator, illustrative payload, accepted policy, runtime implementation,
workflow, Python requirement, dependency, support inventory or generated artifact changed.
Recorded report evidence keeps its original Git/toolchain bindings; test edits do not
relabel historical reports as produced by this new revision. A's unpublished RoPE work
is untouched. This coordinator fix should be integrated by B through normal Git before
further work; it does not expand B's authorized implementation scope.

The next hosted run is the full CI verification; local checks above are not a hosted-green
claim. The earlier coordinator SR-C1 acceptance covered its bounded correction and retained
reports, not hosted CI. This newly reported failure is addressed separately here.
