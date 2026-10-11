# U0006/report decision supplement

**PROPOSED, UNAPPLIED.** Javid is the acting decision-maker; no Reza approval,
U0006 acceptance, independent review or U-P6 exit is asserted. This supplements
[U0006](U3-U0006-proposal.md) and the [B handoff](U3-B-analytic-preparation-handoff.md),
without changing their results or any runtime, contract or model card.
Base: `89d5d6aff5f9735a219ebc7d63a86fa2fe420e21`; implementation
`42eb1691ed29bf9ba7d129ac8e63a7bce5744e98`. B's recorded full run remains
1,420 passed / 29 skipped. The coordinator reports a separate bounded rerun on
primary `89d5d6a`: 26 passed / 29 skipped in 75.71 s, all five mutants in both modes,
using B's locked interpreter with primary `src:contract` on PYTHONPATH. Neither is
a new execution in this supplement, a coordinator full run or independent review.

Revision against [accepted next-work scope](U3-next-direction-v1-acceptance.md),
`ad23500bc5f360727c660acd71781b4dc530115c`: the conservative direction is endorsed;
this revised payload and implementation scope still await coordinator review and
Javid's concrete decision. This revision replaces internal-draw bookkeeping with
observation at the test-body/engine boundary, and limits the next implementation
proposal to standalone B-owned validation. Historical test receipts above are unchanged.

## 1. Exact proposed ADR text

Proposed human destination:
`docs/decisions/U0006-what-verification-can-and-cannot-establish.md`.
The following context, decision, consequences and exclusions are the proposed text;
no protected ADR is created by this author.

> # U0006 — What verification can and cannot establish
>
> **Status:** proposed; requires Javid's acceptance and human-owned commit.
>
> **Context.** The accepted U2 aggregate/per-op analytic engine exposes resolved
> accounting and roofline predictions, not executed telemetry. B's bounded
> [preparation](../reviews/U3-U0006-proposal.md) and
> [report proposal](../reviews/U3-U0006-report-supplement.md) distinguish those claims.
> [U3-next-direction-v1](../reviews/U3-next-direction-v1-acceptance.md) endorses the
> conservative direction and requests a bounded revision, not wholesale profile acceptance.
>
> **Decision.**
>
> L0/L0m verification is a scoped statement about executed checks of a declared
> model, never silicon validation. Preserve STUB, unknown error and independently
> unverified energy under U0003/U0004. Analytic shape accounting is not executed
> MAC, DMA, queue, placement or history telemetry. Unsupported observations remain
> explicit skips; deferred or unfinished applicable checks remain not-run. Neither
> contributes positive verification. An applicable counterexample fails its
> relation and dominates every enclosing reduction, even if execution is unfinished.
> Partial, empty or skipped-only coverage cannot be summarized as passed.
>
> Freeze relation definitions, premises, domains, modes, case-selection rules and
> budgets before execution. Retain every actual engine invocation, input, result
> and observed counterexample, including executed shrinking attempts and mutant
> controls, with exact implementation, assumptions, suite and input/result bindings.
> Separate
> engine checks on fixed prepared work, producer-path checks and mutant results.
> A mutant rejection demonstrates test discrimination, not an engine failure or
> hardware accuracy. Hash identity, an actual test run and independent accepted
> review are distinct obligations. Reusing a version string cannot authorize a
> report from another implementation. A report must retain omissions and failures;
> review cannot erase them or expand their scope.
>
> Freeze concrete admitted inputs before two qualifying replays. Preserve discovery
> failures even if a replay passes. Observe generation and engine calls through
> supported public APIs and an explicit recording wrapper. Do not retain a second
> ledger of framework-internal rejected draws that never invoke the engine; report
> unavailable internal counts as unavailable, never as zero. Record all actual
> calls even when a framework cannot label which belong to shrinking. Example
> budgets, observed generation, retained cases and actual executions are distinct.
>
> Reduce failed applicable relations or failed required mutant discrimination to
> failed; otherwise unfinished, skipped, empty or under-budget coverage reduces to
> not_run; only nonempty complete passing coverage reduces to passed. Rich relation
> states remain in canonical source bytes. The three VerificationRecord outcomes
> can carry conservative reductions only after separately authorized integration.
>
> **Consequences.** The proposed first implementation is standalone analytic report
> generation and validation under B-owned validation paths. Bind exact implementation,
> assumptions, suite, concrete inputs and results; refuse missing/tampered cases and
> changed implementations even with unchanged version strings. Git retains source
> history; retain only report-relevant artifacts and existing content identities.
> Stable report bytes exclude operational timing/host/nightly receipts, which refer
> to their report hash. No circular dependency on a later publication commit.
>
> **Does not do.** This decision supplies no measurement authority and accepts no
> test run or review. Production provenance dispatch, A loader changes, card
> attachment and evidence eligibility are deferred; initial L0/L0m references stay
> null. It does not accept a fork, change U0003/U0004, alter U2 historical evidence,
> waive U0002, discharge nightly/U-P6 gates, authorize private Hypothesis hooks or
> modify protected carriers. Concrete profile review and implementation authorization
> remain separate from this proposal's publication.

