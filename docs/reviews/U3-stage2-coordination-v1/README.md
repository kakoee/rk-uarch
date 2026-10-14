# U3 Stage 2 coordination — Lane B received

Independent Lane B Stage 1 targets `184d2c2b08c28a01673be143b086ef223ba6706a`.
The report and evidence remain unchanged and uncommitted. Lane A's review is still
in progress; its evidence is untouched. This note authorizes bounded author proposal
responses only, not implementation, policy acceptance, migration or G2 closure.

## B-F1 reproduction and response direction

The coordinator reproduced the reviewer origin check and both transitive-shadow probes
in a new private archive of the exact target with the reviewed repair patch applied.
Explicit pytest `-c <export>/pyproject.toml --rootdir <export>` and cleared ambient import
paths ensured modules came from the export. Result: 3 passed / 2 deselected; these passing
probes demonstrate the defect, not a passing repaired implementation. Both new
`scripts/typing_extensions.py` and `scripts/annotated_types.py` leave the proposed inventory
unchanged and synthetic strict loading accepted, while the direct vendor CLI executes
the shadow and raises the review marker. No live source or producer was run/changed.

B should propose a conservative correction that preserves protection against transitive
shadows, rather than option 3's reduced guarantee. Option 1 (bind/refuse relevant import
names under actual prepended search roots, with conservative scripts coverage) is the
preferred starting point. B must show exact scope, inventory implications and positive
unrelated-change controls; 52 entries is not a target to preserve. If a different technical
remedy is safer/smaller, propose it explicitly. No entry-point rewrite or policy reduction
is accepted by this note; the corrected patch stays unapplied.

B-F8 should be fixed in the same test-proposal response: mutations belong in temporary
roots, including direct-entry shadow probes. Finally-based restoration of a developer's
checkout is insufficient. Preserve B-C1 hook discrimination and B-C2 currentness behavior.

## Provisional cross-lane recommendations — await A's report

- B-F3: use independent component bounds at the bounded B checkpoint. No unapproved
  analytic component API or full-model bypass; first actual analytic reliance triggers
  its checks, R/U-P9 at the latest for required baselines. Both lane texts must agree.
- B-F5: B owns real Linux CI under existing ownership. Request an explicit accepted
  assignment, prerequisites, first-use deadline and effort in B's proposal; no workflow
  implementation or exact tool/license acceptance is granted here.
- B-F6: finite-window conservation/clipped residence and required observations at B;
  stationary Little's-law <=1% at first claim under frozen population/window/boundary
  premises, normally U6 or earlier if relied upon. Do not quietly skip a required case.
- B-F2 also affects A prose; coordinate the two memory-only operators and base-clock
  premise after A's report. Historical reason codes/reports remain unchanged.
- B-F7 needs exact proposed replacement text and a human-decision row; do not change
  the live U-P6/build-spec or accept a mathematical reinterpretation by implication.

These are recommendations to reconcile, not a new amendment or Javid's semantic decision.
B can complete independent corrections now and mark shared dispositions pending a dated
coordinator reconciliation with A. Every B-F1–B-F8 row still needs an author response.

## Publication/evidence housekeeping

Review scripts were inspected read-only. Targeted Ruff on B's newly untracked evidence
finds 15 style/import diagnostics; they are not defects in the reviewed candidate.
Do not publish these scripts unchanged into all-tree lint or alter reviewer evidence
silently. Preserve originals; coordinate publication-compatible evidence separately.
No new lint exclusions or protected configuration change is authorized. Reviewer A's
in-progress evidence and files must not be staged, edited or committed by B.

