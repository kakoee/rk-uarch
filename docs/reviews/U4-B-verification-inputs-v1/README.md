# U4 Lane B independent verification inputs, revision 1

Status: proposed case selection and agent-authored mathematics, **not native evidence**.
Authority: [U4 kickoff](../U4-kickoff-v1/README.md), installed U0011/U0023 and the
[accepted design](../U3-reviewed-design-and-policy-v1/acceptance.md). Baseline is
`f58e07828fa7a953b06800b227b948d7e9e71a88`; u03-end target
`6d39a234a14855c86ca54b795501a0b0b2618d7b` is an ancestor. Author: Lane B agent.
No human assignee, human working, approval or independent-review verdict is claimed.

The [catalogue](catalogue.md) freezes the proposed finite selection and literal answers
for this checkpoint. [Arithmetic](arithmetic.py) and [six worksheet tests](test_arithmetic.py)
use Python's standard-library rational arithmetic, a searched edge sequence and bounded
closed forms. They import no production timing/count code, accept no arbitrary task graph,
and implement no event scheduler, general traffic simulation or second timing engine.
Their passing assertions verify these worksheets only. Native controls/faults/restored
runs, signed profiles and two qualifying replays remain planned/not_run.

[Human worksheet inputs](human-worksheet-inputs.md) contain questions and inputs only.
[Agent expectations](agent-expectations.md) are deliberately separate. The human must
supply their own committed working under validation/L1_limits/hand/ after authorization;
an unfilled worksheet SKIPS by ID and cannot pass L1.

Exact A schema/profile/registry joins and immutable tool pins were not published at the
initial baseline. A subsequently published the early M patch at bad9a125d82bbf723675465c9291fb37fa82f799;
[the exact audit and partial fixture joins](../U4-B-policy-transition-v1/m-audit.md) reconcile it. The finite selection here does not grant arbitrary variant admission.
Pin full hardware/graph/point/profile bytes, semantic revision, seed=0 and allowed jobs
before any public invocation. All synthetic specs are proposed-design stipulations with
per-field rationales; eventual reviewed destination is hw/designs/test-fixtures/.
Production remains the one cold npu-l4/ratio1/BF16/TP1 component tuple. No schema or hardware
file is installed by this package. The profile signer/review mechanism requires an exact
M decision; an agent-authored case list is not a human signature.

[First consumers and R questions](first-consumers-and-R.md) keep preparation bounded.
Historical U3 reports remain partial/not_run with aggregate clock 22/24. This package
neither regenerates them nor claims their coverage for native work. STUB, unknown error,
unverified energy and null unrepresented observations persist. Component u_c0_duration_ps
stays null; independent lower bounds do not introduce an analytic component API.

Reproduce locally from repository root:

```sh
python3 -B -m unittest discover -s docs/reviews/U4-B-verification-inputs-v1 -p 'test_*.py' -v
```

Publication and final reconciliation are recorded in the [handoff](../U4-B-policy-transition-v1/handoff.md).