## 2. Canonical source profile (exact proposed fields)

Proposed raw format: `uarch-analytic-verification-source/1`. This is a **new source
interpretation**, not an already accepted raw proof format. No public carrier
field is added. All fields below are required, unknown fields/duplicate keys are
refused; nullable fields use explicit null. Hashes are `sha256:<64 lowercase hex>`;
counts are nonnegative integers (booleans forbidden); numbers are finite. Serialize
using existing `canonical_json(...).encode('utf-8')`, without a trailing newline.
The raw blob has **no self-hash field**; `SourceRecord.raw_blob_sha256` hashes its
exact bytes. Arrays retain meaningful order; declared sets are sorted unique.

| Source field | Exact content / meaning |
| --- | --- |
| `format` | Literal above |
| `execution_kind` | `actual_suite_run` or `illustration`; only the former is eligible for an executed-run claim |
| `input_kind` | `synthetic_fixture` for this bounded profile; does not mean the reported execution or reviewer was simulated |
| `engine`, `model` | Full accepted EngineIdentity and ModelIdentity; `model == engine.model` |
| `implementation_git_commit` | Full pre-execution clean checkout commit; engine, protocol, preparation and contract code must match that checkout, not just core.py's hash |
| `assumptions` | Full accepted AssumptionSet with validated assumptions_hash and exact model/algorithm equality |
| `suite` | `{id, version, git_commit, entrypoint, plan_hash}`; commit is the clean committed suite implementation used, entrypoint names its runner (an explicitly prospective name only for illustration), plan_hash is content_hash(plan) |
| `toolchain` | `{python_version, hypothesis_version, pytest_version, uv_lock_sha256}`; exact versions/lock bytes, no environment path |
| `discovery_plan` | Original plan committed before discovery; same fields as plan, corpus_hash=null; its digest is content_hash(discovery_plan). |
| `plan` | `{profile_id, profile_version, rung, purposes, modes, cells, selection}`; purposes is a sorted subset of counts/duration/diagnostics/energy; modes is exactly `["aggregate","per_op"]`; rung is L0 or L0m |
| `execution` | `{state, stop_reason, ledger_count}`; ledger_count sums all three ledger lengths; state is `complete` or `interrupted`; stop_reason null only for complete execution |
| `corpus` | `{entries, discovery_case_ids}`; entries are ordered `{cell_id, ordinal, discovery_case_id, input_hashes}` for each distinct admitted input tuple, including counterexamples and executed shrink inputs; discovery_case_ids lists every retained discovery case (including repeated inputs). No plan/report hash in this object. |
| `cases` | `{discovery, candidate, mutant}`: three ordered ledgers using the case fields below; no success-only sampling. The discovery ledger is frozen; each qualifying report records one candidate replay. |
| `relations` | Exactly one result for every plan cell, including skips/not-run cells |
| `mutants` | Separately labeled discrimination records; never mixed into candidate relation outcomes |
| `objects` | Sorted unique `{hash, kind, value}` objects needed by these cases: hardware, request, bundle, job, result or diagnostic bytes. For bytes, value is base64 and hash is byte SHA256; for accepted carriers use their existing identity rules. No unrelated repository inventory. |
| `reduction` | `{coverage, outcome, purpose_outcomes}`; recomputed by §3, never trusted as an assertion; purpose_outcomes maps every plan purpose to passed/failed/not_run |

Each `plan.cells[]` is
`{cell_id, relation_id, purpose, modes, path, domain, premises, budget, required_mutants}`.
`cell_id = relation_id + ':' + '+'.join(modes) + ':' + domain.id`; IDs are unique.
`modes` is one mode except the cross-mode comparison, which lists both in the order
above. `path` is `fixed_prepared` or `standalone_producer`. `domain` is
`{id, definition, input_fixture_hashes, scope_dimensions}`. Definition has exactly
`{fixed, ranges, transformation, tolerance}`: fixed maps input JSON pointers to
exact values; ranges lists `{pointer, minimum, maximum}` with inclusive integer
bounds; transformation is `{id, arguments}` with a versioned suite-defined ID and
canonical argument map; tolerance is `{relative, absolute, unit}`, explicitly null
where no numeric comparison applies. Scope_dimensions maps required EvidenceScopeCase
field names to prospective `{role, json_pointer}` selectors, where role is a
versioned suite-defined input/result role and json_pointer addresses that carrier.
These selectors contain no hashes of cases not yet generated. At execution, resolve
them to existing ArtifactPointers into retained objects and derive concrete scopes
from captures, not a Cartesian product; missing family/registry or another required
binding prevents a carrier projection. Do not invent a family. `premises[]` is
`{id, predicate, observation_selectors}`; predicate is a versioned checker identifier
and each selector uses the same prospective role/pointer form. `budget` is
`{max_examples, required_valid_examples, max_engine_invocations}`; this profile proposes
24, 24, 240 respectively for generated cells. The third field caps actual engine
invocations per cell per ledger, including mutant controls; a literal control uses
1, 1 and its prospectively declared number of calls (not necessarily one).
Budget exhaustion before required coverage is not-run, never an automatic pass.
The wrapper refuses calls beyond the cap and stops that phase with a dedicated
runner budget outcome; it must not misclassify this as an assertion counterexample.
`required_mutants` names the applicable faults below, or an empty array.

