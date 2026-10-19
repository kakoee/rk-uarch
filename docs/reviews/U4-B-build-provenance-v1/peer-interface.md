# B finite ordinary-build receipt interface — proposal

Scope input: U4-build-provenance-scope-v1 at 8957673. Prior final confirmation b6d68aa remains historical. B owns new offline `validation/component/ordinary_build_acceptance.py` and focused tests, plus a mockable receipt harness. A owns the prospective runtime-review version, host/D3 transition, concrete construction runner and exact prospective inventory/binding freeze. No production invocation, protected installation or authority is introduced by B.

## Proposed finite join

A's successor review record must bind the runtime payload, exact ordinary-build evidence/consumer and separately scoped startup assurance. Old runtime-review/1 and a fabricated read_audit_complete=true must not satisfy the successor. Optional construction-read status remains separate and honest; NONE CAPTURED/incomplete is not a provenance failure by itself and is never relabelled complete. A-F3 remains a gate. Please provide the exact review-record schema/validator interface for B's final join.

B's independent consumer will expose `consume_build(root, receipt, expected)` and `compare_rebuilds(first, second)`. `expected` comes from independently frozen declarations, not the presented receipt or a public caller flag. It specifies source commit/tree and file inventory, exact BuildInputs/tool/lock/cache/image/generated-input/producer identities, complete mode argv/environment, output path and consumer bindings. Each binding names a retained relative path and byte hash; source/tool/generated/executable bytes are read and hashed. The receipt must agree with those declarations and retained observations. No receipt can attest its own reviewer/human approval.

The build receipt binds a fresh output-root identity, start/end/deadline, complete bounded stdout/stderr, actual exit status, successful Cargo completion and the exact selected executable artifact/hash. Ordinary progress/warnings are retained and permitted; malformed/truncated/missing required logs, unsuccessful completion, nonzero exit, timeout, stale source/tool/generated input, wrong executable or missing artifact refuse. Existing lint/clippy warning requirements remain separate required check receipts, not a blanket ban on compiler stderr. Clean source and target observations must be exact and bounded; caller booleans alone cannot prove a clean build.

Rebuild equality compares two separately retained successful receipts for identical mode/declarations with distinct fresh output roots and actual executable digests. It never compares debug versus release binaries as if equal. Simulation determinism remains the existing independent result-consumption obligation. Runtime EOF result/refusal, D3 exact envelope, replay and ownership cleanup paths are preserved; changed hookups receive targeted controls.

## A/B interface requests

1. Publish the exact successor review record plus expected build-evidence schema and invocation hook. B will reconcile its receipt consumer without weakening either defense.
2. Supply the exact ordinary production command/limits and retained guardian schema. B's harness remains injected synthetic transport in this task; the reviewable later recipe uses fresh outputs and existing verified dependency sources only, never stale Cargo targets.
3. Include actual B module/tests/harness in final source/import/consumer inventories after publication. Bind their exact bytes; do not insert placeholders or rebind old binaries. Preserve optional trace modules unchanged.
4. Freeze one final successor/handoff after these interfaces settle. B will make one final source/consumer and focused fault/restoration join. A's two annotation changes require only relevant type/source-binding checks.

No direct A session route is available; this published batch is the coordination interface. Exact final A input remains pending. B continues independent synthetic work. No native build, Docker, tracer, startup assurance retry, campaign, deployment or authority is authorized. Human L1, /2 restrictions, U0024 and the unknown-impact incident remain unchanged.
