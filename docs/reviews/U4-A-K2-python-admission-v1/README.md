# U4 A: Python admission, case reuse and shared startup

This is the consolidated **unapplied proposal** for the campaign-throughput task
and both shared addenda. Three exact patches and their complete changed files are
in this package. Accepted source remains `24fa36803081e5077d5977baa91441a2c8534ec8`;
the original first-use package remains `f2b270aa55204a6bf43ff8d3b7fdeb902db30c0f`.
No production/protected file, sealed runtime, authority, dependency or native binary
was changed. All new execution evidence is Python validation of saved genuine data;
native spawning was blocked. The stopped campaign remains **88 checked calls / 89
transports, incomplete**. Its bytes are verified in
[partial-campaign-preservation.json](partial-campaign-preservation.json).

## Exact candidate and three lifetimes

[source-bindings.json](source-bindings.json) gives full baseline/postimage/patch
SHA256 values. Final postimages are:

| Source | SHA256 |
|---|---|
| runner.py | `ce82a76e6887ace0d65349a7c09159293466b73ff656680e90184a716ffd7ed9` |
| hardware.py | `98b1b06ddf686da948223ca517b0ac16729fbd0f3f6fd1b5bc6f61c1507cb1b5` |
| host.py | `0f44dee94c753829b05d3a646d3ffb33a297468da11e5d8647aeaf64c24508ba` |

- **One public call:** [runner.patch](runner.patch) admits and owns canonical bytes
  and a fresh loader result once. `run_fixed_delay` request admissions fall from
  three to one; standalone `parse_response` from two to one; `encode_request` stays
  at one. Public input still validates afresh. Changed/malformed midcall authority
  falls back to fresh admission, retaining baseline refusal meanings. Transport,
  framing, limits, public signatures and the complete result-validation body are
  structurally unchanged. No external admitted-model argument or bypass flag exists.
- **One case and mode:** `admitted_case(value, *, host)` yields
  `execute(*, limits=None)`. It privately owns exact admitted bytes/model and authority
  values; each execution checks authority before/after transport, opens/hashes the
  actual executable and fully validates its output. Three repetitions need one
  request admission instead of nine. Debug and release use independent real bindings
  and contexts: two admissions per six-slot case group. Caller mutation cannot change
  captured input; new bytes/authority require a new context. The sequential context is
  PID-bound, expires on exit and releases its state. It exposes no shared mutable model.
- **One startup session:** [host-session.patch](host-session.patch) adds
  `resolution_session()` yielding `select(*, mode)`. The genuine resolver validates
  the entire installation and all 133 jobs once, including both mode receipts/binaries.
  Each selection rereads exact selector bytes, rehashes every originally bound file
  and materializes independent record/profile models through the real authority
  constructor. It never manufactures release authority from debug. The session owns
  immutable bytes/values, is PID-bound and expires on exit. Drift refuses; restoration
  succeeds only after all original identities are rechecked. The public `resolve_host`
  remains a fresh complete validation per call. There is no durable/global host cache.

[hardware-rule.patch](hardware-rule.patch) is separately applicable and protected.
It caches at most 128 compiled **rule patterns**, never input paths. Each lookup
consults the current rule order and allowed labels. Mapping edits therefore remain
effective; schema metadata and exception behavior are preserved. This is independent
of the three admission lifetimes.

The full API/fork/cleanup contract and final B fix are in
[peer-interface.md](peer-interface.md). B's single-threaded parent selects both modes,
keeps the session open until workers are reaped, and lets workers inherit genuine
bindings through the reviewed Linux fork path. Case contexts are entered locally
after fork. No token serialization, worker corpus re-admission or nested pool is
proposed. B owns scheduling/resources; the independent checker still reparses each
saved request in A's timings. Optional checker reuse is a separate B-owned join.

## Measured processing and startup

All timings below use the accepted image and pinned Python 3.12.14/Pydantic 2.13.5
with explicit private import origins. Image, interpreter, package, module, command,
environment and test hashes are recorded in each run. No downloads occurred. Containers
were network-disabled, read-only, unprivileged, `--pull never`, with original evidence
read-only. A Python audit hook and subprocess guard prohibited process execution.
Transport replay checked exact request bytes and returned saved genuine output;
actual executable descriptor/hash verification and independent expectations remained.

[final-guard/report.json](receipts/final-guard/report.json) contains the unprofiled
factorial comparison: K01, K02, K03-owner, K04, each three saved debug-0 replays;
12 checks per configuration, two rounds in reversed order, in one process. These
are not new native repetitions or release results. Medians in seconds:

