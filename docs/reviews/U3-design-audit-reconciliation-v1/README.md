# U3 design and dependency-audit coordinator reconciliation

For Javid and the lane authors. Reviewed published main `1ad61f6` on 2026-10-12.
This is coordinator reconciliation, not independent U-REVIEW, G2 acceptance or an
implementation/policy release. No protected or production file was changed.

Inputs: A design `3ebe76b87881e83f0aa62e91018346d1d1b065d4` and handoff `c828510`;
B audit `a602683`, readiness `cbb4fcd`, merge `a32b752` and clarification `1ad61f6`.
The coordinator fast-forwarded to published main, preserving both lanes' history.

## Direction and scope

A's v2 package implements the accepted sequence: U3 design; M/K1/K2/B for bounded
engine work; R for the actual reference suite; T for the first full product table
in U7. It does not require full tables in U3/U4. U10 remains product integration.
K1's semantic/toolchain conditions are distinct from the later host/nightly gates.
B's first-consumer schedule follows that separation and preserves historical gaps.

B proposes reducing the support inventory from 97 to 52 entries: 39 retained,
58 removed, 13 added. It binds generation/verification imports and reviewed data,
rather than all consumer Python modules. Imported schemas/initializers can still
trigger refresh. This is not a promise of zero future adoption cycles. The policy
and migration remain unaccepted; existing U0002 enforcement is unchanged.

The packages merit continued review, but the exact combined package is not ready
for blanket acceptance. Resolve the bounded items below first. No architecture
or sprint-order redesign is requested.

## A-C1 — clock coverage scope

`U3-native-stage-design-v2/verification.md` names C1 as “v1 compute-clock distinct
coverage, both modes” and associates the historical 22/24 shortfall with the proposed
anchor remedy. B correctly identifies that cell/remedy as aggregate-only. Existing
per_op exact whole-query reciprocal scaling has a false premise due to the memory-only
embedding. A's surrounding prose recognizes the premise problem but the table remains
ambiguous and is a normative attachment in proposed U0011.

Correct the table and any dependent summary. Keep aggregate C1, independently justified
component-clock tests, and any future true-premise per_op domain distinct. Do not change
historical outcomes or authorize a new corpus. See [A follow-up](lane-A-followup.txt).

## B-C1 — public loader enforcement lacks a discriminating test

The proposed new-policy branch in `scripts/u2_inputs.py::load_inputs` invokes
`u2_support.verify`. In a private export with the exact repair patch applied:

- Original proposed tests: **30 passed**.
- Remove only that five-line invocation, replacing it with `pass`: **30 passed**.
- Restore the invocation: **30 passed**.

A separate coordinator synthetic input control passed through the actual `load_inputs`
boundary. Its input copy was explicitly synthetic: new policy/inventory and recomputed
input hashes, not human generation, adoption or actual provenance. A changed bound
`src/rkuarch/hw/derive.py` was refused with the real hook (`input support bytes changed`)
and accepted with enforcement disabled. Restored source/enforcement accepted the valid
control again. Thus the hook works in this probe, but its removal is not detected by
the supplied tests. No oracle or input producer was run.

Add durable synthetic integration controls through `load_inputs`, covering valid input,
bound-byte drift, inventory/dependency changes, policy substitution and legacy dispatch.
Require the intended source/inventory refusal, and show hook removal accepts attacks
and fails the new assertions. Keep actual generated/adopted positive currentness as a
separate later human-lifecycle check; synthetic unit controls do not discharge it.

## B-C2 — migration-specific expectation in a permanent test

`test_legacy_integrity_survives_but_currentness_requires_migration` always expects
`vendor.check_generator(ui.ADOPTED)` to refuse. `ui.ADOPTED` names the current adopted
artifact, not an immutable legacy fixture. After legitimate new-policy adoption the
strict check should succeed, so the exact test would reject the desired final state.
This is a source-inspection finding; no real new-policy adoption exists or was simulated
as provenance. B already discloses remaining integration-test work; this identifies one
concrete completion requirement before accepting the code patch.

Separate an explicitly pinned legacy control from current-artifact expectations. Preserve
legacy refusal against changed source without requiring every future current artifact to
fail. Do not weaken strictness, use historical checks as currentness, or remove the test
merely to make migration green. See [B follow-up](lane-B-followup.txt).

## Checks executed by the coordinator

- Live strict vendor currentness: passed at `1ad61f6`.
- A's inspected documentation checker: 8 files, 25 local links, two JSON projections,
  arithmetic and effort assertions passed. These are not native execution evidence.
