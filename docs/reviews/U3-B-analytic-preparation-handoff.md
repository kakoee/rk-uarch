# Lane B bounded analytic verification preparation

This is the requested standalone preparation handoff, not U-P6 acceptance, an
independent review, U3 start authorization or a joint exit. Javid (@jjaffari) is
the acting human decision-maker for both lanes; no Reza approval is claimed.

## Revision and ownership

- Published U2 baseline: annotated `u02-end`, peeling to
  `79bc1f014306e520aacba3491d60ae6c644b26a8`.
- Implementation and U0006 proposal commit: `42eb1691ed29bf9ba7d129ac8e63a7bce5744e98`.
- This handoff is a subsequent documentation-only commit. Its enclosing Git commit
  identifies the handoff revision; no self-referential hash or tree copy is used.
- Working clone: `/home/jjaff/AI-infra-simulation/rk-uarch-u3-b`, its own `.git`,
  local `main` and newly synchronized `.venv`. Remote:
  `https://github.com/kakoee/rk-uarch.git`.
- Changes are new B-owned `validation/` helpers/tests/mutants and uniquely named
  review documents. No pre-existing shared file required editing or coordination;
  no Lane A file, production semantics, protected path, public schema, hardware,
  dependency, adopted input or workflow changed.
- Post-implementation fetch found Lane A commits
  `f581b50da69ff9b75b0c6c7a68342da647270200` and
  `c7fcb6f9a49dcc5afadc93d452151b1c4e8b92f7`. Their exact diff adds only
  `U3-A-planning-handoff.md`, `U3-G2-physical-expectations.md` and
  `U3-U0005-proposal.md` under `docs/reviews/`. The initial fast-forward attempt
  correctly refused divergent branches; normal merge
  `9ee0bc2475fb086b25977bfd4df7a84a7c457bc2` integrated them without conflicts,
  resets, rebases or history rewriting. Peer proposals remain proposals; integration
  supplies no independent review or acceptance.
- Publication uses a final fetch/integration after the handoff commit and a separate
  ordinary main-only push. No force push, tag, broad manifest or checkpoint copy.

The [U0006 proposal](U3-U0006-proposal.md) contains the complete capability matrix,
preconditions, explicit non-coverage, count conventions, report/version binding
proposal and concrete human decisions. It belongs in `docs/reviews/`; a human must
approve and commit any eventual protected ADR or contract change.

## Executed local checks

Host: **ElfinKidsLaptop**, Linux `6.6.87.2-microsoft-standard-WSL2`, x86_64;
Python 3.12.14, uv 0.12.9, Hypothesis 6.168.3. The existing uv-managed base
interpreter was reused; Lane B's environment was newly created with the locked
repository dependencies. This was not a designated-server or cold-clone U3 gate run.

| Command | Result |
| --- | --- |
| `uv sync --locked --extra dev` | Passed; new clone-local environment, no lockfile change |
| `uv run pytest -q validation --junitxml=/tmp/u3-b-analytic-preparation.xml` | **26 passed, 29 skipped**, 73.77 s; all five mutants executed locally in both modes |
| `uv run ruff check .` | Passed |
| `uv run mypy src contract/uarch_contract scripts` | Passed, 68 source files |
| `uv run mypy --no-explicit-package-bases contract/tests` | Passed, 28 source files |
| `uv run lint-imports` | Passed, two contracts kept |
| `uv run python scripts/vendor_rk.py --check` | Passed, snapshot/matrix and strict current compatibility verified |
| `uv run python -m uarch_contract.generate --check` | Passed, schemas fresh |
| `uv run pytest -q --junitxml=/tmp/u3-b-full-suite.xml` | **1,420 passed, 29 skipped**, 560.52 s, on the implementation tree committed as `42eb169` |
| `git diff --cached --check` | Passed before implementation commit |
| `uv run pytest -q tests/unit/test_prompt_sync.py tests/unit/test_third_party.py` | After peer integration: 6 passed, no skips |

The peer merge and subsequent handoff change prose only; implementation, tests,
contracts and adopted inputs are identical to the full-suite-tested revision. No
second full suite was run for unchanged code. The six focused post-merge checks
verify prompt/register regressions, not either proposed candidate image's licence.

The full suite covers the existing public analytic table/report and companion CLI
paths, physical count/rank/precision/replay tests, report visibility and provenance
regressions as well as these additions. It does not rerun the complete adopted
1,008-case upstream-generation/physical-discrepancy matrix. No oracle was regenerated
or adopted and strict currentness was not weakened.