| Configuration | Admissions / 12 checks | Median seconds |
|---|---:|---:|
| Baseline | 36 | 94.484 |
| Rule only | 36 | 26.269 |
| Per-call reuse | 12 | 45.201 |
| Per-call + rule | 12 | 12.461 |
| Case reuse | 4 | 29.531 |
| Case + rule | 4 | 9.187 |

Every configuration produced the same canonical result/receipt signature. The
independent checker was retained. cProfile runs are separate files and are excluded
from these timings. Resolver times are separately recorded, not hidden in processing.
This matrix executed runner `fd27471a…`; final `ce82a76e…` adds only the missing-profile
presence check below. The matrix is inherited evidence for unchanged work, not a
claim that the final bytes ran that matrix again.

[startup/report.json](receipts/startup/report.json) holds the separate startup
comparison. The optimized hardware rule is held constant on both sides, isolating
host-session reuse. Two fresh public resolutions took 78.439 + 80.042 = **158.481 s**;
the shared session producing both modes took **83.127 s**. This is one bounded
same-process phase measurement, not a campaign performance guarantee. Both baseline
resolutions traverse the full 133-job corpus (266 admissions total); the new session
control counted exactly 133, unchanged after both selections and all drift controls.

| Shared session phase | Seconds |
|---|---:|
| Selector | 0.000278 |
| Common records, approval and source checks | 0.005328 |
| Profiles and registry | 0.265620 |
| Corpus and job admission | 81.892836 |
| Both mode receipts and binaries | 0.014114 |
| Immutable state preparation | 0.166988 |
| Two mode materializations and rehashes | 0.782028 |

Read timing is a subset of those phases, not additional time: 92 common reads,
135 corpus/inventory/job reads, two profile/registry reads and 18 mode reads.
Two selections rehashed 239 unique bound file identities each (478 reads, 0.283476 s).
The corpus phase's reads took 0.220690 s, so this measurement attributes its dominant
cost to validation, not filesystem hashing. Timing markers change only instrumentation;
their exact source is retained. An independent unprofiled control measured 82.456 s
common setup, 0.672 s for both selections and 0.695 s for a case constructor. The
fresh candidate public debug resolver also passed independently (82.504 s).
Peak process RSS across the whole startup/profile/control experiment was 149,728 KiB
(146.2 MiB); this is not retained-session-only memory or B's worker budget.

These measurements do not reconcile B's earlier reported 556.93 s setup or the
coordinator's separate batch timings. B owns its exact combined startup/processing/
total and worker-resource comparison. No parallel initial validator is proposed:
common reuse removes one full traversal without introducing a competing worker pool.

## Discriminating checks and honest evidence lineage

Frozen plans/tests precede their respective source corrections; all intermediate
receipts remain. [public-equivalence.json](public-equivalence.json) compares 33 exact
baseline/corrected public refusal and operational records, including causes/messages.
Controls include malformed/noncanonical external requests and outputs, duplicate keys,
foreign/stale/rehashed outputs, mutated nested dict/model/model_copy, different engine,
profile, registry and permitted-job anchors, path changes, limits and restored positives.
No arbitrary exception is accepted as the expected refusal.

- The initial baseline discriminates the removed admissions and absent case API.
  Actual scratch source reversion/restoration repeats nine versus one admission for
  three replays, with the same output signature. The final case suite includes
  before/during authority mutation, wrong mode, reentrancy, expiry/PID, argument
  overrides, second/final output corruption and a genuine release context constructed
  without executing it. Late malformed engine anchors (`None`, dict, object) initially
  differed; the guarded runner now matches all three baseline EngineIdentityMismatch
  outcomes exactly. See `receipts/authority-before` and `receipts/final-guard`.
- Rule equivalence covered 11,630 checks, ordered/live rule edits, labels, add/remove,
  160-pattern churn, invalid paths/types, Unicode indices, wildcards and newline edges.
  Actual baseline/corrected/reverted/restored warm regex preparation counts are
  1/0/1/0. The bounded cache stayed at or below 128. Serialized HardwareSpec and all
  committed mapped schema mirrors agree in `receipts/rule-controls-v2`.
