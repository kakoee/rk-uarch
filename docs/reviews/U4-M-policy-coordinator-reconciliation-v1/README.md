# M/policy installation readiness — coordinator reconciliation

Subject: B's published `7f36d540599e00041379640790e13e09bd2426c3`.
Executable package: `56d7ddcb4314ec4ecf7f7631c0b2edbe7d17a4e2`.
This is bounded coordinator reconciliation, not K1's independent review or a U4 verdict.

[Next decision](next-decision.md) proposes only human source installation/local commit of
32 exact accepted paths. No installation authorization is recorded here. No design, trust
mechanism, toolchain or licence choice is reopened. The later lifecycle remains separate.

## Executed checks

A fresh disposable clone of the exact subject was used with the existing CPython environment.
The normal pre-commit hook was copied for read-only installer inspection; no human flag was
set and no install-mode execution or source commit occurred. Both patches were applied only
in scratch. Their hashes and all 32 postimages match; M's 26 outputs were also compared with
A's accepted package manifest. Recomputed support inventory matches all 56 path/hash pairs.
The installer passes read-only preflight on a clean clone, checks current artifact integrity,
and establishes the expected strict refusal after the proposed patch.

Final results: **39 preparation guards passed; 173 combined M admission / policy /
vendor-entry tests passed, with one real-adoption skip**. Runtime imports were asserted to come from the disposable
clone before collection. PYTHONPATH/MYPYPATH/VIRTUAL_ENV/UARCH_HUMAN were unset, bytecode and
pytest caches disabled, and test temporary roots kept outside the clone. No new packages,
native execution, hosted job, server contact, input staging or oracle generation occurred.

The initial coordinator run set PYTHONPATH to the scratch source. Its explicit environment
guard refused this (1 failed, 172 passed, 1 real-adoption skip). This is preserved in
[initial-environment-refusal.json](initial-environment-refusal.json); it is not a product
finding or a passing run. The corrected run removes that setting and retains explicit
in-process source/origin checks. [Final commands/results](checks.json) and
[identity summary](result.json) distinguish actual executions from inherited evidence.

B's broader 369-test, schema, static and source-mtime receipts remain inherited. They were
not rerun wholesale. The full Python suite, real new-policy adoption, K1 acceptance and
remote qualification are not established here. Historical native or workflow limitations
are not treated as new defects in this unchanged source selection.

## Installation placement

The coordinator checkout has pre-existing untracked U3 reviewer files. The installer requires
no untracked paths, so it cannot run there as-is. Preserve those files. The existing A clone
was inspected read-only: clean at `892b9ee00c485718082e8ea9a765578cbd64d684`. After approval,
use normal fast-forward to the exact authorization commit there and reserve its source from
concurrent author writes. Its eventual source commit remains local until a complete compatible
artifact/adoption tip passes checks. The fresh K1 reviewer uses its own pinned export and
can continue independently. No author checkout was updated by this reconciliation.

The known artifact mismatch after installation is intentional but not publishable currentness.
The next freeze, human generation, candidate audit, adoption/test activation and coherent push
retain their exact separate approvals and checks under B's transition plan. U0024 continues
to defer infrastructure; it does not waive any of these artifact steps.
