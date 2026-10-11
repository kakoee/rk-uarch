# U3 schema/report coordinator reconciliation — 2026-10-11

Reviewed primary main `db9f91d4db4388404e5341f7c2364e13394cb15e` after fetching and
fast-forwarding. This is coordinator reconciliation, not independent U-REVIEW or U3 closure.
No live protected file, production implementation, author evidence or worker HEAD
was changed by the review. Only this coordinator package is selected for publication. This directory contains only coordination evidence and proposals.

## A: protected patch ready for the human decision

The exact patch published at `53435927497eb3e4552e32e2c5e887e0bcb05ddc` matches its stated
17-path scope: two contract modules, eleven schema mirrors, three test files and the
U0022 addendum. Patch SHA256:
`8a02ed6cf56846c6f688d195b068aadd19bb2bab11fe751a8af36d8408e04169`.
The approved four-file coverage prose at `c3e7788` is already on main.

Coordinator executed:

- Applied the patch only in a disposable current-main Git archive. Both exact CI mypy
  commands passed with PYTHONPATH/MYPYPATH unset and fresh export caches: 70 source files,
  31 contract-test files. Targeted suite: **138 passed, 28 skipped**.
- Ran the published exercise.py independently against its recorded `531d9c9` base:
  all eleven schema roots equal the accepted prototype, old and new generators are fresh,
  Ruff and both mypy commands pass, both import contracts pass, and **138 passed / 28 skipped**.
  These are overlapping checks, not 276 distinct tests.
- The exercise's strict support check refused with `input support inventory changed`, as
  required. This confirms the need for the subsequent human U0002 lifecycle, not currentness.

No new blocking contradiction found in the bounded carrier patch. Carrier acceptance does
not establish runtime graph/job/result admission: the 28 runtime tests remain visibly pending.
The patch is additive and exports no execution-admission API. v1 is not silently upgraded.
See [the exact next decision](next-decision.md): human installation/local commit and bounded
A runtime implementation are proposed together, with one later combined source freeze.
No protected installation, future implementation permission or adoption is inferred here.

## B: retained reports validate; SR-C1 requires correction

Standalone implementation and evidence are integrated through `db9f91d`. Their actual
execution binding is `eab89e07b0c7e41f7a2a0ee236dd1b00f78228c6`, not a relabelled newer commit.
Coordinator executed all **36 report tests**, passing, and independently decompressed and
validated both complete retained reports against their separately committed plan, corpus and
implementation pins. Canonical uncompressed file hashes:

- L0: `181a73bbb3c8cdb2271d14dbb93facc2e1f581c4c78fd11a01426b383dde59ee`;
  partial/not_run, duration-purpose passed, other purposes not_run.
- L0m: `9dac9cd38e68b6faea79d32f591443cd4207268ae2d0eefafa319a6851a7ca65`;
  partial/not_run, duration-purpose not_run.

These are validator replays of author-retained results, not new engine executions of the
full corpora. The author's 1,456 passed / 29 skipped full suite and two byte-identical report
runs remain attributed to B. No full-suite, runner or nightly rerun is claimed here. Live strict vendor currentness
and Ruff on the new coordinator probe also passed.

**SR-C1 — invalid-return diagnostics cannot always be serialized.** In
`validation/reporting/analytic_report.py`, Recorder.invoke catches malformed results and
then tries to encode that same output inside a canonical JSON diagnostic. Nonfinite values
or non-JSON objects cause that diagnostic construction to fail too. The call is retained as
`error`, but diagnostic_hash remains null and no call_finished event is emitted. The outer
handler records PROTOCOL_REJECTION. Complete discovery/replay still builds a report, but
public validation crashes on the null diagnostic (TypeError), rather than accepting an honest
not_run report of the failed execution.

The [saved probe](probe_invalid_output.py) uses three illustrative engine stubs. Serializable
malformed `{}` is the error-retention control. A dict containing NaN and a plain Python
object each reproduce the defect. [Results](probe-results.jsonl) record the call/event counts,
reduction and validation exception. The preliminary inline probe reproduced the same issue.
The first saved-script launch failed because the runtime import path omitted the repository
root; that coordinator harness issue was corrected before recording the results. No static
check uses this runtime path override.

This blocks completion of B's promised general error-retention behavior. It does not overturn
the valid recorded successful-run reports or imply an observed passing verdict for the faulty
runs; their reductions remain not_run. The current malformed-result regression covers only
serializable JSON and misses the diagnostic construction failure.

[Send B this bounded correction](lane-B-correction.txt). Require tests first, stable retained
diagnostics, full discovery/replay/validation controls and a production-revert discriminator.
Preserve all pins, conservative reductions and existing scope. The corrected implementation
must generate its own reports from a new clean commit; do not rewrite old report identities.
No production attachment or protected change is needed for this correction.

## Remaining work

Javid's protected-install/runtime decision; A implementation and its semantic admission tests;
B SR-C1 correction and independent review; one combined U0002 freeze/human generation/audit/
adoption before source-bound publication; later shared v2 interface decisions. Simulator
choice/U0005, runner registration with Reza and manual nightly remain independently pending.
Normal Git in the existing clones remains the workflow. No checkpoint-tree copying.