- Repair SHA256 matched B's `bb15bd236938c659b3c07b8be03121aaa5f41ee339560ba150a7cb4cec8391f8`;
  patch applied only to a private `git archive` export of `1ad61f6`.
- Proposed policy tests: 30 passed; hook-removal and restoration as described above.
- CI-form mypy with PYTHONPATH/MYPYPATH removed: 79 production/script files and 31
  contract-test files passed. No full suite, native build, performance, hardware,
  generation/adoption or hosted CI rerun was performed.

## Next decisions, kept separate

1. A corrects A-C1; B corrects B-C1/B-C2, publishing bounded follow-ups through normal Git.
2. A supplies a concrete proposed M import/initializer/data impact note for B's audit.
   B then states what this actual schema design would retain in support. No installed
   schema is assumed; new actual edges still require checks at implementation.
3. Reconcile corrected packages and obtain independent review before asking Javid to
   accept exact stage/model/observation/U0011 and separate policy/migration choices.
4. Exact toolchain/licenses and the protected M patch are subsequent concrete decisions.
   No kernel implementation is released by this reconciliation. The pre-M policy decision
   does not become a blanket prerequisite for unrelated K1 design preparation.
5. Analytic remedy/corpus, two human-worked fixtures, reference access/readiness and later
   performance/product budgets retain their own scopes and first-use deadlines.

Do not ask Javid to approve all remaining U3/U4/U7 work as one bundle. The user-facing
next action is the two bounded author follow-ups, not another plan amendment.


## Correction recheck at 184d2c2 — 2026-10-12

Review target `184d2c2b08c28a01673be143b086ef223ba6706a`, tree
`6f74542bf5fc85997e044a135293db95297e3e20`. Received A correction `c17cb9c`/
handoff `5c81915` and B correction `184d2c2` by normal fast-forward. The earlier
reconciliation remains historical. The scoped coordinator corrections are resolved;
the proposals are ready for independent review, not accepted for implementation,
installation, migration or G2 closure.

| Item | Coordinator recheck |
| --- | --- |
| A-C1 | Verification, proposed U0011 and summaries distinguish aggregate 22/24, native component-clock checks and a future true-premise per_op domain |
| M consultation | A identifies prospective imports, initializers, shared carriers/export and data reads; B classifies their consequences. This is design consultation, not an audit of unimplemented M code |
| B-C1 | Four public-loader attacks fail when only its verification call is removed; valid/legacy controls remain passing |
| B-C2 | Pinned U1 integrity/currentness is separate from synthetic legacy U2 dispatch and the current-adoption positive; a real new-policy adoption must pass strict validation |

Checks executed here:

- Corrected patch SHA256 `97d0ec302606838a7055ec3d43ce1d3b759e8e015ecb796eed154ce4b0915e55`
  verified; proposed production hunks byte-identical to the prior patch. Applied only
  to a private archive of the exact target, never live.
- A checker: eight files, 36 links, two JSON projections and arithmetic passed.
- Corrected policy and vendor-entry selection: **53 passed, 1 skipped**.
- Remove only the new-policy loader invocation: **4 failed, 40 passed, 1 skipped**;
  the four drift attacks failed with `DID NOT RAISE ValueError`.
- Restored loader: **44 passed, 1 skipped**. The first coordinator wrapper overcounted
  duplicate pytest diagnostic text and stopped after source restoration in `finally`;
  the restored selection was then run separately. This was a wrapper assertion, not a
  proposal-test failure.
- Live strict vendor currentness passed. No full suite, new static-suite rerun, native
  execution, generation/adoption or hosted CI result is claimed by this recheck.

The single skip is real human-generated/adopted new-policy positive currentness. It
remains an open migration exit; synthetic controls do not supply provenance or adoption.

Next: use the [fresh independent review prompt](independent-review.txt). Review the
actual model/interface choices and dependency policy, not just correction receipts.
Retain A/B sessions for author responses. Javid's stage/U0011/schema-plan decision,
separate policy/migration decision, toolchain closure and later exact protected
installation remain separate. No further author correction is requested at this point.


## Review allocation correction

The user correctly identified that the standing process is per lane. The combined
review recommendation above is superseded; its historical text is retained. Use two
fresh non-author sessions, with [A's prompt](lane-A-independent-review.txt) and
[B's prompt](lane-B-independent-review.txt). Both review `184d2c2` and independently
check shared boundaries. B's scope includes its readiness/consumer proposals as well
as the dependency repair. Each reviewer writes a distinct report and later adjudicates
that lane's author responses. The coordinator reconciles shared findings.

No proposal or accepted policy changed. This corrects review allocation only, not the
reviewed commit, pending human decisions or implementation authority.
