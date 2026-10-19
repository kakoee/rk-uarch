# Capture diagnostics: proposed policy and command join

This is a decision-ready proposal, not accepted capture policy or activation. B implementation was published at ac9c5f6. The live monitor stays byte-exact at caaca851… with conservative stderr refusal. The new offline helper is not connected to that live route. All monitor/construction changes are unapplied and tested in a private export. No real tracer, accepted-image exercise, build or capture was run.

## Proposed separation and its evidence

Preserve A's exact unwrapped construction argv and selected environment. Under the accepted tracer prefix, run this fixed tracee wrapper, where PHASE is exactly canary/debug/release:

```text
/bin/sh -c 'set -C; exec 1>/receipts/PHASE.child.stdout 2>/receipts/PHASE.child.stderr; exec "$@"' capture-child CHILD_ARGV...
```

The child arguments are positional arguments, not interpolated shell syntax. The wrapper changes only its own descriptors, after the tracer has launched it. Tracer/bootstrap stdout and stderr remain on the guardian's original channels. Shell noclobber requires fresh child files; a redirection or bootstrap failure remains on an original channel and refuses. Both child streams are separate because stdout may otherwise mix bootstrap output with Cargo or the canary sentinel.

A host-only mock tracer launched the shell with the fixed receipts prefix relocated to a private host directory. Its diagnostic stayed on original stderr; child stdout/stderr went only to their separate files. A second shell invocation refused existing files without replacing them. This demonstrates the descriptor mechanism in a synthetic subprocess test. It is not accepted-image/strace evidence, an actual capture or proof that an untrusted producer cannot forge records.

Offline acceptance independently checks the retained traces: exact wrapper exec followed by exact native child exec, exclusive `openat` creation and fd1/fd2 redirection before the native exec, no pre-redirection writes/forks, known process tree, complete terminal records, write-record byte accounting and phase output rules. Caller flags cannot establish attribution. Streams cannot alias or use symlinks. The outer monitor still checks exact rendered command/guardian intent, owner/full ID, cleanup, resource/time/total-output bounds and source/input identities before a diagnostic result can affect record validity.

The supported accounting subset is deliberately narrow: complete decoded `write` records and one writer per child stream. A partial successful write counts only its returned byte prefix. Truncated strings, `writev`/unsupported stream-mutating mechanisms, undecodable data, multiple writers without a separate order proof, unknown syscalls or missing records refuse. This does not presume the actual shell/tracer will emit this exact supported form. Any different real form remains a concrete attribution gap requiring a reviewed extension; there is no fallback to accepting a flag or summing byte lengths. No real stream attribution is claimed yet.

## Exact proposed phase rules

The hash-bound policy is `component-capture-diagnostic-policy/1` at `inputs.capture_diagnostic_policy`. The new capture branch is plan `/2` and receipt `/2`; historical plan `/1` stays conservative and unwrapped. A's production BuildInputs `/3` and recipe `/2` remain the declaration authority for build argv/environment; the legacy canary recipe `/1` and exact canary argv remain separate. Policy JSON contains no approval or authority field.

| Retained channel | Canary cap | Debug/release cap | Acceptance rule |
| --- | --- | --- | --- |
| `container/stdout` (bootstrap) |65,536 bytes |65,536 bytes |Must exist and be empty. Any mixed/bootstrap output refuses. |
| `container/stderr` (tracer/bootstrap diagnostics) |65,536 bytes |65,536 bytes |Must exist and be empty. Tracer loss, unknown diagnostics, bootstrap failures or mixed child text all refuse. |
| `traces/PHASE.child.stdout` |4,096 bytes |16 MiB |Exact canary sentinel, or complete newline-delimited Cargo JSON with classified record reasons and exactly one final successful `build-finished` record. |
| `traces/PHASE.child.stderr` |4,096 bytes |4 MiB |Exact prospective canary missing-file diagnostic, or complete exact lines in the independently frozen phase-specific reviewed list. No general warning/error/Running prefix whitelist. |

The proposed canary bytes are stdout `U4-read-canary-v1\n` and stderr `/bin/cat: /canary/absent: No such file or directory\n`. These are literal prospective expectations exercised synthetically, not a newly measured image result. Canary acceptance also checks the unchanged strict parser's canary obligations (inherited sentinel read, failed lookup, directory enumeration, process coverage and image mmap). The diagnostic writer must be the unique `/bin/cat /canary/absent` child, with status1; stdout must be written by the sentinel cat. All other processes, the root and guardian must finish with status0.

For debug/release, every process and the guardian must finish with status0. stdout permits `compiler-artifact` and `build-script-executed` records followed by exactly one `{"reason":"build-finished","success":true}`; `compiler-message`, unknown records, scalar JSON and missing/truncated final records refuse. This classifies output only: it does not validate or adopt an artifact or prove semantic correctness. stderr permits only complete exact reviewed lines for that mode. Lines containing tracer/loss/truncation/unfinished markers cannot be reclassified through that list. Every retained child byte must match trace-supported successful writes in process order. Exit0 or valid Cargo completion alone is insufficient.