`plan.selection` is `{policy, database, derandomize, seed, phases, deadline_ms,
retain, corpus_hash}`. Proposed policy is `hypothesis-freeze-replay/1`, database
null, derandomize true, seed null, deadline_ms null, phases exactly
`["generate","shrink"]`, retain `all_engine_calls_and_counterexamples`, and
corpus_hash null in the pre-discovery plan. Freeze it to content_hash(corpus) before the
qualifying replays; this sole permitted completion changes plan_hash, with the
pre-discovery plan retained as `discovery_plan` at the top level. All other plan
fields must remain identical. Phase changes require a new prospective plan/run.

Each ledger case is `{case_id, cell_id, ordinal, stage, origin_case_id, status,
reason, inputs, results, calls, premise_results, assertion_id, failure_fingerprint}`.
Case_id is ledger name plus cell_id plus its zero-based ledger ordinal; stage is
`discovery` or `replay`. Origin_case_id is null during discovery, otherwise the
corpus entry's discovery_case_id. Do not invent parent-draw IDs or shrink-phase
labels from private framework state. Status is pass/fail/skip/not_run. Inputs/results
are ordered object hashes (pairs retain low/high order). Calls are ordered
`{job_hash, result_hash, diagnostic_hash, state}` records, state completed/error/
not_run; nullable hashes resolve only to retained actual outputs. Results equal
ordered non-null result hashes. Persist the job before invocation and the output
before running assertions; retain exceptions/partial output, not just successful
results. An interrupted in-flight call is an error with a stable interruption reason,
never a fabricated result. Do not call validation failures an unexecuted engine result.
Premise results are `{id, state, reason, observation_pointers}`, state true/false/
unobservable and pointers resolve to retained objects (empty when unavailable).
Failure_fingerprint is null or `{assertion_id, observed}` with canonical values.
Reasons are stable catalogue codes, null only for pass; raw traceback/host context
belongs to the separate operational receipt. Every observed counterexample is
retained before framework shrinking/retry, even if it precedes an engine call.

Keep discovery cases whenever the body invokes the engine or observes a counterexample;
retain every such invocation, including repeated inputs, executed shrinking attempts
and failure reproduction. Do not store a case for an internal rejected draw that
never reaches that boundary. A body that rejects before any engine call increments
only the observed-body counter; it contributes no valid example. No dependency on
Hypothesis private internals or scraping verbose/statistics output is permitted.
The wrapper surrounds **all** calls, including repeat checks and mutant controls.

Each `relations[]` is `{cell_id, applicability, reason, status, premise_results,
actual, case_ids}`. Applicability is applicable/inapplicable/unobservable;
status is pass/fail/skip/not_run. `actual` has exactly:

| Field | Observation and counting rule |
| --- | --- |
| `observed_body_entries` | Discovery test-body entries after public strategy argument delivery, counted by our wrapper; includes repeats and body-level rejects, not framework-internal generation. Zero only if none observed. |
| `internal_draws`, `internal_rejections`, `executed_shrink_calls` | Null in this first profile: not observed through the selected public API. Null means unavailable, not zero. Executed shrink calls are still retained in discovery; they are not separately classified. |
| `valid_examples` | Distinct admitted corpus entries whose required candidate replay calls/assertions completed (passing or failing). Duplicate inputs, repeat calls and mutant calls do not inflate it. This is not Hypothesis's internal valid-example count. |
| `engine_evaluations` | `{discovery, candidate, mutant}`: counts all calls other than not_run in each cell's three ledgers; mutant count includes controls. Discovery results can fail the relation regardless of replay results. |

Observed_body_entries is an explicitly measured scalar, not reconstructible from
the retained-call subset; it must be at least its retained discovery-case count.
All other available counts are recomputed from the ledgers/corpus. Unknown counts
cannot satisfy coverage budgets. Full validity requires exact IDs, order, object
closure and plan/corpus membership, including unexecuted cells. The versioned
profile registry fixes its complete relation list; deleting a skipped/deferred cell
cannot create a new successful report under the same profile ID/version.

**Initial relation catalogue** (version suffix `/1` is mandatory):

