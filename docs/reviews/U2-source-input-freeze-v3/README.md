# U2 source/input freeze v3

Prepared under Javid's instruction to proceed after the actual-reviewed public
demonstration passed. This freezes the accepted source/input selection for the next
human artifact revision. It authorizes no agent oracle generation, candidate adoption,
commit, push, tag or sprint closure.

- Source tree: `4c940f88f07eb1a22fd64ab5378d66d6b69eced7` (uncommitted Git review tree).
- Existing branch commit: `769a1fef2320430386888bf450af579ea26cf664`.
- Input manifest: `08d0e905cc50943d286b9c6dbcfb2cf844c969dda28b9446162d12734870871c`.
- Previous adopted manifest: `f8220c9457226562040e5646835c3073acd2f58cd7631a5eb9e74632e60cc96e`.
- Upstream pin: `1e5706e0ebfcc67c1a7333079a35b75f693e9963`.

[Git source reconstruction](source-tree.json) records only Git blob identities over the
existing branch commit, not a copied source checkpoint. Its 137 changed entries include
accepted fixes, documentation and small demonstration records. A Git tree is not a
commit or protection for other uncommitted work. Keep all worktrees.

The 24 prepared input files retain 22 exact v2 files; only support-files.json and its
manifest change. Support inventory: 84 → 87 entries, three additions, twelve changed,
zero removed. [Exact input/support delta](input-delta.json) identifies each change.
All hardware descriptors, sidecars, precision declarations and retained original
provenance bytes are unchanged. Seven component/precision pairs, 1,008 nominal cases
and four direct precision refusals retain their required coverage. Changed generated
counts, durations, nulls or refusal outcomes will still require explicit reconciliation.
No numerical equivalence is presumed before the human runs.

Both reviewers accepted software tree 53f9f21b7cc3f84c0cbdb5f3f1e74e6e4aeca522.
Runtime, test, contract, script and CI/config files are byte-identical between that tree
and this frozen selection. The inherited independent full-suite result is 1,392 passed,
two expected strict-support failures, no errors/skips; it is not a new coordinator run.
[Fresh clean-export checks](clean-source-checks.json) cover lint, both exact CI mypy
commands, import contracts and schema freshness. The actual-reviewed eight-point public
workflow demonstration passed separately, including producer-disabled replay and reports.
It does not replace the complete matrix or U0021 publication gate.

Read-only preflight checks source bytes, input/support identities, old artifact integrity,
pristine pinned rk-sim checkout and unchanged existing locked oracle environment.
Environment: CPython 3.12.14, `/tmp/rk-sim-u1-jjaffari-1e5706e`, ElfinKidsLaptop Ubuntu/WSL2.
No environment synchronization, dependency installation or oracle workload calculation
is performed by preflight. Package metadata collection is explicitly distinct from an
oracle workload. This environment is not a simulator-performance benchmark host.

## Human generation

[U0002](../../decisions/U0002-the-vendored-snapshot-and-parity-discipline.md) requires:
“Only a human runs `make vendor-rk`.” The prepared wrapper invokes that same guarded
generator. The coordinator has not run it or set the human flag.

```bash
bash /home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-source-input-freeze-v3/human-generate.sh
```

The wrapper checks the freeze, creates a fresh destination, runs two fresh generator
processes and requires `created: 48 files` then `verified-identical: 48 files`. It checks
source/input/environment identity between and after runs, performs strict candidate
verification, and records complete raw inspection and semantic differences. It uses
Python to inspect logs and does not require rg.

Candidate files stay ignored under `tables/U2-real-generation-v3/candidate`; compact
logs go to `docs/reviews/U2-real-generation-v3/`. Return both generation status lines
and the final manifest digest. If any command fails, preserve its files and return the
output; do not overwrite/relabel it or rerun the whole wrapper into occupied directories.
The complete candidate must be audited before separate adoption approval. Final runtime
matrix/replay, same-published-commit GitHub clone and hosted CI remain required.
