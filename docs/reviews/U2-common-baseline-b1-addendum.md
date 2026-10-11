# Accepted B1 addition to the U2 common baseline

Status: ACCEPTED under [U2-B1-decision-v1](U2-B1-acceptance-record.md).
Use this addition together with unchanged baseline v1, whose manifest remains
8ce7b0d6ee152df698543d5be98dc2f2733533a7ed679bcbfa53335303e8370e.

Frozen addition directory:
`/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-common-baseline-b1-addendum/`.
It contains 45 repository-relative payloads; SHA256SUMS digest:
`b8c08a9be17dccbcebbf94d316438830e0b2959df6018d06c4eb43721605710b`.
Verify SHA256SUMS from that directory before consumption. Active U0004 and H1/H2 inputs
in this addition govern over historical pending labels. Preserved originals stay unchanged.

The only active hardware files supplied are npu-l4 and npu-m256, with their exact approved
bytes. The current sourcing index records their stipulation status and the explicit reference
restriction. TPU v5e and Blackhole p100a exist only under preserved review paths; they are
excluded from physical runs, performance reports and L3 evidence. No generic schema change
or promise of physical correctness is implied by accepting the two proposed designs.

A1 reconciliation is still pending submission. No new dependent implementation handoff is
issued here. Existing A1 work may continue; use the approved additions when those inputs
are needed. B1 policy/input approval does not supply A's executable APIs. Reconcile those
before B2, preserving the division between A1 types and later A2 runtime closure/bridges.
The 64 semantic B cases and B-F16 remain open; do not ask again for U0004/H1/H2 approval.

No worker was overlaid, and baseline v1 was not modified. Do not replace B's original ADR or
inventory just to change status: its original B1 manifest must remain valid. Future handoffs
should reference this approval/addition and identify implementation changes separately.

Verification: both exact approved designs pass the existing HardwareSpec validator; all
59/67 sourced leaves are stipulations with rationales. Approved YAML bytes match B1 inputs.
Reference drafts are absent from active hw/references paths. Hash checks cover this addition,
the original 262-file baseline and worker B1. This is input verification, not a runtime exit.

Everything is local and uncommitted. Commit/push, generation/adoption, final reviews and
closure remain separate. Main and worker files remain untouched by this integration step.
