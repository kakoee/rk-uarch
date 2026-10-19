# Finite transition map

| Current mechanism | Required successor |
| --- | --- |
| component_host.py: prepare_component, ComponentSession.check and refresh; host selector under /etc; transitive required_files reads | Ordinary installed-package preparation/run interface with normal executable selection. No /etc or /var/lib record requirement, no release-review/source/cache/log archive reads on session/job execution. Reuse relevant job/result checks, not authority checks. |
| component_build_review.py, component_review.py; review/2 and startup-assurance/1; B ordinary_build_acceptance | Remove from the ordinary call/import chain. Keep development-only utilities only if they have an actual use; no replacement review/3 or new manifest framework. Historical packages remain exact. |
| native protocol.rs authority(), generated ENGINE_JSON/TRUST_JSON and finite hash-bound case admission | Normal binary accepts valid supported jobs according to schema/model/capability rules and explicit test-mode distinction where needed. Remove per-build human/compiled-corpus permission, not correctness checks. No cfg(test) or private adapter substitute for this path. |
| NativeEngineIdentity / NativeModelIdentity implementation_hash, compiler_lock_hash; host-owned anchor arguments | Minimal explicit versioned schema/API transition to package/engine/model versions. Preserve input-data hashes and actual semantic checks. No dummy hashes, silent reinterpretation or second IR; do not rewrite historical results. |
| preparation, mapper, Python/Rust DTOs, result/checker selection | Update all producers/consumers together; actual returned version and requested model must match. Wrong job/model, unsupported work, malformed output and capacity/lifetime faults remain discriminating. |
| D3 negative-review/authority chain | Run negative tests through the same ordinary executable, retain meaningful refusal checks and failure receipts. No special human token to test an invalid request; do not replace the safety of precise refusal tests with code-only matching if that hides wrong guards. |
| custom trusted-start launcher, pre-start manifest assurance, cache/hook/DSO attestation | Standard installed Python environment and declared dependencies. Package import smoke tests are ordinary correctness evidence, not a hostile-startup defense claim. A-F3 withdrawn by scope change; blocked experiment not retried. |
| capture tools, read-audit gates and compiler-line allowlists | Optional archived diagnostics; absent from required runtime/build acceptance. Keep failure facts unchanged. No mandatory bit-identical binary rebuild. |
| pyproject wheel contents, native executable, packaged schemas/validators | Installable package works outside checkout using only runtime dependencies and requested data. No tests, docs/reviews, Cargo cache, .git or development receipts required at runtime. |
| tests asserting obsolete approvals/pins as product behavior | Retire/replace explicitly with the simple-contract tests. Preserve model/semantic controls and original review evidence. Do not keep old gates alive only to pass obsolete tests. |

Verification should demonstrate one supported positive, producer-disabled saved replay,
required debug/release determinism and a small set of meaningful invalid-job/wrong-result
controls through the ordinary binary. Cover other affected model laws through existing
tests and reused evidence. The installed-package fixture runs outside any checkout with
only needed runtime files and inputs present; imports and file-access assertions can prove
absence of developer paths without tracing compiler syscalls. No new universal filesystem
monitor is requested. Report actual startup/per-job wall time only as an unqualified local
diagnostic if readily available; no performance threshold or new benchmarking project.

Keep protection of repository-owned contract files, golden expectations and ADRs during
development. That workflow is separate from a user's right to run installed software.
Do not delete historical sealed deployments or touch unrelated containers to clean up.
The existing /2 model discrepancy stays restricted; approved /3 laws are unchanged.
