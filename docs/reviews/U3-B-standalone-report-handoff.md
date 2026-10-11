# U3 B — standalone analytic report implementation handoff

Implemented and locally exercised the standalone boundary authorized by
[U3-RoPE-and-verification-v1](U3-RoPE-and-verification-v1/README.md): sections 2–4
and 6 of the [supplement](U3-U0006-report-supplement.md) at
`428b7bb29664b7de2b8c8ef8ce3a8bad2e5245ee`, its example and human-committed U0006.
Javid is acting human decision-maker. This is the author's implementation/execution
handoff for coordinator reconciliation, not independent review or U-P6 acceptance.

## Commits and boundary

- `c687848a540eb4e7bd472e5a43da99be15a3df7d`: tests-first standalone generator,
  validator and package under `validation/reporting/`.
- `5276c454bfdde7c0172fef9dfa7d8a7d40213537`: normal integration of peer main,
  preserving A's `e622673577017a50f3e436205809f76fdf7ffae7` schema proposal and
  coordinator `531d9c923c30dd465cf56c8a5865cd9ce62cdd84` bounded authorization.
- `eab89e07b0c7e41f7a2a0ee236dd1b00f78228c6`: implementation binding excludes
  Markdown prose while still rejecting changed execution code with unchanged versions;
  includes a real temporary-Git-repository discriminator. **Both qualifying executions
  and their suite/implementation bindings use this clean, committed checkpoint.**

Human ADR commit `f62eb7025dd5a48f03a81e92bc334f58bfb2a202` is an ancestor of that
checkpoint. Publication of these receipts is a later commit, outside their hashes.
B changed no production source, CLI, dependencies, protected files, loader/card
admission, provenance dispatch, review eligibility, workflow or host configuration.
The Markdown exclusion is specific to this new standalone Git comparison; existing
U0002 support-file/currentness checks remain unchanged and passed.

> U2 physical-resolved/1 accounts for its captured operator graph. It excludes RoPE
> rotation/conversion work and coefficient traffic; its vector/byte counts and timing
> are not complete RoPE-equipped decoder work. This does not change historical numbers,
> nominal compatibility outcomes, parameter counts or the matrix-count convention.

The corpus remains synthetic BF16 model-v1 input. STUB, unknown error and unverified
energy remain explicit; no v2 input, executed MAC/DMA/queue/placement/trace/energy or
steady-state telemetry is introduced.

## Implemented behavior and discrimination

[`analytic_report.py`](../../validation/reporting/analytic_report.py) registers complete
L0 (28 cells) and L0m (27 cells) catalogues in both aggregate and per-op modes.
`analytic-l0`/`analytic-l0m` target 24 distinct valid examples per active cell,
with a 240-invocation cap per cell per ledger; the explicit smoke profiles use 1/8.
Prospective plans, frozen concrete corpora, implementation, toolchain, engine/model,
assumptions, suite, inputs, jobs and results are bound and validated. Validation requires
caller-pinned plan/corpus/implementation expectations, including the complete registered
catalogue; rehashing a favorable subset cannot bypass those expectations.

Discovery uses public Hypothesis APIs with database disabled, derandomization and
both generate/shrink phases. Every observed body/call and failure is retained; repeated
inputs remain in the discovery ledger, while the corpus admits first occurrences of
distinct tuples. Unavailable internal draw/rejection/shrink counts are null. The journal
writes call starts and returned results/errors before evaluating the assertion. Returned
mutable values are detached before subsequent calls can overwrite them. Errors retain
diagnostic bytes; operational tracebacks stay outside stable source bytes.

Fixed-input replay uses retained authenticated bundles without invoking the standalone
producer. Producer relations are explicitly separate and retain intents/emitted bundles;
a producer mismatch before an engine call remains an observed counterexample. Failed
discovery cannot be erased by passing replay. Errors, interruption, distinct-case shortfall
and absent required discrimination remain not_run; applicable failures and surviving
mutants/broken controls dominate reductions. Skipped-only illustration is none/not_run
and cannot claim an actual run. CLI success means a well-formed report, not a passed rung.

