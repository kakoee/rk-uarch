# Current status — public demonstration passed

The actual independent declaration reviews were accepted and the remaining commands
completed. See the [completion receipt](completion/README.md) for fresh execution,
producer-disabled replay, byte identity and report visibility checks. The original
input receipt and reviewer records are preserved unchanged. The original draft handoff
below is historical; its pending statements have been superseded for this demonstration.

---

# U2 public demonstration — awaiting independent declaration reviews

Status: first half executed; declarations UNREVIEWED. No ReviewRecord, assembled context,
table or report has been issued for this demonstration. This is not artifact adoption,
a new oracle run, hardware measurement, U0021 validation or sprint closure.

The coordinator ran the real public `validate`, `assumptions`, `prepare`, `capture`
and `companions draft` commands from a clean export of reviewed software tree
`53f9f21b7cc3f84c0cbdb5f3f1e74e6e4aeca522`. All five commands exited 0.
The capture loader authenticated eight jobs/results covering every prepared point.
[Commands and return codes](commands.json), [grid](grid.json) and the
[capture/environment receipt](capture-receipt.json) record what actually ran.

The workload is H1 npu-l4, Llama-3.1-8B, BF16 compute/KV, tp=1, frequency ratio 1:
four decode points (batch 1/8 × context 128/512) and four prefill points (n 1/4 ×
L 128/512). The run made no comparisons. Prior U2 full-matrix discrepancies, capacity
failures and not-run cases remain separate evidence; this example neither deletes
those attempts nor claims full-matrix parity or final runtime acceptance.

Generated artifacts are local at `tables/U2-public-demo-v1/`, which is ignored by Git.
There are 27 files, 7,387,438 bytes. The receipt records their hashes for generated
artifact reproducibility; they are not included in the documentation publication tree.
Keep them until the independent review and demonstration are complete. Regeneration
requires the exact source/input identities and must not silently replace review subjects.

The proposed registry is an explicit singleton administrative family for this exact
hardware identity. It asserts no relationship to another design or measured chip.
Its review pointer and the dependency declaration's review pointer are unresolved.
The independent reviewer may accept or reject either subject, including the proposed
family and the scope/intake statement. Engineering approval is not a declaration review.

Send the [external-review prompt](external-review-prompt.txt) to an independent reviewer
who did not author these inputs or the assembly implementation. The reviewer must use
their real session identity, not claim to be Javid or to have performed silicon tests.
Do not send it back to either implementation author as their own independent approval.
The prompt is a new declaration-review task, separate from U-REVIEW code adjudication.

After actual reviews are returned, the coordinator will verify the records and run
assembly, fresh table execution, saved-capture replay and both report modes, including
repeat-byte comparisons and explicit producer-disabled replay. Those steps are pending.

Receipt preparation initially used system Python, which lacked Pydantic. The five CLI
commands already used the project environment and succeeded. Receipt validation then
ran in that same project environment; no producer was repeated to recover from that
bookkeeping error.
