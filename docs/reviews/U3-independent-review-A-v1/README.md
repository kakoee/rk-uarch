# Lane A independent review evidence — U3 target `184d2c2`

Probes and logs supporting [the Lane A Stage 1 report](../U3-lane-A-review.md). Reviewer
arithmetic and read-only carrier checks only: no native build or run, no engine/producer
invocation, no generation/adoption, no install and no protected or author file edited.
Arithmetic under the proposal's laws is not native execution evidence.

| File | Purpose |
| --- | --- |
| `run_all.sh` | Re-creates a fresh `git archive` export of the target and runs everything below |
| `run_all.log` | Exact output of the run cited in the report (UTC timestamp inside) |
| `probe_contract.py` | Export-only imports; npu-l4 hash; literal C1 OpSpec/PreparedOp; R06 v1 disposition; hash/OpSpec fault and restored controls |
| `probe_ledger.py` | Classifies all 59 npu-l4 SourcedValue leaves against the B ledger; checks the resident projection against existing `Counts`/`ExtCounts` |
| `probe_arithmetic.py` | Standard-library re-derivation of E1–E5; alternative readings of E4 and zero-delay; fault/restored controls |
| `probe_volume.py` | Lower-bound size of mandatory observations at B's maximum input (estimate, not a measurement) |

Reproduce from the repository root (paths are arguments; scratch output only):

```bash
bash docs/reviews/U3-independent-review-A-v1/run_all.sh "$PWD" <empty-scratch-dir> docs/reviews/U3-independent-review-A-v1
```

The runner unsets `PYTHONPATH`/`MYPYPATH`, uses the existing `.venv` binaries without
`uv sync`, and asserts that `rkuarch`/`uarch_contract` resolve inside the export rather
than through the venv's editable path to the live clone. WSL2 host: no timing in these
files is a performance observation.