[`test_analytic_report.py`](../../validation/reporting/test_analytic_report.py) was written
before implementation (initial collection failed on the absent module). All development
failures were corrected before publication. Its 36 cases, including parameterizations,
exercise:

- populated controls in both modes and identical frozen replays; fixed replay with the
  producer patched to fail; separate batch/context producer checks;
- missing/duplicate case, tampered result, mismatched plan/corpus pins, omitted catalogue
  cells, misleading reduction, unreferenced objects and invalid domain/transformation;
- changed implementation with unchanged versions, and prose-only versus code changes
  in a real Git repository; dirty/uncommitted actual-run refusal;
- discovery failure surviving passing replay, invocation-cap interruption, too few distinct
  cases, boolean budget refusal and omitted calls disguised as interruption;
- surviving mutant/broken control refusal; malformed/error returns never counted as kills;
  all five targeted mutants; explicit counterexample-producing Hypothesis shrinking and
  reproduction, comparing every recorded call to an independently collected call list;
- journal ordering, producer failure before engine invocation and reused mutable results.

Fault-injection test fixtures are labeled illustrations. They establish discriminating
behavior, not extra qualifying actual-run reports or invented independent reviews.

## Actual local executions

Each command below ran once from clean committed `eab89e0`, using this clone's locked
interpreter. Each generator froze its discovered corpus before **two sequential replay
attempts in one process**, with fresh mutant closures. Both files passed internal
validation; external `cmp` returned 0 for each pair. No fresh-process, thread-count,
fork or designated-host determinism claim follows.

```sh
uv run --no-sync python -m validation.reporting.analytic_report generate --profile analytic-l0 --output /tmp/u3-b-analytic-report-eab89e0-l0 > /tmp/u3-b-analytic-report-eab89e0-l0.stdout 2> /tmp/u3-b-analytic-report-eab89e0-l0.stderr
uv run --no-sync python -m validation.reporting.analytic_report generate --profile analytic-l0m --output /tmp/u3-b-analytic-report-eab89e0-l0m > /tmp/u3-b-analytic-report-eab89e0-l0m.stdout 2> /tmp/u3-b-analytic-report-eab89e0-l0m.stderr
cmp /tmp/u3-b-analytic-report-eab89e0-l0/report-1.json /tmp/u3-b-analytic-report-eab89e0-l0/report-2.json
cmp /tmp/u3-b-analytic-report-eab89e0-l0m/report-1.json /tmp/u3-b-analytic-report-eab89e0-l0m/report-2.json
uv run --no-sync python -m validation.reporting.analytic_report validate --report /tmp/u3-b-analytic-report-eab89e0-l0/report-1.json --expected-plan /tmp/u3-b-analytic-report-eab89e0-l0/plan.json --expected-corpus /tmp/u3-b-analytic-report-eab89e0-l0/corpus.json --expected-implementation eab89e07b0c7e41f7a2a0ee236dd1b00f78228c6 > /tmp/u3-b-analytic-report-eab89e0-l0.validate.stdout
uv run --no-sync python -m validation.reporting.analytic_report validate --report /tmp/u3-b-analytic-report-eab89e0-l0m/report-1.json --expected-plan /tmp/u3-b-analytic-report-eab89e0-l0m/plan.json --expected-corpus /tmp/u3-b-analytic-report-eab89e0-l0m/corpus.json --expected-implementation eab89e07b0c7e41f7a2a0ee236dd1b00f78228c6 > /tmp/u3-b-analytic-report-eab89e0-l0m.validate.stdout
```

| Actual observation | L0 | L0m |
| --- | ---: | ---: |
| Distinct frozen cases | 336 | 237 |
| Discovery body/case entries | 336 | 240 |
| Candidate cases per replay | 336 | 237 |
| Mutant control/fault cases per replay | 384 | 96 |
| Discovery engine-boundary calls | 864 | 768 |
| Candidate calls per replay | 864 | 756 |
| Mutant calls per replay | 960 | 384 |
| All actual calls: discovery + two replays | 4,512 | 3,048 |
| Relation pass / skip / not_run | 14 / 14 / 0 | 9 / 13 / 5 |
| Whole-rung coverage / outcome | partial / not_run | partial / not_run |

