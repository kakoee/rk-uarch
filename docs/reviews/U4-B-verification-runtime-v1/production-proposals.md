# Production hotspots: proposed follow-up for A

No new A response is available, as confirmed by the coordinator/user. These are proposed
follow-ups, not approved implementation work or a dependency on the completed B CI changes.
No production/protected file, sealed K2 runtime copy or historical evidence is changed.
Preserve every verification and refusal behavior. No duplicate tests or additional broad run
are requested. This clarification reads existing profile/JUnit data and source identities only.

## Timing semantics and representative callers

The existing cProfile at `6208968` selected the three exact nodes in archived `profile.time`.
It recorded 59.669 s of profiled function time; GNU time measured 59.92 s elapsed including
startup/exit. Profiling overhead is substantial. **Cumulative** time includes callees;
**exclusive** time is the function's own Python body. These nested cumulative values overlap
and must not be added or treated as independent optimization savings. Caller edge times below
are also cumulative. [Derived data](hotspot-followup.md) includes exact unrounded values,
all direct callers and the original profile SHA256; the historical archive remains unchanged.

| Canonical function / owner | Calls | Cumulative s | Exclusive s | Representative measured caller edges |
| --- | ---: | ---: | ---: | --- |
| `src/rkuarch/table/artifacts.py::_load_verified`, A | 12 | 24.289 | 0.008 | `verify_report_inputs`: 8 calls / 16.840 s; `load_verified_report_inputs`: 4 / 7.449 s |
| `src/rkuarch/workload/prepared.py::validate_execution_bundle`, A | 618 | 17.690 | 0.119 | `prepare_engine_job`: 324 / 8.485 s; `fixed_bundle`: 190 / 6.003 s; analytic report `replay`: 44 / 1.442 s; remaining callers: 60 calls |
| `contract/uarch_contract/hardware.py::hardware_unit_rule`, both humans | 246,470 | 19.614 | 2.988 | All from `HardwareSpec.coherent`, itself invoked 5,030 times by Pydantic validation |

For table loading, the in-memory wrapper's callers include `build_table` (3),
`assemble_stub_context` (2), `write_table` (2), and the selected companion test (1).
The disk wrapper's callers are `write_report` (2), the selected companion test (1), and
its saved-input fixture (1). These wrappers perform additional work beyond `_load_verified`.

## Repetition: observed calls versus identical inputs

- **Table loading:** 8 memory and 4 disk validations occur in this small selection. The
  companion test assembles the same carriers twice with reversed artifact ordering, writes
  identical table bytes to `fresh` and `repeat`, copies them to `relocated`, then loads and
  reports that table. This demonstrates repeated logical input use across real public
  boundaries. cProfile did not record table/artifact digests: it does not prove that all
  12 calls have byte-identical input closures or authorize reusing their acceptance.
- **Bundles:** `expected_jobs` calls the real `jobs` factory 162 times, producing 324
  per-point `prepare_engine_job` calls. Its callers are `validate_case` (88) and `exercise`
  (74). The factory iterates points of the same bundle, so this path repeatedly validates a
  bundle for point preparation. There are also 190 `fixed_bundle` validations and 44 replay
  validations. Distinct bundle digests and cross-case identical-input frequencies were not
  captured; 618 is a call count, not a cache-hit estimate. B's installed reuse is limited to
  preparation within one report-validation call, with current-byte keys and isolated copies.
- **Hardware rules:** 246,470 lookups / 5,030 coherence validations averages exactly 49
  sourced-leaf lookups per validation. The hardware-rule caller accounts for **6,735,170**
  `re.escape` calls (10.388 s cumulative, 1.456 s exclusive), repeatedly constructing
  expressions from a 54-pattern rule table. The whole profile's 6,735,331 `re.escape` calls
  include 161 calls elsewhere. Per-pattern/path/input-identity distributions were not
  recorded; rule-expression repetition is established without equating distinct hardware
  specifications or caching their validation verdicts.

## Contribution to the normal CI command

These functions execute inside the real Python selection, historically
`pytest -q -m "not nightly and not silicon and not native and not golden and not determinism"`.
The installed CI command retains those markers and explicitly selects `tests validation`,
with `contract/tests --require-vendor` owned by the separate strict job. This profile is
ordinary Python verification, not a native campaign or controlled-host performance run.

