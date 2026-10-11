# U2 v3 checkpoint evidence

This evidence selection accompanies the reviewed U2 software, documentation and adopted
v3 references. It records completed **local** checks; U0021 requires a fresh GitHub clone
and hosted Ubuntu CI on the same published commit before publication verification,
tagging and sprint closure can finish.

- [Local validation](U2-adoption-v3-execution/README.md): 1,394 passing tests, full real
  matrix execution, complete reports, determinism and producer-disabled replay.
- [A review](U2-lane-A-review.md) and [B review](U2-lane-B-review.md): original independent
  reviewer reports, including scoped acceptance and deferred publication gates.
- [Frozen source](U2-source-input-freeze-v3/source-tree.json) and
  [frozen inputs](U2-source-input-freeze-v3/inventory.json).
- [Human creation](U2-real-generation-v3/created.log),
  [second-run byte equality](U2-real-generation-v3/verified-identical.log), and
  [candidate audit](U2-artifact-adoption-v3/audit.json).
- [Adoption approval](U2-adoption-v3-execution/acceptance.json) and
  [complete placement](U2-adoption-v3-execution/acceptance-and-placement.json).
- [Two test binding corrections](U2-adoption-v3-execution/proposed-test-binding-v2.patch)
  and [installation](U2-adoption-v3-execution/test-binding-installation.json) preserve
  the original v2 fixture and all 87 frozen support files.
- [Generated output manifest](U2-adoption-v3-execution/runtime-output-SHA256SUMS)
  preserves reproducibility identities without adding the multi-megabyte report members.

Historical receipts preserve the status at their original recording time. References to
uncommitted state, earlier failures and local paths are historical facts, not current
exit claims. Original reviewer probe directories and unsuccessful exploratory logs remain
local; this selection includes final verdicts and final passing receipts. Existing small
normative selections remain as previously reviewed; no entire checkpoint archive is added.

Executed coordinator helpers are archived byte-for-byte as `.py.txt` / `.sh.txt` evidence.
Their original local filenames and absolute execution paths remain in receipts; the text
copies preserve the exact scripts without treating historical probes as active project
Python modules. The original local tools remain untouched. These historical scripts are
not a new public command interface; use the [workflow guide](../u2-workflow.md).

The independent eight-point public demonstration uses actual AI declaration reviews.
The full-matrix orchestration's explicitly synthetic administrative records grant no
accuracy or evidence eligibility. All 96 physical discrepancies, 48 capacity failures
and 864 not-run cases remain recorded. Neither local WSL2 checks nor CI no-ops establish
a simulator-performance host or replace later hardware validation.
