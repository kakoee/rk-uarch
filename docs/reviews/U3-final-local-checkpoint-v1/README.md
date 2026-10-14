# U3 final local checkpoint preparation

Javid accepted the design and prospective policy **for U3 closeout only**. This package
prepares their durable records and completed independent reviews for one local commit on
main. U4 remains unauthorized. Push, published-revision checks, tag and closure are separate.

The five human-installed documentation files match their approved postimages. The fresh
non-author narrative was reconciled and installed byte-for-byte from proposal
`f46e96de645f52d260ba575414c0b5f0cbdae752ba0c5e1eebdfda277af167be`.
See [reconciliation](documentation-reconciliation.json) and the
[fresh-session handoff](../U3-final-documentation-refresh/handoff.md).

The proposed selection is about 1.5 MB of documentation and review evidence, across 140
paths. The commit contains six live documentation targets: build-spec, execution-plan, U-P6,
U0002, U0011 and how-it-works, plus the closeout record, approvals, review reports and
necessary evidence. Runtime, contract schemas, tests, support inventory, adopted artifacts,
CI configuration and dependencies are unchanged. The policy repair is still an unapplied
proposal. Native implementation and full tables are future work.

Original reviewer reports and receipts are unchanged. Twenty review programs are published
as byte-identical `.py.txt` evidence, with replay instructions, so archival fault probes are
not collected as maintained tests or linted as production scripts. Their original `.py`
files stay untouched and untracked locally; no caches or bulk generated output are selected.
[Publication mapping](../U3-closeout-documents-v1/evidence-publication.json).

## Verification and scope

Completed precommit checks on a private local clone of `7afba9b`, overlaid with the
selected documentation:

- Full suite: **1,701 passed, 29 skipped, zero failures/errors**. [Log](checks/full-suite.log).
- Contract tests also passed with `--require-vendor`; these overlap the full-suite count.
- Full-tree Ruff, both exact CI-form mypy targets, import contracts, schema freshness and
  strict vendor currentness passed.
- Static commands had PYTHONPATH/MYPYPATH unset. Runtime module origins were confirmed
  inside the private clone; the existing environment was reused without installation.
- The received narrative's 60 links and numeric/hash assertions were rechecked against its
  saved evidence; its 342 focused executions remain attributed to the fresh session.

[Validation](validation.json) records commands, environment, counts and conditional CI
input counts. [Tested selection](tested-selection.json) identifies the documentation
overlay used for that run. The final selection adds result receipts, status prose and the
separately checked commit helper; runtime, tests, schemas, configuration and the five
approved normative postimages are identical. [Final packaging checks](packaging-checks.json) cover those additions (full-tree Ruff,
179 local links, maintained-text whitespace and documentation-only scope).
This is precommit validation, **not** the required hosted/local same-published-commit gate.
Empty native, golden, determinism, patch, performance and prediction-ordering jobs are not
credited as executed correctness or performance evidence.

[Helper checks](helper-checks.json) verify check-only success and refusals for wrong digest,
changed bytes/mode, wrong branch, changed hook and nonhuman commit. No test set the human
flag or made a commit. Maintained prose/code pass whitespace checks. Raw `.patch`, `.diff`
and `.log` evidence retain their original context/diagnostic whitespace rather than being
rewritten. No repository hook, lint or CI configuration changed.

## Local commit, then stop

Proposed message: `docs(u3): record accepted design, policy and closeout evidence`.

The final [commit selection](commit-selection.json) lists every path, byte hash and file mode. Its own SHA256 is
supplied separately to [human-commit.py](human-commit.py). The helper requires the exact
parent `7afba9b16d954fd46684711764cb3718170e53aa`, main, an empty real index, exact file
bytes, no unrelated tracked edits and the unchanged normal hooks. Check-only mode uses an
isolated temporary index. Only `--commit` with the human's `UARCH_HUMAN=1` stages and commits
the listed paths. It checks the resulting parent and tree, then prints a receipt.

This human action is required because [CLAUDE.md](../../../CLAUDE.md) says “Agents propose
and stop on ... docs/decisions/”; the installed hook also requires human commitment for
those paths. The helper never sets that variable, pushes, tags, migrates artifacts or
releases U4. Untracked original review scripts are preserved.

After returning the local commit receipt, publish main separately, execute the fresh
hosted/local checks on that published revision, and present the result for human closure
and `u03-end`. U3 is not declared closed by this checkpoint.
