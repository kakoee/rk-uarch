# Successor implementation and evidence checklist

| Area | Required successor behavior | Focused evidence |
| --- | --- | --- |
| Component review and D3 | Explicit versioned record/consumer transition; build provenance and startup assurance independently required; optional read status has no authority | Missing, wrong-subject, stale-format and mismatched executable/source/tool/generated input refuse; trace absence alone does not prevent an otherwise qualifying synthetic record; absent startup still refuses |
| Identity | Freeze actual final source, consumer, build commands/environment, tool/cache/image and generated inputs | A changed required input invalidates its binding; no self-hash cycle; old binaries retain old identities |
| Build execution | Fresh output directories; accepted tools; declared environment; captured actual status/stdout/stderr; existing bounded resource/cleanup handling | Success with ordinary compiler diagnostics can be recorded; nonzero exit, missing artifact, timeout or incomplete required logs cannot become success; mock tests must not count as native build evidence |
| Reproducibility | Separate source provenance, clean build success, binary rebuild equality and simulation determinism | A hash discrepancy is reported; debug/release binary differences are not mistaken for result nondeterminism; reuse applicable receipts without another broad sweep |
| Runtime checks | Correct job/model/checker route, exact negative envelopes, independent consumption, retained failures, replay, full-ID cleanup unchanged | Changed hookups get discriminating guard-removal/restoration checks; unchanged semantics inherit exact evidence |
| Startup | A-F3 remains a distinct prerequisite | Synthetic refusal for missing assurance only; no retry/reconstruction/transfer of blocked startup-substitution activity |
| Historical evidence | Preserve read gaps, NONE CAPTURED and all historical packages | Hash/identity comparisons; no retrospective read_audit_complete or old-runtime rebinding |
| Planning | ADR, execution plan, canonical prompts and build-spec agree | Patch postimages, prompt-sync and links; no full suite for prose alone |

Do not turn this into a new universal attestation framework. Reuse existing strict record
and binding helpers where suitable. Any new review format is prospective and tied to its
exact consumer; presence of a boolean alone is not proof. The exact schema is the A/B
implementation proposal, not an installed schema or approval created by this checklist.
Existing compiler warning policies (including clippy -D warnings) remain effective.
The seven-container incident retains unknown impact; cleanup may touch only exact full
container IDs owned by the task. No shared-label deletion or prune.
