# Lane A Stage 3 adjudication evidence — target `a7f4acb`

Supports the 2026-10-13 Stage 3 section of [the Lane A review](../U3-lane-A-review.md).
These are proposal-text, carrier and arithmetic checks on private `git archive` exports.
They are not native execution, regression or corpus evidence. Nothing was installed or
generated, and no author, peer, protected or prior evidence file was edited.

| File | Purpose |
| --- | --- |
| `random_selection.txt` | The `SystemRandom` draw (made before the run) that selected A-F9 for the bounded revert |
| `run_stage3.sh` | Fresh exports of the target and Stage 1; author checks on both; bounded A-F9 revert, partial reverts and restore; reviewer probe; preservation hashes |
| `run_stage3.log` | Exact output of the run cited in the report |
| `revert_af9.py` | Reverts only the A-F9 text in a scratch copy (each edit must match once) |
| `f9_reason.py` | Evaluates the author's four f9 assertions one at a time to show which one fails |
| `stage3_independent.py` | Reviewer re-derivation of all ten corrections without the author's helpers |

Reproduce from the repository root:

```bash
bash docs/reviews/U3-independent-review-A-stage3-v1/run_stage3.sh "$PWD" <empty-scratch-dir> docs/reviews/U3-independent-review-A-stage3-v1
```

In the Stage 1 line of the reviewer-probe section, the printed `exit=0` is the exit status
of `tail` in the pipeline. The failures list on that line is the result.
