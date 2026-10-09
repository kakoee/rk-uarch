# U2 B1 decision v1 — human acceptance record

Status: **ACCEPTED** by Javid (@jjaffari), acting for both U2 lanes.
No Reza approval is asserted.

## Exact authorization

> Approve U2-B1-decision-v1: U0004, the exact H1/H2 stipulated designs, and draft-only references. Keep A1 reconciliation, generation/adoption, commit/push and closure separate.

Accepted decision brief: [U2-B1-decision-v1.md](U2-B1-decision-v1.md),
SHA256 `b867040803fe2dba1680be95de3bbf5425ddefd68aeea02065717819603c8f3e`.
Its pending wording remains historical; this subsequent record supplies the approval.
The B1 37-payload manifest remains
`05daf76bfda1b71a6307bcfeab6fd60ea4045676525991205543454d5cc20747`,
preserved at `U2-inputs/B1-05daf76bfda1/`.

## Accepted inputs and exact scope

| Input | Accepted source SHA256 | Disposition |
| --- | --- | --- |
| U0004 candidate | 79269d86dcb7381fd1e70c382e9bd4fa1384d0121ba69ec531c9fe23a18076f1 | Accepted text, including the explicit commercial/thesis sentence; active ADR adds approval/status annotations. |
| hw/designs/npu-l4.yaml | 41731f6ac7fe99aaf221edaf917ffdd03cd0fcdd8149ee5f5110bfe42a5911c0 | Exact stipulated H1 input, all 59 sourced values and categorical settings. |
| hw/designs/npu-m256.yaml | e12d08d40e7b3c0e7ab1443141745a6c082ee544ecfc43c5609c8cd289a35d9e | Exact stipulated H2 input, all 67 sourced values and categorical settings. |
| TPU v5e reference draft | acea41f651a5f63e1697937f3879364e5f4342249efeaff1dcc6b6b4345a898d | Retain only under preserved review inputs; no physical runs/performance reporting/L3 evidence. |
| Blackhole p100a reference draft | cdd1a51cc9c181b2c9062e8c46ad79989f6873734602152059b05ca363ef3371 | Same draft-only disposition. |
| Complete B numeric/source inventory | 6cfe2e0441bc125e10b065f925edd03b8f18417d1d0af78495867b95a8b5bc01 | Exact decision context retained; its original proposed-status text is historical. |

The two designs are accepted questions for simulation, not evidence of physical feasibility,
measured performance or validated energy. No FP16/FP8 support is added to BF16-only npu-l4.
The separately accepted nominal efficiency1.0 remains an unvalidated model assumption.

Reference placeholders and missing unit/usable-capacity/operating-point/layout facts remain
unresolved. Do not install these reference drafts as active runtime inputs or treat approval
as a waiver of runnable-reference requirements. Reviewed replacements or an explicit fidelity
limitation are required before a future physical reference run.

## Integration and remaining work

Install only the two exact accepted designs, an active U0004 with acceptance annotations,
and a current sourcing-status index. Keep B1 source artifacts and the accepted candidate
unchanged. A separate frozen B1 supplement supplies these additions to the common authority;
the 262-file baseline v1 stays byte-identical.

A1 reconciliation remains a separate checkpoint. The 64 B semantic cases remain pending.
B-F16 still requires actual export, reviewed tooling, four precision observations, human
two-run generation, whole-revision adoption and integrated tests. No oracle generation,
artifact adoption, final review verdict or sprint exit is authorized by this record.

No commit, push, tag, main transfer or closure is performed here. Worker worktrees remain
untouched; hashes identify uncommitted local bytes, not Git history or off-machine backups.