- Startup controls cover independent emitted graphs, mutation isolation, invalid mode,
  closed/PID-mismatched selection, exact selector drift, and 14 bound-byte faults:
  HostRecord, approval/review/trust, registry/profile/source, corpus/job membership,
  individual job, cross-mode receipts/binaries and changed release binary. All refused
  at the original bound-digest check; restored originals passed. These are explicit
  read-fault injections after the original open checks, never root-file edits or
  positive capabilities manufactured from altered data. Six public-resolver negatives
  independently match baseline and candidate type/message in `receipts/peer-join`.
- B's `f7bb6ef` note identified missing-profile `KeyError` before the intended case
  refusal. A froze the condition, added an explicit presence check and ran actual
  before/corrected/scratch-reverted/restored sources. Results were KeyError / declared
  ValueError / KeyError / declared ValueError, all with zero transports. After each
  restoration, three saved replays passed exact canonical/receipt/checker comparisons.
  Corrected/restored runner is final `ce82a76e…`. See
  [peer-join/report.json](receipts/peer-join/report.json).

Failures are retained: initial nested engine snapshot serialization TypeError;
obsolete measurement intentionally terminated (137); an incorrect test expectation
for an engine-version literal; a test-only tuple/list schema comparison; and the
malformed-engine/missing-profile refusal mismatches corrected above. Test expectation
fixes follow installed baseline behavior, not weaker acceptance. Earlier timing runs
remain separate and are not pooled into the final comparison.

The human lint fix `a887a1d` to previously published harnesses is preserved. Exact
original executed bytes are archived as `.py.txt` under `historical-tests-first` and
`historical-harnesses`; [historical-test-provenance.json](historical-test-provenance.json)
binds that distinction. Run reports identify the actual harness/source hashes used,
including inherited original runtime-manifest fields; a copied historical preflight
status is not a newly executed preflight claim. Private caches/sources stay outside Git.
Published receipts contain no fabricated native result.

[static-checks-final.json](static-checks-final.json) records final strict mypy, Ruff,
candidate formatting, each separate patch plus combined application and exact postimages,
unchanged live preimages and saved sample bytes. The final runner and host AST receipts
verify unchanged transport/result-validation/signatures and original resolver checks.
[handoff-checks.json](handoff-checks.json) validates receipt/test/source hashes, local
links, arithmetic and current selected support. Historical checks remain pinned to
their actual older inputs. No broad native suite was rerun for this proposal.

## Recurring development and remaining joint decision

Use focused unit/boundary tests without host resolution for unrelated development;
use affected public/case/session controls for changes to these boundaries. B prepares
the exact existing-selector commands: fast saved validator/checker smoke is eight
debug repetition-0 results; broader saved regression is all 133 cases × both modes ×
repetition 0 and refuses missing release evidence. These omit host admission and
cannot issue full-campaign receipts. Runtime/authority/transport or repetition changes
need their corresponding affected tests and the broader selection; quick checks never
replace required gates. The complete first-use path retains all **133 × 2 × 3 = 798**
fresh native slots, per-result checks, six-way comparisons and replay/refusal obligations.
Its restart remains held. No new test framework or CI/U0024 policy is introduced.

[identity-and-lifecycle.md](identity-and-lifecycle.md) and
[identity-audit.json](identity-audit.json) trace the concrete edges. All three paths
are accepted BuildInputs source entries and sealed runtime files; hardware.py is also
in the 56-file selected support closure. None is in the four-file Rust model subset.
Full BuildInputs determines implementation identity, so direct replacement under
`/candidate` fails the genuine resolver and B's origin/layout checks. Equal schemas or
result bytes cannot waive protected support/adoption requirements.

The proposed runtime-only route retains the exact original native build tree, binaries,
engine identity, jobs and authority, and separately binds the three Python postimages
plus B's helper and pinned runtime into a newly reviewed closure with explicit distinct
roots/origin checks. B owns the concrete combined helper/placement delta; the coordinator
and human must accept that separation and protected hardware/support lifecycle before
installation/execution. If unified build/runtime identity is retained, changed source
entries instead require later reconstruction and rebinding. Neither route is installed
or presumed authorized here. Exhaustive reads remain unclaimed.

B's initial `2ef246a` private join and its later `d0a99bd` startup preparation are
inherited peer evidence, not final `ce82a76e…` qualification. Its ordinary missing-profile
finding is resolved and exact final source/API is published for the combined join.
The substantive remaining work is B/coordinator combined measurement/runtime binding
and the human installation/support decision. Stop here for that reconciliation; no
campaign restart, native rebuild, root installation, artifact adoption or closure claim.