A preliminary local run exposed a test-only serialization mistake: passing a tuple
of `OpResult` objects directly to `canonical_json`. The test now serializes their
JSON-mode representation. The preliminary run had 19 passes/one failure; its focused
reproduction failed the same way. One obsolete shrinking run was interrupted after
two refusal tests passed. The final bounded and integrated results above supersede
those development runs; no failing normal-suite test is published. Initial import
formatting/line-length lint findings were also corrected before final checks.

The local JUnit files are operational receipts, not committed evidence packages or
stable report hashes. They contain timestamps/durations and remain in `/tmp`.
No source archive, whole-tree snapshot or new broad file manifest was created.

The exercised engine is `analytic`, version `resolved-ops/1`, protocol
`uarch-engine/1`, model `physical-resolved` version `1`. Its unchanged implementation
identity is `sha256:fa3938f8c009c7b80700d35feba7504e4b4da06e628d2e387480c358963974ea`;
the accepted physical assumption set binds to
`sha256:255afd1ceb9c02a4909464c41e98e16085485a8e500090a8e2d98dc2ee56a896`.
These are engine/assumption provenance bindings, not a new evidence claim.

## Mutant discrimination and controls

Each row below passed its valid engine control and caught the named fault by
`AssertionError` containing that mutant's name, for both `aggregate` and `per_op`.
The Hypothesis settings bound each parametrization to 24 examples, disable the
example database and deadline, and use deterministic generation. Controls exercise
the two fixed decode/prefill points; mutant rejection occurs at the first witness.
Mutant objects are structurally valid and resealed, so stale identity alone is not
the reason for rejection.

| Mutant | Discriminating assertion | Result |
| --- | --- | --- |
| `off_by_one_matrix` | Independent fixed graph count key, despite reconciled per-op/total mutation | Caught in both modes |
| `double_attribution` | Critical-path attribution sums to duration | Caught in both modes |
| `zero_unmodelled_diagnostic` | Busy time/diagnostics must remain null | Caught in both modes |
| `nondeterministic_output` | Full canonical result bytes repeat | Caught in both modes |
| `wrong_bandwidth_field` | Duration halves when bandwidth doubles and all terms remain memory-bound | Caught in both modes |

Mutant tests carry the existing `nightly` marker. They are intentionally included
in the local commands above; the ordinary hosted Python selection excludes them.
They have **not** run on the required self-hosted nightly runner. The test wrappers
are never installed as production engines and do not establish thread-race,
queue-loss or allocator fault coverage.

## Skips, unresolved decisions and remaining checks

There are 29 explicit skips: 14 relations in each analytic mode, plus exact
whole-query reciprocal clock scaling for `per_op`. The 14 are executed-MAC
telemetry, DMA conservation, window utilization, Little's law, timed causality,
SRAM occupancy, energy conservation, NoC/SRAM bandwidth response, core permutation,
idle mapped cores, untouched stipulation (deferred domain), latency response,
DMA concurrency and cold/steady history. The proposal gives each reason. Aggregate
compute-bound clock scaling executes; memory-only embedding prevents applying its
premise to the complete `per_op` fixture. Separately deferred DRAM-bound clock
response is documented, not counted as an executed test.

Synthetic BF16 hardware-rate generators and separately regenerated tp=1 query
pairs are bounded examples of supported contracts, not full precision/topology,
selected-rank, arbitrary graph or physical accuracy coverage. Fixed prepared work
and producer correctness remain separate. Saved replay is authenticated and runs
with the producer disabled; stale and rehashed-invalid graphs are refused.

The proposal leaves exact decisions for Javid: U0006 capability wording, a valid
DMA control volume/inventory equation, clock and queue observation premises, and
the canonical report source payload/scoping under existing VerificationRecord
closure. No new schema or semantic rule has been implemented for these decisions.
Accepted U0003/U0004/U0019/U0021 policies are preserved, not reopened. Any bound-input
change retains U0002's human generation/adoption lifecycle.

Still required: stable hashed L0/L0m source reports and version-mismatch tests,
reviewed verification/card bindings, broader property domains, Lane A/human-approved
fork protocol extension, fork execution of applicable suites with no silent
re-preparation, independent same-work G2(c) counts, fork build/determinism/runtime/
licence criteria, independent review and the actual designated-host nightly run.
The current analytic-only engine identity cannot honestly be reused as a fork
identity. No claim is made that adding the fork will require zero interface work.

Host status remains: `javid@152.53.209.203`, administrator Reza unavailable,
container installation pending, runner state unverified, nightly schedule paused.
No server privilege, runner registration, schedule or host/runtime/gate waiver
changed. Golden baselines/scenarios, native sources, performance baselines,
silicon predictions and fork execution are absent from this preparation; their
conditional CI steps are not positive evidence. No hosted-CI success is claimed
from this local session.

Stop at this handoff. No tag, sprint closure, later prompt, independent-review
verdict or model badge promotion follows from these checks.
