# L3 silicon — predictions first, then measurements

Per reference chip: SUITE.md (signed by both lanes before predictions exist), predictions/
(committed in one "FROZEN PREDICTIONS:" commit, never edited), UNKNOWNS.md (every stub the
engine read), results/ (raw and immutable). check_ordering.py fails CI if any result appears in
a commit at or before its prediction's. A new prediction is a new file in a new commit. Every
benchmark states device-side timing, its mapping match (matched | compiler-chosen), its initial
state, and the compiler-reported FLOPs and bytes the workload graph is checked against.

Run `python3 validation/L3_silicon/check_ordering.py` from the repository root with
full Git history. Predictions are `<chip>/predictions/<id>.json`; a result receipt is
`<chip>/results/<id>.json`, with any accompanying raw files under `<chip>/results/<id>/`.
Every result file needs its prediction's addition commit as a **strict ancestor**.
Independent branches and same-commit additions do not establish prediction-first order.
All files under predictions/, including compressed prepared jobs, simulator outputs and
unknown inventories, are immutable and require the same freeze commit subject.
Prediction additions require the existing `FROZEN PREDICTIONS:` subject prefix. The checker
also refuses edits/deletions of committed prediction and result bytes, including changes
later reverted. Unknown flat result layouts refuse instead of bypassing the check.
Use directories outside `results/` for plans and README files.

The existing CI ordering job runs this check even when no predictions are present, so
results alone cannot skip it. Empty history reports infrastructure readiness only. Git
history cannot prove that someone did not measure privately before committing; the
original separation of prediction and measurement work remains necessary. No current
U4 verification output is silently converted into a U5 frozen prediction.


The TPU v5e U5 freeze uses Javid's explicit 2026-10-22 human acceptance in place of
outstanding lane signatures for the unchanged 52 units. See its [operative agreement](tpu-v5e/SUITE.md)
and [archive/replay guide](tpu-v5e/freeze/README.md). No compiler/device observation is
inferred from that acceptance or from native simulator outputs.