| Rung | relation_id prefix | Purpose / path / premise |
| --- | --- | --- |
| L0 | `analytic.fixed_counts`, `analytic.count_rollup` | counts / fixed_prepared / independent d4 BF16 key; accepted repeat conventions |
| L0 | `analytic.attribution_sum`, `analytic.repeat_bytes`, `analytic.saved_replay`, `analytic.input_refusal` | duration / fixed_prepared / same authenticated job; sum tolerance 1e-9 relative, zero absolute for nonzero fixture durations; no producer on replay |
| L0 | `analytic.null_diagnostics` | diagnostics / fixed_prepared / accepted unmodeled fields must be null |
| L0m | `analytic.dram_monotone`, `analytic.dram_memory_response` | duration / fixed_prepared / identical work; latter requires all terms memory-bound after ×2 bandwidth and duration ÷2 at 1e-9 relative |
| L0m | `analytic.aggregate_clock` | duration / fixed_prepared / aggregate only, exact resolved clock/peak ratio k=2–4 and compute-bound after scaling |
| L0m | `analytic.mode_order` | duration / fixed_prepared / both modes, equal counts/per-op work, per_op no faster |
| L0m | `producer.decode_batch`, `producer.decode_context` | duration / standalone_producer / BF16,tp1,fixed model/fusion/hardware; explicit new graph/hash per query |

For all other U-P6 obligations use stable IDs `L0.<name>/1` for
executed_mac_conservation, dma_conservation, window_utilisation, little_law,
causality, sram_placement, energy_conservation; and `L0m.<name>/1` for
noc_sram_bandwidth, core_permutation, idle_core, unused_stipulation,
latency_monotonicity, dma_outstanding, cold_steady, per_op_exact_clock,
dram_bound_clock. Assign purpose counts to the first two L0 names, diagnostics to
window/queue/causality/placement, energy to energy, duration to all L0m names.
Retain the published reasons/domains; do not turn the 29 historical pytest skips
into successful checks. Future source reports split the deferred unused-stipulation
case into not_run and unobservable cases into skip; the original receipt is immutable.
DRAM-bound clock is also explicitly not_run, not a newly claimed executed skip.

## 3. Applicability and reduction

A false/unobservable premise gives **skip**, with recorded reason and observation
(or explicit absence), only when admission actually establishes inapplicability.
An applicable but deferred, unstarted, interrupted, errored or under-budget cell
is **not_run**; unexpected infrastructure errors are not fabricated counterexamples.
An assertion violation on admitted inputs in either discovery or candidate replay
is **fail** (a later passing replay cannot erase it); satisfied assertions over
all required valid examples are **pass**. Internal missing/tampered/duplicate case
or object is an invalid report: refuse parsing/attachment, not a benign not_run.
A faithfully declared interruption retains ledger completeness and unexecuted cells.

Reduce cells for each purpose, and then the whole rung, in this order:

1. Any applicable fail, surviving required mutant or failed mutant control → `failed`,
   even with skips, exhausted budgets or interruption. A mutant qualification failure
   is labeled suite-power failure, not invented candidate telemetry.
2. Otherwise any not_run, incomplete execution or missing required mutant execution
   → `not_run`.
3. Otherwise any skip, or zero applicable cells → `not_run`.
4. Otherwise nonempty all-pass cells and all required discrimination checks completed
   successfully → `passed`. Purpose projections also include every mutant required
   by their planned cells.

`coverage=complete` only if execution completed and every declared cell was applicable
and reached its required valid-example count (or produced a counterexample), with
all required mutants completed. Otherwise coverage is `none` if no candidate check
was evaluated, else `partial`. Coverage and outcome are separate: partial may fail,
never pass. Skipped-only is none/not_run; finished passes plus skips is partial/not_run;
an unfinished run with a counterexample is partial/failed. Purpose projections
use the **prospectively frozen** cells of that purpose, not a post-run favorable
subset. The whole-rung reduction preserves all obligations; a passed purpose is
not a passed whole rung. This conservative proposal intentionally leaves current
partial U-P6 coverage without a blanket positive verification claim.

Each mutant record is `{mutant_id, implementation_git_commit, target_cell_id,
mode, status, control_case_ids, mutant_case_ids, rejection_assertion_id, reason}`.
Status is killed/survived/control_failed/not_run. Killed requires a passing control
on exactly the same inputs and the named target assertion's rejection, not a
crash, wrong schema, stale hash or unrelated assertion. Control/fault calls are
retained in cases.mutant; both ID lists refer to that
ledger, whose inputs/results refer to objects. They never count toward candidate
actual.valid_examples. No case may be silently shared between ledgers.
The five identifiers remain off_by_one_matrix, double_attribution,
zero_unmodelled_diagnostic, nondeterministic_output and wrong_bandwidth_field.

## 4. Reproducibility and binding