The supplied `diagnostic-policy-proposal.json` has **empty debug/release stderr lists**. Thus real nonempty build stderr currently refuses. The synthetic positive uses a clearly labelled synthetic line; that line is not inserted into the proposal. Human acceptance must decide this exact classifier, canary expectation and bounds, then separately approve any concrete build-line classifications with their exact policy hash. No synthetic line list can become real authority. If a broader dynamic classifier or multi-writer mechanism is desired, it needs its own concrete reviewed amendment.

Original guardian stream caps may be lower but cannot exceed65,536 in the new branch. The unchanged phase budgets remain at most30 seconds/16 MiB total owned output for canary and600 seconds/512 MiB for build capture. All trace bytes and child/original streams count toward the total; the checker additionally caps200,000 trace records. The monitor polls individual caps and total files, so overshoot is retained and refuses; this is not a filesystem quota. Existing bounded cleanup and final metadata overhead remain separate. Failed records retain raw streams, traces, hashes, partial statuses and the refusal reason. There is no truncation-to-cap, deletion, retry-to-clean-log or implicit missing-file-as-empty rule.

Empty original stderr plus complete classified records is explicitly **not an independent loss counter**. `read_audit_complete` always remains false, even when `diagnostics_accepted` and mock record validity are true. Unknown/unfinished/lost or unclassifiable evidence remains a refusal and cannot be converted into read completeness.

## Implementation, tests and discrimination

Actual new files are `validation/component/capture_diagnostics.py` and its test. `proposals/diagnostic-monitor-unapplied.patch` is based on A's exact300c7093 declaration monitor, not the earlier caaca851 live file. Its combined postimage is8c527a57ff350423b6855f9533d137f329342aed0c9d4daf3f1ba8a28f547241. It adds the policy-bound `/2` branch, wrapped command, individual stream polling and structured acceptance/refusal consumption while retaining A's declaration checks and legacy behavior. No live monitor or protected source is edited.

The focused final selection has27 diagnostic tests, six command/monitor joins and one historical `/2` serialization/refusal control:34 total. New tests are synthetic/offline; the sole real subprocess exercise is the host-shell mock tracer. The monitor integration uses an inline fake worker and a synthetic guardian ledger, so no actual worker/container/capture starts. Matching mock data produces a `/2` receipt; duplicated otherwise-classified stderr makes the real monitor return `record_valid=false` and retain the diagnostic error. Both debug/release wrapped commands preserve B's independently recorded literal argv/environment, with exactly one linker-map suffix and eleven exact keys. A consistently resealed omission still refuses; legacy plan `/1` remains unwrapped.

One targeted fault removed only the raw-byte/write equality guard in the private helper. All three phase positives still passed, and duplicated classified stderr was unsafely accepted, causing the regression's `assert not True` failure. Exact bytes were restored and the four affected controls passed. This is a behavioral discrimination, not a stale hash or incidental refusal. No broad mutation sweep was run.

Development records distinguish an initially incomplete synthetic syscall list (which refused before the targeted monitor error) from the corrected fixture and final tests. Initial typing/export diagnostics were corrected without suppressions; private-overlay Ruff/mypy checks cover the actual proposed imports. Earlier B33/consumer/D3 evidence is inherited unchanged; it is not relabelled as this run.

## Construction coordination and remaining decisions

A's exact4418829 intermediate declaration delta has been reconstructed and all six postimages verified. Its per-mode specification and recipe `/2` integrate with the diagnostic wrapper without modifying the native child's argv or environment. The known duplicate-suffix/shared-environment mismatch is addressed in that proposal; historical `/2` serialization is preserved. The final A source/consumer/import freeze must include the actual new helper/test, combined monitor, pure specification, policy/command schema and unchanged parser closure. No placeholder pins or silently rebound binaries are acceptable.

A's final declaration/source handoff is still a separate exact dependency until it is published and reviewed. The interface direction and intermediate arithmetic do not substitute for that final join. Human acceptance of the diagnostic policy is also pending; code/test success supplies no approval. A concrete future policy, recipe, generated identities, accepted tool/cache mounts, wrapper/shell startup closure, immutable placement, permitted capture/build and runtime/public-first-use decisions remain separate.

A-F3 remains deferred, neither retried nor transferred. The three candidate-03 read gaps remain unresolved, with no new read/capture coverage. Incident impact remains unknown. Protected installation, authority, genuine L1 workings, the /2 first-use restriction, U0024, R/TPU readiness and G3a/U4 closure are unchanged. This package does not authorize an actual capture or build.
