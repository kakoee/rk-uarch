# Javid's clarification: simulator SIMD restriction and utility hashing

Status: human scope clarification recorded; applies to the ongoing C2 reconciliation.

Javid stated:

> That no SIMD had nothing to do with this. It was about the runtime of the simulator
> itself, particularly of it can accelerate it if functional tensors gets involved

The coordinator incorrectly extended the simulator acceleration restriction into a
requirement that the entire utility hash path contain no SIMD. Javid's clarification
resolves that interpretation. The build-spec's exclusions of SIMD/GPU/MPI execution
backends are consistent with this distinction.

## Effect on current work

- Compiler-generated SIMD in utility hashing, including the observed release hash-output
  packing, is not a violation of this simulator acceleration restriction and does not
  block C2 or later K2 progress.
- Do not pursue the proposed `no-vectorize-loops` / `no-vectorize-slp` experiment or
  further disassembly merely to eliminate SIMD from hashing. The coordinator's full-hash
  no-SIMD acceptance condition is withdrawn. Preserve existing observations as historical
  evidence, not a failure awaiting remediation.
- Continue checking canonical bytes, hash outputs, dependency/build identity and
  deterministic behavior. The ten typed-carrier mismatches remain unresolved. Read-audit
  limitations still need their own bounded reconciliation; this clarification neither
  resolves nor expands that work.
- Deliberate SIMD acceleration of simulator execution, particularly functional tensor
  execution, remains outside the currently released work. No new execution backend or
  functional tensor implementation is authorized.
- Keep accepted dependency versions, features (including `force-soft`), toolchain and
  compiler flags. This is not a request to optimize hashing or change accepted inputs,
  install live dependencies, construct C3 images or implement public K2.

## Supersession and handoff

This clarification supersedes only the utility-hashing SIMD restrictions and associated
stop/decision obligations in the C2 construction proposal, approved probe handoff and
coordinator reconciliation. All other input bindings and boundaries remain operative.
Historical author packages, approvals and receipts are preserved. No protected file is
edited by this record.

Send this addendum to the active B session (and A if considering follow-up work):

> Javid clarified that the no-SIMD restriction concerns simulator execution acceleration,
> particularly functional tensors, not utility hashing. Read
> docs/reviews/U4-hashing-SIMD-scope-clarification-v1.md after integrating main. Treat
> compiler-generated hash-output SIMD as non-blocking; do not pursue anti-vectorization
> flags or further no-SIMD proof. Continue the bounded typed-carrier parity, coverage and
> read-audit review. Preserve evidence and accepted dependency/feature/flag identities.
> No broader implementation release follows.