Hypothesis derandomization is reproducible only for pinned strategy/test code,
Python/Hypothesis version, settings and collection identity; a seed alone is not a
case specification. The published 24-example setting is a budget, not a retained
case corpus. Do not reconstruct lost original cases from its JUnit summary.
Proposed runner freezes the ordered generated concrete corpus, validates all its
identities and hashes it **before** the report-qualifying replay pair. Retain all
observed engine calls and counterexamples during discovery,
including executed shrinking and reproduction, without labeling private phases.
Use public `given`, `settings`, `Phase` and strategies plus the suite's own boundary
wrapper; do not use Hypothesis observability/internal callbacks. The property body
receives concrete strategy values before the wrapper prepares/calls the engine.
Prefer constructive strategies; a framework rejection before body entry is unknown.
Public settings keep database=None, derandomize=True, deadline=None and generate/
shrink phases. `max_examples=24` is a search target, not a guarantee of 24 distinct
retained cases. Freeze first-occurrence-ordered distinct admitted input tuples into
the corpus; retain every repeated invocation separately. An executed shrink input
may enter the corpus, but does not erase its earlier counterexample. If fewer than
24 distinct admitted cases finish the replay, retain under-budget/not_run (or failed
if a counterexample exists). No extra successes are generated to hide a failure.
Run that same frozen corpus twice with producers disabled for fixed-input cells; for producer cells
retain intents, emitted bundles and producer identity and compare those too.
Identical plans/corpora/implementations must produce identical canonical raw report
bytes (both reports embed the same frozen discovery ledger). Failure/shrink attempts
remain in the immutable discovery ledger; replay
cannot erase them. A fresh discovery with changed corpus is a different report.

Plan/corpus commitments precede outcome observation for the qualifying pair; any
failure found during discovery is recorded, never excluded to select passing cases.
The observed-call records and corpus are report artifacts, not a manual source
revision system. No ledger of never-invoked internal draws is required. Retain all
case objects for this bounded scope, not a sample.
Within objects verify hardware spec_hash, intent/request identities, bundle and point
hashes, job/result identities and original joins; rehashing a substituted graph or
result cannot excuse an inconsistent binding. Compare full EngineIdentity/model,
assumptions and declared protocol/accounting, plus the exact implementation checkout.
Current anchors are analytic `resolved-ops/1`, `uarch-engine/1`, physical-resolved `1`,
implementation `sha256:fa3938f8c009c7b80700d35feba7504e4b4da06e628d2e387480c358963974ea`,
assumptions `sha256:255afd1ceb9c02a4909464c41e98e16085485a8e500090a8e2d98dc2ee56a896`.
Different implementation bytes, suite code or assumptions refuse reuse even if
version strings match; a later documentation-only publication commit is not engine
identity. Record the immutable pre-run source commit, not that eventual publication
commit. No report hash includes its enclosing publication commit, review hash or card.

Operational receipts separately reference the final raw report hash and record
host, elapsed time, invocation/session, stdout/stderr, interruption and nightly run
URL/status. These are not stable report fields and cannot grant missing execution
or review. Nightly execution requires its own real designated-host receipt; byte
identity on WSL does not discharge it. No timestamp/path/host-duration normalization
of engine results is allowed to manufacture deterministic results.

## 5. Mapping to actual APIs; no invented eligibility

| Existing API | Proposed use and current limitation |
| --- | --- |
| `SourceRecord` in `contract/uarch_contract/evidence.py` | `kind=contract_test`, `independence_from_candidate=false`, reference_identity=suite.id, reference_version=`suite.version + "@" + suite.git_commit`, limitation explicitly states synthetic BF16 inputs/self-consistency/no silicon/energy evidence; raw_blob_sha256 binds canonical source bytes, source_hash uses the existing identity exclusion. An illustrative/mock run uses kind=synthetic_fixture and cannot be attached as actual execution. |
| `VerificationRecord` | One per (rung,purpose,exact model), with nonempty exact EvidenceScopeCase list and source_hash; outcome is that purpose's §3 reduction. Full relation/mode/partial/mutant states stay in raw bytes. Empty/unrepresentable scope produces no record, not an invented scope. No omnibus counts+diagnostics+duration record mislabeled as duration. |
| `ReviewRecord` / `review_subject_hash` | Reviewer examines the immutable source and its complete retained cases. Subject hash excludes the verification_hash and review_hash, as implemented; after actual review, bind review_hash then verification_hash. Review must match that subject, be independent=true and decision=accepted for positive eligibility. Pending/rejected reviews and negative outcomes remain visible, never synthesized as accepted. |
| `ReportContext` | After authorized integration, index all relevant VerificationRecord hashes (including failed/not_run) in verification_hashes; retain limitations and exact assumptions/model/request. They are not EvidenceRecord measurement entries in evidence_index. Mixed modes and richer scope are checked from the source, since EvidenceScopeCase has no analytic-mode field. |
| `ModelCard` | Initial profile leaves verification.L0/L0m null: each scalar hash cannot faithfully summarize several purpose records and partial whole-rung coverage. Show scoped reports through context only after implementing the interpreter; do not choose a favorable purpose hash or a raw blob for the card. Keep badge=stub, validated_error_band=null, energy_verification=null. A future multi-purpose card representation is a separate human decision, not an implicit field addition here. |