The operational journals independently contain 4,512 and 3,048 matching call-start/
call-finish events. The same discovery ledger is embedded in both canonical reports;
it was executed once, not twice. All active L0 cells and nine L0m cells reached their
24 distinct-case requirement. Both modes have populated passing actual controls.
L0's duration-purpose projection passed; counts/diagnostics/energy remain not_run.
L0m's duration-purpose projection remains not_run.

**L0m aggregate-clock shortfall:**
`analytic.aggregate_clock/1:aggregate:d4-bf16-v1` observed 24 generated bodies but
only 21 distinct admitted inputs after its prescribed hardware transformation.
Three repeats remain in the discovery ledger. The required count remains 24; its
result is `INCOMPLETE_OR_UNDER_BUDGET`, not_run. No extra draws, rerun selection,
budget reduction or waiver was used. The four other not_run cells are unused-stipulation
and DRAM-bound-clock, each in both modes. This is an honest partial execution report,
not a blocker to standalone artifact validation or a completed L0m claim.

All five mutants were killed by their designated assertion, with a passing control
on the same inputs: `off_by_one_matrix`, `double_attribution`,
`zero_unmodelled_diagnostic`, `nondeterministic_output` (L0), and
`wrong_bandwidth_field` (L0m). Each has separate aggregate/per-op records with 24
control and 24 fault cases per record per replay. Crashes, schema/hash rejection and
unrelated assertions do not qualify. Those counterexamples are suite discrimination,
not candidate-engine failures or hardware measurements.

## Retained artifacts and reproduction

[Execution artifacts](U3-B-standalone-report-execution/) contain one losslessly compressed
canonical report for each identical pair, exact frozen plan/corpus bytes, the original
combined receipt covering both attempts, invocation journals, generator stdout/stderr,
validator stdout and JUnit receipts. Empty generator stderr files are retained. The
second identical raw report and redundant discovery-object copy are not duplicated.
Gzip uses zero mtime; decompressing reproduces the exact original source bytes:

| Source | Raw bytes | SHA256 of canonical raw source, not gzip |
| --- | ---: | --- |
| `L0-report.json.gz` | 14,830,926 | `181a73bbb3c8cdb2271d14dbb93facc2e1f581c4c78fd11a01426b383dde59ee` |
| `L0m-report.json.gz` | 30,415,819 | `9dac9cd38e68b6faea79d32f591443cd4207268ae2d0eefafa319a6851a7ca65` |

Plans/corpora and engine objects carry their existing identity hashes within the
reports. There is no whole-tree snapshot or broad file manifest. Python 3.12.14,
Hypothesis 6.168.3, pytest 9.1.1 and the exact uv.lock digest are recorded in source.
The stable source has no publication commit, host, wall time or reviewer claim.
Operational receipts reference its raw hash and explicitly record nightly=not_run.
Generator elapsed times (509.80 s L0 / 482.80 s L0m) overlap other local checks;
they are not simulator/G2 benchmarks or evidence for the pending 200-second decision.

Example validation of the retained L0 source from a compatible checkout/environment:

```sh
gzip -dc docs/reviews/U3-B-standalone-report-execution/L0-report.json.gz > /tmp/u3-b-retained-L0-report.json
uv run --no-sync python -m validation.reporting.analytic_report validate --report /tmp/u3-b-retained-L0-report.json --expected-plan docs/reviews/U3-B-standalone-report-execution/L0-plan.json --expected-corpus docs/reviews/U3-B-standalone-report-execution/L0-corpus.json --expected-implementation eab89e07b0c7e41f7a2a0ee236dd1b00f78228c6
```

