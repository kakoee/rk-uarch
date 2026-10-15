# Installed K1 inventory: coordinator reconciliation

B's exact proposal at `c41499458307836484efdeb587a6c8bd4c5c910f` is ready for
the separately reserved live-binding decision. No correction is requested.

The [two-path patch](../U4-B-K1-installed-inventory-v1/inventory-bindings.patch)
updates the historical 19-test inventory to the actual 28-test selection and adds a
separate replay/fault evidence binding. It changes no Rust code, toolchain, image,
artifact, policy or workflow. The controls file is passive data; installing it does
not activate a fault runner or hosted CI job. Future execution must explicitly consume
and verify it, as described in B's [handoff](../U4-B-K1-installed-inventory-v1/README.md).

## Coordinator checks executed

- Re-ran `reconcile.audit()` without its file-writing main entry point. Installed
  postimages, the approved AST-identical formatting exception, real Cargo metadata,
  saved native results and fault/restoration logs all verify.
- Re-ran the 35 host guard tests: **35 passed**. These validate saved evidence and
  deliberate in-memory mutations; they are not new native executions.
- Applied the exact patch in a private temporary repository. Both postimages match
  their declared candidates byte for byte. Reverse restores the old inventory and
  removes the new controls file; forward restores both exact candidates.
- Scoped Ruff and whitespace checks pass. Read-only workflow search found no active
  native-K1 consumer in `.github/workflows` or `.github/*.py`; historical proposals
  remain unchanged. Remote main matched the submitted commit. No CI polling occurred.

Temporary audit and patch check: `/tmp/u4-k1-inventory-review-yffs9lfi`.
Executed commands and scope are recorded in [verification.json](verification.json).

## Evidence boundaries

The 28 tests per mode, six replay payloads and 13 metadata-fed linkage/guard checks
remain attributed to tested source `fb7ba4a75d17650d91c2d2532460ccc1c16b5808`.
The semantic faults and restoration campaign remain attributed to
`63ca8bec5a4ac1d7dcf87290a5cf080c846de66d`. The native/dependency bytes are identical;
the only non-review delta is the approved Python test formatting. No new fault run
on the final source is claimed. Prior Stage 3 acceptance is preserved, not repeated.

No full Python suite, native tests, measurements, remote CI or nightly ran in this
reconciliation. Live `.github/native-k1-tests.json` remains unchanged, and
`.github/native-k1-controls.json` remains absent. This review does not release K2 or
close G3a/U4. See the [exact next decision](next-decision.md).