Actual closure is `SourceRecord → raw bytes`, `VerificationRecord → source/review`,
then context/card artifact closure through `load_verified_report_inputs` in
`src/rkuarch/table/artifacts.py`. Existing closure resolves/hash-checks bytes and
`verify_review` checks subject membership; **it does not by itself require an
accepted independent decision or interpret this proposed raw format**.
`src/rkuarch/provenance/applicability.py::_accepted_review` additionally checks
independent/accepted. Existing `proof.py::interpret_verification` understands only
the bounded `u2-proof-bundle/2` profile via `proof_raw.py`, independent expected-source
links and synthetic literal eligibility; it rejects this proposed format and our
honest independence=false. Do not set that flag true or relax the old interpreter.

**Deferred integration, outside the first implementation scope:** a distinct analytic
profile interpreter/dispatch and coordinated A loader/card admission would eventually
be needed. The first standalone generator/validator does not create SourceRecord,
VerificationRecord, ReviewRecord, ReportContext or ModelCard artifacts, decide evidence
eligibility, or modify either production interpreter. Standalone self-consistency
reports never feed L3/L4 or measured-error eligibility. Existing carriers can transport this meaning; they do not supply its
semantics automatically. No protected carrier change is selected. The sole protected
text proposal is §1 for eventual human-authored
`docs/decisions/U0006-what-verification-can-and-cannot-establish.md`. New parser/profile
semantics need human agreement before implementation; edits to bound support code
still require U0002 human generation/adoption. No change is applied in this task.

## 6. Illustration and bounded acceptance plan

The [complete skipped-only illustration](U3-U0006-report-example.json) includes every
required source field and no placeholder hashes or omitted members. The file is
readable JSON transport; canonical_json produces the proposed stable raw bytes
without indentation or a trailing newline. It is an
`illustration`, **not executed evidence**, and uses a deliberately small diagnostic
profile with exactly the little-law cell in each mode. Both cells are unobservable,
all actual engine-call counts are zero, internal counts are unavailable (null), the
corpus is empty and reduction is none/not_run. It is not the full U-P6 profile and
cannot claim rung completion. No queue telemetry or accepted review is invented.
The profile ID is explicitly illustrative and must be refused in actual-run mode.

Its engine/assumptions and lock identities are taken from the existing source; the
suite commit is this revision's pre-work base and its proposed entrypoint does not
exist there. That is permitted **only** for illustration, never actual_suite_run.
The validator's actual-run path must verify the entrypoint exists at the declared
clean suite commit. The example's omission of engine jobs/results follows from zero
invocations, not permission to omit any executed case. Full executed-case retention
is covered by the tests-first plan below; no new analytic execution is claimed here.

Before runtime implementation, write bounded discriminating tests with actual run
controls and explicitly mock reviews only in test fixtures (never accepted reviews
of this proposal). Suggested corpus: two fixed points × both modes, two deterministic
hardware variants, plus one pair per metamorphic relation; small fixtures below are
not substitutes for the declared 24-valid-example production plan.

| Test / attack | Exact expected result |
| --- | --- |
| Two replay runs with same plan/corpus/source checkout | Full stable raw bytes and hash identical; different operational timestamps/paths remain outside those bytes. Changed engine output bytes fail determinism, never normalized away. |
| Change implementation, preserve version strings | Refuse engine/model/source-checkout mismatch; even a rehashed report requires a new execution and review. |
| Tamper one case/result; omit one planned case; duplicate ID; rehash subset | Refuse byte/identity/closure or exact plan-ledger mismatch. Test intact valid control first. |
| Inject applicable attribution failure | Cell fail and purpose/whole-rung failed, including when later execution is interrupted; mutant killed status cannot erase candidate failure. |
| Passes plus skips, or one applicable deferred check | Partial/not_run; zero promoted rung/card hashes. Completed narrower purpose may retain scoped passed without changing whole-rung outcome. |
| Skipped-only or empty applicable set | none/not_run, never all([])=passed; absent concrete scope yields no VerificationRecord. |
| Stop before budget; max_examples exceeds distinct observed cases | not_run unless a failure exists; no substitution of max_examples for actuals. Duplicate/reproduction calls do not inflate valid_examples. |
| Framework rejects before body/engine; body rejects before engine | No internal-draw ledger; internal counts null, body count only where observed. Zero engine calls only if actually none. |
| Counterexample shrinks, then replay passes | Preserve all invoked inputs/results and the original failure; discovery failure still dominates. No private phase labels required. |
| Missing, pending, rejected, non-independent or wrong-subject review | Deferred carrier-integration test, not first standalone scope. Standalone reports cannot assert accepted review or eligibility and never emit card references. Existing review rules remain unchanged. |
| Surviving mutant or invalid control | Suite-power failure; unmatched crash/identity/schema exception does not count as killed. Candidate relations retain their own outcomes. |
| Raw profile dispatched to current U2 proof interpreter | Unsupported remains expected; no production dispatcher change in first scope. |

No test in this table has been implemented or executed by this prose-only task.