Use [B's response prompt](lane-B-stage2.txt). The reviewer returns for Stage 3 after
coordinator reconciliation. No new reviewer or author session is needed for B's response.

Lane B report SHA256 at receipt: `550fe94a69e8a9ae53071ebc0928a55af0a3c1d1f88020119e6211b3ac55c820`.


## Both Stage 1 reports received — coordinated response scope

Lane A now reports two blocking clauses and eight non-blocking findings on the same
`184d2c2` target. The two reviewers independently support the accepted architecture,
U7 full-table placement and U10 integration. Neither report grants design acceptance.
The earlier provisional note above is retained as history; authors no longer need to
wait for A's report to propose the shared clarifications below.

Coordinator arithmetic reproduction: inspected A reviewer probe is standard-library
only, with no repository imports, writes or engine execution. It reproduces E4's
1 GHz channel/arrival observation differences and the 1.2 GHz completion split
(59000 ps fixed-delay reading versus 60000 ps named-domain next_edge reading). The
refresh-omission fault is masked for the first two requests; request five distinguishes
69000 versus 68000 ps under the probed law. These are calculations under proposed
conventions, not native execution or performance evidence.

### Author response direction

- A-F1: A defines explicit test admission and identity/ineligibility semantics; B owns
  the proposed hardware-variant catalogue and rationales. Do not widen production
  admission or treat invented parameters as sourced chip claims. Keep K1 private,
  K2 fixed-delay and B subsystem-test capabilities distinguishable.
- A-F2/A-F3: prefer compliance with the accepted next_edge invariant, not a new exception.
  A specifies every clock crossing, bandwidth-service rounding, wait attribution,
  issue/overhead law and exact fixture mapping; B independently derives expectations
  against that proposed revision. Old end-times are not targets to preserve by tuning.
- A-F4/A-F5/A-F6: resolve owner arbitration, operator/count/byte meanings, validation
  order, all hardware leaves and canonical enumerations in the proposal before asking
  for exact schema/semantic acceptance. Protected/runtime files remain unchanged.
- A-F7: K2 needs the approved fixed-delay boundary and fixtures; component mapper readiness
  belongs before B unless A demonstrates an actual earlier dependency. Align the texts.
- A-F8: explicitly estimate shared complete-work expansion when TPU-specific R is stalled;
  do not make T depend on TPU access and do not double-count reusable work. State U6 inputs.
- A-F9/A-F10: budgets remain prospective human decisions. Propose the exact later U9
  trigger record and observation-volume accounting/envelope choices without calling an
  estimate a measurement, removing required observations or changing policy silently.

### Shared A/B recommendations to include in their response packages

1. B-F3: independent component bounds at B; no undeclared analytic component API. Required
   analytic checks still precede their first real consumer, including R/U-P9 baselines.
2. B-F5: B explicitly accepts/plans owned real Linux CI/tool-pin work, its effort and
   first-use prerequisite. No actual CI change or unpinned tool acceptance is authorized.
3. B-F6: required finite-window/clipped-residence/credit/allocation observations at B;
   stationary <=1% Little's-law check at first claim with frozen premises, normally U6
   or earlier if used. Align V21 and B's table; no false completed-window pass.
4. B-F2: both memory-only ops are head/embed and layers/kv; C2 dominance is at the base
   clock. Correct current proposals on both sides; retain historical reason codes/reports.
5. B-F7: exact proposed DMA and clock prompt replacements plus a named human decision;
   no live U-P6/build-spec edits before acceptance. These are mathematical clarifications,
   not permission to drop conservation checks.
6. A-F1/A-F2/A-F3/A-F10: B records its fixture/test/observation and performance-gate input;
   exact variant files/hashes and qualifying corpus remain future separately bounded work.
   No new hardware installation or native measurement follows from a design response.

These are coordinator drafting recommendations, not Javid's acceptance of new semantics,
ADRs, schemas or budgets. Authors may reject a finding with concrete counterevidence;
respond to every numbered finding, retaining explicit unresolved dependencies. A and B
may proceed in parallel; public fixture expectations tied to a changed A law must wait
for that exact proposal revision, not be silently assumed unchanged.

Use [A Stage 2](lane-A-stage2.txt) in the existing A author session, and send the
[B addendum](lane-B-stage2-addendum.txt) to the existing B session alongside its original
response prompt. Keep both reviewers available for separate Stage 3 adjudication after
coordinator reconciliation. Do not start replacement reviewers or apply live patches.

Lane A report SHA256 at receipt: `b69965a70dc4262141c2d52b877cb9ce253566c1aba3bbf5d64e8e198e774233`.
