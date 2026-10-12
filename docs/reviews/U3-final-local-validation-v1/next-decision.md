# U3-runtime-publication-v1

Proposed decision, pending Javid's approval. The previous checkpoint approvals expressly
kept push separate; this is that publication decision.

Approve a normal fast-forward push from A's local `main` to GitHub `main`, followed by a
fast-forward update of the primary `rk-uarch` clone and observation of hosted CI on the
exact published commit. Preserve all lane and human history; do not force-push.

The software target tested is `3a148a0bc953ad0a536de1934184ba9e313e544d`, tree
`24f1a418ea052d1400c89c38b1968d142d0f829e`. Its final publication descendant adds only
this validation directory through an ordinary Git merge; the coordinator's final message
identifies that exact candidate commit. Recheck remote ancestry and a clean tracked/index
state before pushing. A changed remote requires reconciliation, not overwriting peer work.

Included:

- Human-installed additive rotary v2 contract and accepted U0022 prose.
- Reviewed local RoPE preparation, admission, analytic execution, capture/replay and dispatch.
- Human adoption `ed9d7bb` and admission activation `fa8716b`.
- The coordinator probe import correction and two hash-order-independent CLI refusal tests.
- This validation record, using Git commit IDs and diffs rather than copied checkpoint trees.

Validation: 1,701 passed, 29 existing skips, no failures/errors; all required static/schema,
strict support and contract checks passed. All 97 frozen support files and the adopted
manifest `1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a` are unchanged.
The full suite ran on local WSL2/Python 3.12.14, not hosted CI or the designated Linux runner.
Conditional CI jobs with no inputs are explicitly inventoried in `scope-check.json`.

This approval does not change runtime semantics, adopt another artifact set, grant an
independent-review verdict, approve fork tools, attach production verification evidence,
complete the runner/manual nightly, tag a release or close U3. Public v2 product/report
integration remains separate. No generated bulk `tables/` files are included.
