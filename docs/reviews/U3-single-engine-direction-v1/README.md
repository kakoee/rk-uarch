# U3 — One progressive production simulator

Javid approved the architecture direction on 2026-10-12. This package translates it into
one exact documentation patch; live protected files are unchanged. The pre-change checkpoint
is `7fbb0f3bc551f9984f080d9d82c43084cf6e8419`, containing the published A/B histories and the
remaining 42 coordination records (about 135 KB before archive-status clarifications).
Primary was clean at that checkpoint. A is clean at `42fc341`; B is clean at `70adf09`, whose
history is included. No worker clone was modified, no branch history rewritten, no push made.

## Review

- [Exact 27-path patch](architecture.patch), based on the checkpoint above.
- [Readable proposed U0005](proposed-U0005.md); there was no accepted U0005 to rewrite.
- [Scope and executed validation](review.json).
- [Human installer](human-install.sh), with read-only `--check` and explicit `--commit` modes.

The four verification/validation sources are independent mathematical expectations,
behavioral checks, optional matched component references and frozen-prediction hardware
measurements. Remove mandatory full-fork selection, a substantial Python U-C1 replacement,
ONNXim-compatible mapping, permanent full-fork comparison and fork-relative speed targets.
Retain the existing U-C0 baseline and Python preparation/mapping/reporting layers. No runtime
or schema code changes; existing legacy carriers remain readable with their existing rules.

## Revised order

| Stage | A | B | Exit |
|---|---|---|---|
| U3 | U-P5 bounded native-stage/mapped-protocol design | Complete applicable U-P6 and disclose remaining coverage | G2 design/readiness decision; exact stage/schema and runner prerequisites before runtime |
| U4a | U-P7 minimal approved mapping → U-P11a fixed-delay kernel → bounded U-P11b | Independent U-P8/U-P12 literal, behavioral and fault checks | Small declared slice; unsupported work refuses; no complete-table claim |
| U4b | Expand the same engine and U-P7 to full table requirements | Required verification, replay, worker determinism | G3; initial fidelity at most C1, STUB |
| U5 | Frozen native and analytic predictions | TPU measurement and scoped evidence | Existing G4 unchanged |
| U6 | U-P11c diagnostics, initial mesh qualification and absolute cost | Finish U-P12 independent qualification and metrics | Replacement G5; no rebuilding core or fork agreement |
| U7–U11 | Deeper models, silicon, conditional parallelism, integration, hardening | Corresponding evidence and product work | Existing purpose retained; obsolete fork dependencies removed |

No implicit small-scope waiver of U4b's full grid: required unsupported points block G3 or
need a separate scope decision. A missing optional reference is not_run, not verification.
Once an optional comparison is admitted prospectively, failure cannot be erased by dropping
that tool. Same-code comparisons verify integration only. The compatible admitted NoC bound
is retained; incompatible NoC-0 contention sweeps are not asserted as equivalent.

G4/G7 silicon and G8 synchronization gate blocks are byte-identical. No badge, fidelity,
energy or hardware-accuracy threshold is relaxed. Existing accepted ADRs remain unchanged;
U0005 explicitly supersedes only future fork-delivery assumptions. U0011/U0012 remain future
human decisions, with updated purposes. Old effort/calendar tables are labeled historical;
no invented savings, fresh engineering estimates or implementation release is claimed.

## Validation actually executed

In an isolated Git checkout at the checkpoint plus this exact patch:

- Four existing prompt-sync tests passed, including shipped rk-sim prompt mirrors.
- Strict vendor snapshot/matrix/current-support verification passed.
- All 27 changed paths are Markdown; none intersects the 97-path support inventory.
- Existing ADRs and G4/G7/G8 gate text are unchanged; whitespace checks passed.
- Clean-baseline patch application and exact target reconstruction are checked separately
  before package commit; installer check mode makes no repository mutation.

No full-suite/matrix rerun, independent adversarial review, runtime execution, artifact
refresh, host operation, CI dispatch, paid resource use, sprint tag or closure is claimed.
The runtime-publication CI receipt belongs to `456215c`, not this documentation patch.

## Installation and next action

The direction is already approved. `CLAUDE.md` says: “Agents propose and stop on contract/,
tests/golden/expected/, CLAUDE.md, docs/decisions/.” This patch includes CLAUDE.md and new
U0005, so one human installation/commit is needed; the installer uses normal hooks and
requires the human to set UARCH_HUMAN. It does not push. Use the exact package commit supplied
in the coordinator response:

```bash
UARCH_HUMAN=1 bash docs/reviews/U3-single-engine-direction-v1/human-install.sh \
  --commit <package-commit>
```

Return the commit receipt. Publication is separate. After installation/reconciliation, the
next author task is the revised U-P5 **design** prompt; no native implementation is released
by this documentation commit. Continue ordinary independent clones/main development, not
copied checkpoint trees. The temporary review checkout is disposable; Git and this one patch
are the review history, not another manifest-based revision system.