Existing whole-suite JUnit records give these **test-level** elapsed contributions (including
attributed setup/teardown). They are not exclusive function costs:

| Profiled node | Baseline CI s | Final pre-component Python CI s |
| --- | ---: | ---: |
| `tests/unit/test_u2_b_companions.py::test_no_comparison_positive_is_pure_deterministic_and_offline` | 12.535 | 11.999 |
| `validation/reporting/test_analytic_report.py::test_invalid_return_full_retention_and_public_validation[json-control]` | 13.169 | 12.477 |
| `tests/unit/test_u2_support_policy.py::test_relevant_bytes_refuse[hw/designs/npu-l4.yaml]` | 0.598 | 0.522 |
| Three nodes combined | 26.302 | 24.998 |

That is 2.85% of the 921.33 s baseline command and 2.77% of the 901.26 s final Python
command. The enclosing baseline groups cost 73.406 s (companions), 206.474 s (reporting),
and 39.044 s (support policy), but include other work. Other CI paths also call these
functions. **Full-command per-function attribution and identical-input frequency are unknown**;
there was no full-suite cProfile or argument-digest census. Do not scale the 24.289/17.690/
19.614 s samples into whole-CI savings, add their nested costs, or transfer these timings to
the subsequently installed component source. The complete measured union improved only
11.45 s (1.24%) in one local pair, as documented in the main handoff.

## Existing K2 work and bounded next proposals

First compare the current canonical implementation with A's existing
[admission/startup proposal](../U4-A-K2-python-admission-v1/README.md), its exact
[source bindings](../U4-A-K2-python-admission-v1/source-bindings.json), and the
[combined-runtime reconciliation](../U4-K2-combined-runtime-reconciliation-v1/README.md).
That work already supplies three distinct lifetimes: one public-call admission, one
case/mode context across fresh executions, and one shared startup resolution session.
It also supplies a bounded 128-entry cache of compiled **rule patterns**, consulting current
rule order and allowed labels on every lookup. Do not propose those mechanisms as new work.

Read-only hash comparison at published `756d632` confirms canonical
`src/rkuarch/engines/native/runner.py`, `src/rkuarch/engines/native/host.py`, and
`contract/uarch_contract/hardware.py` still match that proposal's **baseline** hashes,
not its optimized postimages. Exact hashes are in `hotspot-followup.md`. The separately
approved immutable Python runtime used for the
[completed K2 campaign](../U4-K2-completed-first-use-v2/README.md) has its own runtime/helper,
placement and authority identities; it coexists with unchanged canonical imports. Its
startup/case-reuse results therefore do not establish that ordinary canonical Python CI
already uses those optimizations. No sealed filesystem tree was opened or modified here.

Proposed follow-ups, with no implementation authorized by this note:

1. **A-owned table/bundle work:** assess repeated immutable parsing/preparation within one
   public operation against existing mechanisms. The native host/case APIs do not automatically
   apply to analytic table or prepared-bundle boundaries. Retain fresh public input/source/
   currentness checks and all per-response checks; changed bytes or identities must refuse or
   revalidate. Do not cache an acceptance/result/host token across changed inputs.
2. **Protected hardware rules:** evaluate a separately identified canonical adoption of the
   already-reviewed bounded pattern-cache approach before inventing another implementation.
   Preserve current rule order/labels, mutation behavior, units, unknown-path refusals,
   exceptions and schema bytes. Canonical installation still requires the protected-source/
   U0002 identity and review lifecycle; runtime-copy approval does not authorize it.
3. **Protected serialization:** `canonical_json` had 80,492 calls / 15.158 s cumulative in
   the same profile; normalization accounts for 11.955 s cumulative. Any future proposal
   requires exact-byte equivalence and non-finite/boolean/order/Unicode refusal preservation.
   No canonicalization shortcut or implementation is included here.

Keep the sealed K2 copies, original 798-call/replay obligations, receipts and historical
review evidence unchanged. New dependencies, cadence changes, worker pools or hosted actions
remain separate proposals. No further tests, native calls, runtime rollout or broad profiling
were performed for this documentation follow-up.