### Exact first implementation plan (pending coordinator review)

1. Add tests first under proposed `validation/reporting/test_analytic_report.py` for
   the table above's standalone cases. Reuse current accepted synthetic fixtures,
   checks, strategies and five named mutants; no golden/schema changes. Include an
   actual passing fixed-input control in each mode, producer-path separation and a
   spy that proves every engine call (including errors, repeats, shrink attempts and
   mutant controls) is retained. The smallest literal plan uses one distinct case
   per mode; generated profiles keep the 24-example target/coverage rule above.
2. Add only `validation/reporting/analytic_report.py` (and a package initializer if
   needed): local proposal-shape validation, canonicalization/reduction, recording
   wrapper, discovery/corpus freeze and deterministic replay. Reuse current carrier
   validators and identity functions. No contract schema, production CLI or dependency
   changes.
   Proposed commands: `python -m validation.reporting.analytic_report generate
   --profile <committed-profile-id> --output <directory>` and `... validate
   --report <path> --expected-plan <path> --expected-corpus <path>
   --expected-implementation <commit>`. Generate emits the frozen corpus and both
   raw replay reports plus separate operational receipts. Validate compares caller-
   supplied expectations; a report's self-declared identities cannot authorize reuse.
3. Freeze the full L0/L0m catalogue, domains, omissions, mutant obligations and both
   modes from §2 and the published preparation under versioned profile IDs. The
   illustrative profile is never a production default. Preserve fixed prepared-work
   replay without invoking the producer; the distinct producer path retains intents,
   emitted bundles and producer identities on every execution. Local work files
   retain only report objects/receipts; Git commits the suite, not checkpoint copies.
4. Validate closure, original versus replay input joins, exact planned coverage,
   every corpus entry's expected replay and counted calls. Retained discovery cases
   cannot be dropped by rehashing a smaller corpus against a caller-pinned expectation.
   Abrupt termination may leave an incomplete local record: refuse a missing/corrupt
   report, never manufacture complete coverage; orderly interruption yields not_run
   unless an applicable counterexample already exists. Compare complete stable bytes
   across the two replays; use fresh identically initialized mutant wrappers in each
   replay and retain control/fault calls separately. Operational receipts retain
   each attempt separately.
5. Run the new bounded tests, existing L0/L0m controls/mutants and applicable API
   regressions; then `ruff check .`, `mypy src contract/uarch_contract scripts`,
   `mypy --no-explicit-package-bases contract/tests`, `lint-imports` and a full
   suite at the meaningful integrated **code** checkpoint (all via the locked uv
   environment). Report actual totals and
   skips. Production dispatch, A loader edits, model-card attachment and evidence
   eligibility require a later separately authorized task. No fork or nightly gate
   is discharged by this future local implementation.

This plan is a reviewable scope, not permission to implement it now.

## 7. Future DMA, queue and clock premises; reconciliation with A

For each declared DMA direction/control boundary over `[t0,t1)`, in integer payload
bytes, require `inflight(t0) + accepted = completed + cancelled + inflight(t1)`.
Rejected/retried requests are not accepted twice; fragments have unique IDs and
partial completion is counted once. Bus transaction bytes, padding and logical
payload bytes are separate channels. A resident-buffer balance additionally needs
`resident(t1) = resident(t0) + loads + produced - evicted - invalidated`, with
explicit overwrite/alias ownership rules. Compute reads do not consume occupancy;
reuse, fusion and generated outputs invalidate “bytes in = consumed + written back.”
A must expose request/fragment IDs, direction, byte kind/count, lifecycle times,
initial/final inventories and the reuse/residency policy before those checks apply.

Queue identity must define admission, departure and whether service is inside the
queue. Q0/Q1 and DMA endpoint inventories mean immediately before t0/t1; A/D
count events in `[t0,t1)`, and D includes every exit, including cancellation. With
half-open membership, `Q1=Q0+A-D` and
`integral(Q(t),t0,t1) = sum_i length([arrival_i,departure_i) intersect [t0,t1))`
over **all** items present in the window, including censored endpoints. For a drained
cohort with Q0=Q1=0, N>0, W=t1-t0>0: L=integral/W, lambda=N/W,
T=sum(residence)/N and `abs(L-lambda*T)/max(L,lambda*T) <= .01` when the
denominator is positive. Zero-residence flow requires both terms exactly zero and
skips the undefined relative ratio. Empty flow skips the relative test; separately require zero area for the drained
empty queue. For a non-drained finite window, require the exact overlap identity
and conservation first; never use completed-only residence averages to assert
steady-state Little's law. A stationary claim needs a prospectively chosen warmup,
window, stationarity evidence and explicit censoring correction. Missing observations
skip; contradictory observed conservation fails. No such data exists in U-C0.