Use the L0m counterparts for L0m. The caller must obtain these expectations from the
reviewed publication, not trust replacements supplied with an untrusted report. A
later code/contract/suite/dependency change requires a compatible historical checkout
or new execution; unchanged public version strings do not authorize reuse.

## Checks and skips

Commands used this clone's existing locked environment (`uv run --no-sync`); no dependency
or lockfile changed. Final integrated code checkpoint was `eab89e0`.

| Command | Result |
| --- | --- |
| `uv run --no-sync pytest -q validation/reporting/test_analytic_report.py --junitxml=/tmp/u3-b-standalone-new-tests.xml` | 35 passed, 106.24 s, before the final Git-binding discriminator |
| `uv run --no-sync pytest -q validation/reporting/test_analytic_report.py -k git_binding` | 1 passed, 35 deselected, 0.32 s |
| `uv run --no-sync pytest -q validation/L0_invariants validation/L0m_metamorphic validation/mutants tests/unit/test_u2_b_proof.py tests/unit/test_u2_a_loader.py tests/unit/test_u2_a_prepared.py --junitxml=/tmp/u3-b-standalone-regressions.xml` | 106 passed / 29 skipped, 92.02 s |
| `uv run --no-sync ruff check .` | Passed |
| `uv run --no-sync mypy src contract/uarch_contract scripts` | Passed, 68 files |
| `uv run --no-sync mypy --no-explicit-package-bases contract/tests` | Passed, 28 files |
| `uv run --no-sync lint-imports` | Passed, 2 contracts |
| `uv run --no-sync python -m uarch_contract.generate --check` | Fresh |
| `uv run --no-sync python scripts/vendor_rk.py --check` | Strict vendor/support/compatibility currentness passed |
| `uv run --no-sync python -m pytest -q -rs contract/tests --require-vendor --junitxml=/tmp/u3-b-standalone-contract-ci.xml` | 579 passed, 5.26 s |
| `uv run --no-sync pytest -q --junitxml=/tmp/u3-b-standalone-full-suite.xml` | **1,456 passed / 29 skipped**, no errors/failures, 730.410 s in JUnit; includes all 36 new cases |

The 29 existing pytest skips are unchanged: 14 unobservable L0 relations (seven in
both modes), 12 unrepresented/stateless L0m relations (six in both modes), two deferred
unused-stipulation fixtures, and one per-op whole-query clock premise invalidated by
the memory-only embedding. Exact reasons remain in JUnit. The new report deliberately
represents the deferred pair as not_run and adds explicit deferred DRAM-clock cells;
it does not reinterpret historical skipped tests as passed. No full suite is repeated
for the subsequent artifact/prose publication. CI's separate filtered Python/golden/
determinism invocations were covered by the unfiltered full suite rather than repeated.
No native source, third-party patch, perf baseline or silicon prediction files were
present for their conditional checks; no native/image/silicon/fork/nightly run is claimed.

## Remaining dependencies and stop

Coordinator reconciliation and independent review are pending. No SourceRecord,
VerificationRecord, ReviewRecord, ReportContext or ModelCard is produced/attached;
production interpretation/dispatch, loader admission and review eligibility remain
section 5 work requiring separate authorization. Initial L0/L0m card references remain
unchanged. Existing API regressions cover the current production path; missing/rejected
review is not transformed into acceptance by this standalone validator.

A's RoPE additive-schema/protected-patch preparation remains separate. A future v2
verification corpus requires the accepted migration and U0002 human generation/adoption
lifecycle; these model-v1 results cannot be relabeled. Future fork observations require
section 7's explicit DMA control volume, queue/clock premises and actual source interface;
this analytic protocol cannot be reused unchanged to claim that telemetry.

Tool selection, further candidate scouting, instrumentation, fallback, U0005/200-second
limit and G2 verdict remain pending. Runner registration/manual nightly remain pending
with Reza. These local executions provide no designated-host nightly receipt or waiver,
no joint exit, sprint closure or independent-review verdict. Stop here for reconciliation;
no production attachment or later implementation follows automatically.
