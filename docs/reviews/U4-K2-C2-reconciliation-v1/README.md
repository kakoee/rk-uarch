# C2 result reconciliation and bounded B review

Subject publication: `3faa3e9dbe785f43c51e26ad886eeb6bc3b00398`.
[A handoff](../U4-A-K2-C2-probes-v1/README.md).
Status: experiment returned; complete typed-carrier parity remains unresolved.
Javid's subsequent [scope clarification](../U4-hashing-SIMD-scope-clarification-v1.md)
removes utility hashing from the simulator no-SIMD restriction. Hash-output SIMD is
non-blocking; no anti-vectorization experiment is needed. Other follow-up proposals
remain subject to reconciliation.

## Results to reconcile

- Both recorded modes agree on 20,955 of 20,965 frozen cases. The same ten mismatches
  comprise seven rational NumericLeaf union cases, integer token `-0`, and two legacy
  SourcedValue float conversions (boolean/string). These concern small experimental
  carriers, not executed public K2 workloads. Full M inputs were normalized by Python
  before canonical comparison; that does not prove full Rust carrier validation.
- Float/canonical/hash comparisons pass within the tested finite corpus. Three separately
  frozen identity supplement cases pass; their later coverage completion remains explicit.
- Release hash output packing uses packed SIMD operations. The inspected compression
  symbol has no SIMD register instructions. These observations are preserved; Javid
  clarified that full-hash no-SIMD is not required. A did not retry changed flags.
- Compiler/linker commands, environment, build-script outputs and dep-info are retained.
  Exhaustive filesystem reads are not traced. Whether this needs a concrete diagnostic
  before a later build/authority gate must be reconciled explicitly; no tracing waiver
  or tool installation follows from this receipt.

A's [follow-up proposals](../U4-A-K2-C2-probes-v1/next-decision.md), SHA256
`063af1b27bf3786ffd6a007d20e9276758cdd68469823550d18f9ed869d6f51e`, propose field-local
compatibility adapters and a separate two-flag vectorization experiment. The latter is
unnecessary under Javid's clarification and should not be pursued. B should review the
typed compatibility proposals before a release decision; the accepted unchanged
dependency set does not need another vote.

## Coordinator checks executed

Inspected and ran A's read-only `verify_receipts.py` with coordinator Python `-I -B`.
It passed input/approval bindings, compressed/raw output integrity, source/vector pins,
the recorded ten mismatches, supplements, command and unit-test receipts, evidence
controls, preservation bindings and links. This checks saved evidence, not native results
independently reproduced by the coordinator.

Independently parsed the saved vectors and outcomes using byte-LF record boundaries:
20,965 unique input IDs and matching output IDs; 20,955 matches and the exact ten
published counterexamples. Independently recomputed 41,830 SHA256 values over the
available expected/observed canonical strings; all matched their recorded hashes.
This confirms saved byte/hash consistency, not correctness of Python expectations
or the Rust implementation. No native process, build, Docker command, compiler flag
experiment or full suite ran in this reconciliation.

The preliminary read command named a nonexistent `build-identity.md`; that file lookup
failed. The actual `identity-and-reads.md` was then read. This did not affect the verifier
or the separately executed independent recount.

## Next step

Send [lane-B.txt](lane-B.txt) to the existing B session. A holds further construction
pending reconciliation. B may reproduce the exact already-authorized baseline probes
offline in private copies, review the proposed corrections and identify the smallest
remaining decisions. It must preserve existing evidence and avoid applying proposals.
Public K2, live dependencies, C3, final authority and qualification remain separate;
U0024 remains in force.