Clock premises: fixed authenticated work/mapping/precision/counts; integer resolved
core frequencies scale exactly by k, all consumed compute peaks scale by k, memory
bandwidth and non-core domains unchanged, no latency/history change. Aggregate
compute-dominated demand must remain dominant **after** scaling; then T'=T/k.
For per_op the same must hold for every nonzero term, so the existing memory-only
embedding violates the premise. If every priced term remains memory-dominated,
T'=T, not the ambiguous “changes by less than k.” Future queue/timing engines need
separate premises about contention, synchronization and clock crossings; the
analytic law is not imposed unmodified. A must expose resolved domain clocks,
rate/config bindings and actual dependency/timing observations before such claims.

A's published [source findings and interface questions](U3-U0005-proposal.md), §§4/6,
already distinguish declared shapes from observable executed counts and identify
Dummy fallback, fused/KV/precision and attribution gaps. The coordinator's local
`U3-preparation-v1/lane-A-planning-followup.txt` requests source-only operator/statistics/
licence feasibility, with blocked routes explicitly stopped. A's subsequent [source-only supplement](U3-A-source-feasibility-supplement.md),
commit `aa537279260f94828b92aa6e42c9ae85b14f856c`, was fetched, inspected and merged.
It reports stopped ONNXim paths, a blocked supplied PyTorchSim route and no established
complete feasible route; native instruction/cycle counts do not supply per-op MAC
observations, and mixed logs do not establish complete stable statistics. Its proposed
instrumentation is unapplied and cannot repair semantic gaps. These are A's source
findings, not a B simulator run or independent review.

Coordinator reconciliation must settle A §3 alongside this §7: RoPE's absence from
U2 needs explicit human semantic disposition before any translation choice; preserve
accepted RMS semantics. Resolve native field names/units and complete operator
correspondence; padding versus useful work; DMA/queue inventories and time boundaries;
critical-path versus busy-time attribution; refused capabilities and exact fork
identity/image/config/point/rank bindings. Point-select diagnostic coverage must not
be presented as the complete decode/prefill grid or full-model execution. B's future
checks must reject missing, duplicated, swapped, skipped or padded observed work
against the agreed source correspondence. Feasibility, instrumentation permission,
licence closure and host readiness remain separate pending dependencies.
No queue/trace contract is invented here, and the fork cannot use the current
analytic-only protocol unchanged. Analytic source/report work depends on none of
those unavailable fork observations.

## Historical checks and this revision

At the prior supplement commit, executed locally: `uv run pytest -q tests/unit/test_prompt_sync.py
 tests/unit/test_u2_b_proof.py::test_verification_literal_positive_and_real_mode_unsupported
 tests/unit/test_u2_b_proof.py::test_verification_failed_not_run_preserved
 tests/unit/test_u2_b_proof.py::test_reference_must_have_independent_accepted_review
 tests/unit/test_u2_a_loader.py::test_raw_source_blob_closure_and_tampering`
(as one shell command): **9 passed in 3.40 s**. The illustrative JSON parses,
local Markdown links resolve, and `git diff --check` passes. These are existing API
regressions and document checks, not execution of the proposed acceptance plan.
No full suite, new analytic run, fork, model-card attachment, or nightly rerun for
this prose-only change; no static-code check is presented as new runtime evidence.

This bounded revision: `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py`
completed **4 passed in 0.14 s**. Document-only assertions checked the complete
example's fields, accepted EngineIdentity/AssumptionSet, implementation/lock and
plan/corpus hashes, both-mode skipped coverage, null unavailable counts, and canonical
JSON round-trip; local links and `git diff --check` pass. Canonical round-trip is
not two executed replay runs. No new report validator/runner or acceptance tests were
implemented, and no engine invocation, full suite or static-code suite was rerun for
this Markdown/illustrative-JSON change. Earlier full/bounded results remain historical.

## 8. Exact decisions and implementation path

The conservative direction is already endorsed. These concrete decisions remain:

1. Accept the exact §1 ADR wording; Javid's acceptance and human ADR commit are
   separate from this proposal commit. U0003/U0004 remain settled.
2. Approve the revised §2/4 source fields and §6 complete illustration: retained
   engine calls/counterexamples, frozen distinct admitted corpus, observed counts
   versus null internal counts, supported APIs and unchanged failure-first reductions.
3. After coordinator review, authorize only §6's standalone B-owned implementation/
   tests. Keep production dispatch, A loader work, carrier/card attachment and evidence
   eligibility deferred, with initial L0/L0m card hashes null. §5's carrier mapping and
   §7's fork telemetry questions remain future proposals, not additional scope here.

After coordinator review and explicit authorization, B writes §6's tests and standalone
validation generator; production integration and review/eligibility remain deferred.
Any bound-source change still follows U0002 human generation/adoption. Publishing this
proposal authorizes none of that implementation. Per the accepted direction, Javid now
reports container packages installed and rootless Podman 4.3.1/mapping checks passed;
image execution, resource reservation, runner account/readiness and successful manual
nightly remain unverified. No server/schedule change, host waiver, fork run, independent-
review verdict, tag or sprint closure follows.
