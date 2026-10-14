# U3 published-revision verification

**Publication and applicable checks passed; human closure/tag remain separate.**
Verified GitHub main commit `390ec9aa06eef33da6274eb28ae6ca1c3ae3d623`, tree `a8dbdba71af3b43390bfa5e9fc98784d474211af`.
These are new coordinator execution records, currently uncommitted; they do not claim to
be part of that tested commit. U4 remains unauthorized.

## Executed on the exact published revision

A new clone was fetched directly from GitHub, checked out detached, and given a new
virtual environment with `uv sync --frozen --extra dev --python 3.12`. CPython and normal
uv download/build caches were reused; the prior editable install/environment was not.
Module origins point into this clone. Initial and final Git status are clean.

- Local full suite: **1,701 passed, 29 explicit skips**, no failures/errors.
- Required-vendor contract tests and licence tests passed (overlap the full-suite count).
- Lint, both CI-form type checks, import contracts, schema freshness and strict current
  vendor verification passed.
- Environment: ElfinKidsLaptop Ubuntu/WSL2, CPython 3.12.14.
  This is correctness/replay evidence; no simulator-performance measurement is claimed.

[Local receipt](fresh-clone-receipt.json) and [environment details](local-environment-details.json) record the environment, exact commands, skips and
results; [logs](local-logs/) and [driver](fresh-clone-driver.py.txt) retain reproduction detail.
[Hosted CI 38512473386](https://github.com/kakoee/rk-uarch/actions/runs/38512473386) succeeded on the identical commit, including executed
Python, contract and licence tests. [Counts and scope](ci-summary.json),
[job identities](hosted-ci.json), and [log excerpts](hosted-ci-excerpts.txt).

Golden, determinism, native, performance and ordering jobs and the patches step had no
inputs and were **no-ops**. The licence step did run. No native, performance, golden,
silicon or nightly evidence is inferred from their green status.

## Retained limits and next decision

Current analytic results remain STUB with unknown error and unverified energy. Historical
verification reports remain partial/not_run, with the 22/24 clock shortfall and their exact
implementation bindings. Accepted design and policy do not install the dependency repair,
release U4, or implement a native engine. No source, adopted artifact or protected file was
changed by this validation. Original reviewer records remain unchanged.

[Final verification](final-verification.json) completes the published-revision check.
Javid's separate human U3/G2 closeout and tag decision is still required. Any subsequent
documentation publication must distinguish this runtime evidence from tests executed on
that later commit. No tag, closure, cleanup or U4 authorization occurred here.
