# U2 published-revision validation

**Passed on published main `7fee0a8ed0c5d7bbb20b65c1cf68672470a5ac60`**, tree
`deccb57a573717990762e60fb8819f0ae463ce20`. Publication was explicitly approved by
Javid under U2-main-publication-v1; the exact fast-forward and main-only push are
recorded in [the execution receipt](../U2-main-publication-v1/execution.json).
These new validation receipts remain local and uncommitted. No tag, cleanup or sprint
closure has been performed. No reviewer verdict or historical ledger was rewritten.

## Executed on the published revision

A fresh clone was fetched directly from GitHub, detached at the exact published commit,
with no local object alternates and clean initial/final Git state. ElfinKidsLaptop ran
Ubuntu/WSL2, kernel 6.6.87.2, CPython 3.12.14. The virtual environment and uv/XDG/typecheck
caches were new; only the managed base Python interpreter was reused. See
[configuration](configuration.json), [initial Git state](initial-git.json),
[environment](environment.log), [module origins](module-origins.json) and
[exact commands/results](checks.json). All tested runtime modules came from the clone.

- Full suite: **1,394 passed; zero failures, errors or skips** ([log](full-suite.log),
  [JUnit results](full-suite.xml)). Ruff, both strict CI type checks, import contracts,
  schema freshness and strict current vendor verification passed.
- Actual matrix: 1,008 nominal calls, 96 physical points and six preparations. Nominal
  compatibility passed. The physical track retains 96 discrepancies, 48 capacity failures
  and 864 not-run cases. Four existing precision-refusal observations per track were
  retained; no new oracle invocation or generation occurred.
- All **25 runtime phases passed**: 24 rows, 40,320 comparison paths, 59 stipulated
  inputs, complete source/contributor checks, both report modes and three explicit
  capability substitutions refused. Default hides all comparison magnitudes; opt-in
  exposes 18,768 labelled STUB values with unknown error. Energy remains unverified.
- Repeat rendering: six files / 569,915,944 bytes identical. Prepared/captured replay
  with all producers disabled: **3,316 package/report files / 647,859,722 bytes identical**.
- All 9,962 generated members verify. The output manifest is byte-identical to the
  previously committed local-run manifest:
  `8fbc26b677aed6531eb74711108a3a94bcb98d02ade7431155ae18740ea2ee41`.
  Outputs remain outside Git; no output tree was copied into this receipt directory.
- Public CLI demonstration freshly reproduced all 27 original reviewed inputs. Actual
  committed independent AI declaration reviews bound the exact same subjects. Fresh,
  repeated and producer-disabled saved-input runs reproduced 61 output files and also
  matched the committed prior demonstration manifest. See [result](public-demo/result.json)
  and [prior-output comparison](public-demo/published-reference-match.json).
- H2/70B/FP8 tp8 characterization passed with explicit synthetic assignment; human output
  remains labelled and excludes timing columns ([receipt](characterize.json)).
- A bounded C10 probe exported H1 through the public CLI and loaded its exact emitted
  bytes through the pinned upstream component loader; parameters, execution model and
  serialized reload were preserved ([receipt](pinned-loader-result.json)). The first
  attempt could not import the deliberately partial vendored package; its failure log
  is retained. A separate fresh upstream clone at the exact pin supplied missing package
  initialization. This loader-only test did not execute an oracle or add a production
  dependency. Main runtime validation never imported rk-sim.

The matrix harness reuses the committed v3 validation driver with five recorded
path/revision relocations and no assertion changes ([delta](runtime-driver-adaptation.patch)).
The public-demo harness similarly runs against the fresh clone with separate output
paths ([delta](public-demo/driver-adaptation.patch)). Original sources and fixtures
were not modified. [Final verification](final-verification.json) checks the complete
output manifest, replay identities, preserved worktrees and published remote identity.
[Scoped case evidence](case-dispositions.json) preserves historical namespaces/counts.

## Same-commit hosted Ubuntu CI

[Run 38101625804](https://github.com/kakoee/rk-uarch/actions/runs/38101625804) passed on
`7fee0a8ed0c5d7bbb20b65c1cf68672470a5ac60`: 1,394 Python tests, 579 contract tests,
two licence tests, lint/types/imports, strict snapshot verification and schema freshness.
[Job metadata](ci-final.json), [full logs](hosted-ci.log) and [scope summary](ci-summary.json)
record the actual commands and runner environment.

Golden, determinism, native, perf, ordering and the patches step were conditional
**no-ops** because their inputs were absent. Licence tests did execute. Their green
statuses do not grant those forms of coverage; actual U2 repeat/replay checks ran in
WSL2 as described above.

## Limits and next step

This satisfies the published-revision validation portion of U0021 under accepted
U0003 S scope. Nominal aggregate compatibility is not independent validation of physical
full-workload duration, simulator performance or silicon. Positive real measurement/history
eligibility and nonempty energy verification remain unsupported. Full-matrix administrative
review scaffolding remains explicitly synthetic; the eight-point public demonstration
uses actual independent AI declaration reviews. No human reviewer identity is fabricated.

A fresh-session documentation refresh remains required by
`docs/prompts/STANDING-how-it-works-refresh.md` ("One fresh session") and execution-plan
checklist item 12. Earlier coordinator documentation updates do not establish this
fresh-session requirement. The active how-it-works page still describes the older v2
currentness state and needs the factual final refresh, including a reproducible real
analytic row. Relay [this bounded handoff](fresh-documentation-session.txt) to a fresh
**documentation session**, not an implementation author or another adversarial-review
loop. It produces a documentation proposal only. Then reconcile the proposal and compact
closeout evidence for Javid's separate closure, documentation-commit/push and tag steps.
All worker worktrees remain preserved; cleanup requires its own authorization.
