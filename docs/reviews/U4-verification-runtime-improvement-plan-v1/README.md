# Test, verification and CI runtime improvement — queued after component Stage 3

Javid requested this follow-up on 2026-10-17, recalling the Python CI runtime discussion
before U3 closeout. This records a plan; it starts no profiling run, changes no tests or
workflow, and does not interrupt or alter the current independent review.

Start after the current component Stage 3 verdict and evidence are preserved. It need not
wait for U4 tagging. Use one substantial worker assignment led by B for test/verification/CI
infrastructure, with A consulted only for identified production-code hotspots or ownership
joins. Reconcile once at a meaningful milestone rather than rerunning overlapping suites at
many small handoffs. The coordinator retains scope and evidence reconciliation; the worker
does not substitute for independent review.

## Existing state and measured evidence

- Documentation-only classification already exists in `.github/ci_scope.py` and `ci.yml`.
  It shortens some jobs, but the contract job still executes on every commit. Keep executable
  scripts/tests under docs from being misclassified as harmless prose.
- The Python job's ordinary pytest selection and the dedicated contract job overlap in
  contract tests. The latter adds `--require-vendor` and strict currentness. Determine exact
  node/environment/argument overlap before proposing deduplication; these are not proven
  interchangeable jobs.
- No default per-test duration reporting is present in the current Python CI command.
- The completed local K2 campaign used 11 workers: 798 calls in 259.99 seconds, including
  79.77 seconds of shared resolution and 173.87 seconds of case processing. Saved-output
  replay took another 194.25 seconds and made zero new native calls. See
  [actual receipts](../U4-K2-completed-first-use-v2/README.md).
- The current F6 review script runs broad directory selections in four states and buffers
  its report until completion. At inspection, two runs plus setup took about 17m40s and
  the third had run about 9 minutes. These are incomplete observations, not a finalized
  benchmark. A/B guard sweeps are additional review work, not ordinary CI by default.

## Work sequence

1. **Map cost and frequency.** Inventory ordinary developer tests, Python/contract CI,
   static/schema/currentness checks, native local checks, first-use/replay campaigns and
   review mutation sweeps. Record purpose, owner, cadence, exact selected nodes, inputs,
   setup/validation/process costs and known duplication. Distinguish elapsed critical-path
   time from summed CPU time. Use current same-subject receipts where adequate.
2. **Add observability first.** Per-test setup/call/teardown durations and machine-readable
   summaries; stage starts/completions and elapsed time; separate streamed subprocess logs;
   useful mutation progress (completed/planned cases), failure identity and restoration
   status. Flush progress without allowing incomplete progress to masquerade as a passing
   receipt. Failed runs retain logs. Apply this prospectively, never rewrite reviewer history.
3. **Profile the largest recurring costs.** Profile selected slow groups with existing
   tools; separate imports, fixture construction, repeated schema/JSON/hash validation,
   subprocess startup, immutable host setup and actual test logic. Capture baseline commit,
   versions, worker/memory limits, cache state, case counts and machine load. Do not run
   repeated full suites merely to obtain a prettier timing estimate.
4. **Optimize the measured bottlenecks.** Reuse genuinely immutable preparation while giving
   mutation tests isolated copies; reduce unnecessary serialization and duplicate setup;
   reuse safe dependency/build caches keyed by exact relevant inputs. Add source/input
   drift and cross-case contamination controls where reuse changes behavior. Never cache
   away per-response checks or treat a cached acceptance as authority for changed bytes.
   Sealed K2 runtimes remain unchanged; any future production optimization follows its own
   source/identity/review/lifecycle boundaries.
5. **Reduce redundant execution and schedule safely.** Compare CI job coverage and special
   options before moving a test to a single owning job. Required checks must remain required
   and discover the same applicable assertions. For mutation reviews, use a validated
   guard-to-regression mapping to run the smallest discriminating selection, with discovery
   sentinels for activation defects like F6. Retain occasional broad audit selections;
   do not silently remove required final or independent checks. Parallelize isolated cases
   or shards within measured CPU/memory limits, avoiding shared writes and nested pools.
6. **Validate the whole improvement once.** Compare the same test identities, outcomes,
   refusal classes, determinism and required fault detections before/after. Run the affected
   selection during development; one appropriate final integrated suite after changes settle.
   Broaden only for actual new changes or failures. Report wall time, CPU/memory and cache
   effects honestly, along with regressions and limits. No arbitrary speedup target before
   the baseline identifies the available opportunity.

## Expected cadence proposal

| Work | Intended cadence, subject to existing requirements |
| --- | --- |
| Fast developer checks | Relevant edits; never advertised as complete qualification |
| Required CI regressions | Relevant code commits; preserve explicit source/config coverage |
| Documentation checks | Prose-only changes under conservative existing classification |
| Focused fault controls | Changes to the corresponding guard, test or cached preparation |
| Broad mutation sweeps | Significant validator/checker revisions and scoped independent review |
| Full first-use/replay evidence | Required release/identity boundary; no reduction of approved calls |
| Deferred hosted native/nightly/performance | Remain governed by U0024; no infrastructure activation here |

Any change to a normative cadence, mandated repetition count, gate or independent review
obligation is a separate concrete policy proposal, not an optimization disguised as a skip.
Keep the 798-call historical campaign intact; faster development profiles cannot replace it.

## Deliverables and acceptance

Produce a baseline cost/coverage inventory, ranked bottlenecks, reproducible timing records,
progress reporting, a bounded patch with measured improvements, and a recommended ongoing
cadence. Include exact before/after test sets and fault controls, cache invalidation/isolation
proofs, total CI coverage reconciliation, command recipes and remaining costly groups.
Use normal main integration and hooks; preserve peer history and existing docs-only rules.
No new package, hosted infrastructure, registry or spending is assumed. Prepare proposals for
protected edits or new dependencies before that dependent implementation. No CI polling;
Javid monitors hosted outcomes and reports failures.

## This checkpoint is not the U4 exit

The current component Stage 3 adjudicates a 23-file **unapplied** contract/mapper/checker/test
proposal. [Its first-use ledger](../U4-A-component-stage2-v1/first-use-ledger.json) still has
no component engine/build/runtime authority or native execution and retains human choices.
M, K1 and the local K2 first-use campaign are distinct completed pieces, not the whole sprint.

[Execution plan U4](../../execution-plan.md#u4--bounded-native-engine-and-silicon-readiness)
and U-P11b still require native component implementation/verification (checkpoint B), actual
reference-suite admission/readiness (R/G3a), and applicable independent/human acceptance.
The 70-row TPU dossier is a proposal, not an admitted usable reference or signed suite.
Actual silicon measurement belongs to U5 and is not required merely to close U4 readiness.
Full product tables remain U7. U0024 defers remote qualification, not component correctness
or reference readiness. Final U4 review, fresh documentation refresh, closeout and tagging
follow the applicable exits; accepting this proposal plus editing docs is insufficient.
