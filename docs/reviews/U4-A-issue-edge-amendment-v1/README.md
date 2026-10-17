# Complete unapplied DMA issue-edge amendment

This package proposes the contract, independent checker, native and CI identity changes
needed to represent a DMA credit reservation before its receiving core edge. It does not
install any of those changes. All implementation and protected edits were tested only
in private exports. The live clone contains this review package only.

The baseline is published candidate `64837bea3724919facbc27be1c7f5644a6354cfa`, integrated
through B audit `0e9996a` and reconciliation
`e259d2d8f2f0389e14bdb92a3a2cc5ec056ab1ea`. Human installation
`3949b104d0eaae95a7452f976c2afa048fa82ff1` is an ancestor. Its installed strict-wait
credit-cause rule is preserved. Neither development approval nor this package supplies
new execution authority.

[manifest.json](manifest.json) is the exact amendment identity: three patches, 20 file
preimages/postimages, apply/reverse checks and historical byte controls. Apply all three
patches only to a disposable export for review. Their combined postimages were verified
in `/tmp/u4-issue-amendment-apply`; no protected live file was installed.

| Patch | Exact content |
| --- | --- |
| [contract-and-export.patch](patches/contract-and-export.patch) | U0011 appendix; typed /3 activity, queue and DMA carriers; model-version admission; mapped job/result schema mirrors; structural validator and tests; explicit native schema exporter modes |
| [checker-and-identity.patch](patches/checker-and-identity.patch) | Separate /3 checker, transition and reservation checks; independent literal tests; required additive installation identity overlay and guard tests |
| [native.patch](patches/native.patch) | Typed model/observation seam, pending/acquired state, issue phases and accounting, strict /3 native snapshot, nine focused Rust controls |

The native patch is based on the same six unchanged native preimages at candidate
64837bea and reconciliation e259d2d. The shared exporter belongs only to the first
patch. No patch is silently installed by copying this package.

The proposed version boundary is `native-intervals` model **2** with
`uarch-native-observations/3`. Fixed-delay model 1 / observations 1 and component model 1
/ observations 2 remain explicit old paths. Protocol `uarch-engine/3`, input graph,
`U0011-stage2/1` admission and profile/2 promises remain unchanged. This is an additive
output/model version, not a reinterpretation of historical inputs. `/3` and model 2
must match; the old native seam rejects model 2 and the new seam rejects model 1. There
is no new public flag, authority selector or Python-prevalidated execution path.

The exact proposed laws are in the U0011 patch. Their operational endpoints are:

| State | Credit occupancy | Explicit ledger interval |
| --- | --- | --- |
| Waiting | none | job readiness → reservation |
| Pending | one reserved slot, not acquired | reservation → core issue edge |
| Acquired/inflight | one acquired credit | issue → commit/ack completion |

Pending plus acquired cannot exceed capacity on each independent DMA engine. Grants
reserve the earliest available slot in `(job readiness, request ID)` order. At
`next_edge(core, reservation, 0)`, conversion from pending to acquired is atomic; it
neither doubles occupancy nor frees a transient slot. There is no finite same-edge
issue-rate cap. Shared payload-port service remains a separate mechanism.

Every fragment has a nonoccupied `dma_issue/alignment` and zero-duration
`dma_issue/service`, with the DMA engine owner, memory attribution and core clock.
All four endpoints and all three ledger rows remain explicit even when duration is
zero. Positive scheduled completions use phase 0 before phase 2 grants. Existing inline
zero-duration endpoints, including write ACK, remain phase 2 and must precede any grant
they enable by observation ordinal. Conversion precedes transfer service. No issue busy
interval, transfer boundary or completed traffic is invented.

Credit attribution requires **reservation > job readiness**, actual prior saturation
and a tight release by acquired work on the same engine. Readiness equal to release
has dependency-only attribution; later alignment does not turn it into credit waiting.
DMA job start is its earliest reservation, and nonpersistent producer allocation starts
there. Allocation does not imply data production. Terminal-reader completion remains
the free endpoint; retained outputs without terminal readers keep `free_ps: null`.
@1 persistence and @2 exact producer/all-terminal-reader rules are preserved.

[Independent expectations](independent-expectations.json) bind B's unmodified published
arithmetic and the additional prospective controls. The read and write gap reserve at
26,667 ps, issue at 27,000 ps and complete at 86,000 ps. Read memory/NoC/sync attribution
is 51,749/7,584/26,667 ps; write is 52,082/7,251/26,667 ps. The cap1 pair issues at
27,000/86,000 ps and completes at 86,000/146,000 ps. The cap2 pair issues together at
27,000 ps and completes at 86,000/89,000 ps. Two cap1 engines independently allow the
same issue pair while retaining shared-port contention. An original three-request cap2
probe is retained separately; it was not rewritten into the pair.

At release 60,000 ps on a 1 GHz core, readiness 59,999 gives credit-only attribution;
readiness 60,000 gives dependency-only; readiness 60,001 reserves immediately and issues
at 61,000 with dependency-only attribution. Both zero-alignment boundary cases are
explicit. Native controls allow 33 same-edge issues; the independent checker separately
checks 66 reservations across two capacity-33 engines. Native exact-boundary state
controls are labeled typed synthetic tests; they are not claimed as independently
admitted mapped inputs. Full mapped probes are stored separately under
[private-probes](private-probes).

The A-authored independent checker proposal imports neither native execution nor the
carrier validator. It verifies earliest reservation from actual observed completion
witnesses, checks the core edge independently, and preserves the installed mechanism,
traffic, lifetime, complete-inventory and causal checks. It does not calculate an entire
workload's makespan or substitute expected rows for observations. Old `/2` checker files
remain byte-identical. B's arithmetic is independent prior evidence; B has not yet
reviewed this new checker implementation or exact CI transition.

The observed test evidence is bounded:

- Test-first schema controls: four behavioral failures and one old-version pass; the
  implemented carrier controls passed. Independent literal controls: six initial
  behavioral failures, then six passes. The original CI identity test refused the new
  ADR before the explicit transition was added.
- The affected mapped-contract run had 172 passes and one exact legacy refusal-text
  failure. The text was restored and that test passed. The final 34-check selection
  covers new schema/model tests, independent literals, exact installation identity,
  historical selection binding and that restored refusal. Ruff passes for 10 files,
  strict mypy for six source files, mapped schema generation and all three native
  snapshot checks pass. No historical selection was skipped or rewritten.
- Native affected component tests passed 37 in debug and release before the final
  endpoint-bound change, with two explicit exporters ignored. The final frozen source's
  nine proposal controls pass in debug and release. The /3 bound is conservatively 28
  endpoints per sequence; /2 retains 24. The capacity control uses a labeled typed
  synthetic state, not an admitted workload.
- Twelve private full mapped outputs passed both the proposed validator and checker.
  Their exact producing source hashes are in native receipts. They were produced at
  the recorded intermediate revisions; subsequent changes were test/formatting and
  the conservative event bound. They are not relabeled as a final-source campaign.
  Five newly authored controls also match the literal assertions above.
- Six final native guard faults fail and exact restored source passes. Ten malformed
  output controls are refused by both consumers, with baseline/restored passes. These
  are separate evidence classes: a structural early refusal is not claimed as a
  particular later guard's kill. Legacy C02/D01/D02 full output bytes are asserted.

[evidence/final-python-checks/receipts.json](evidence/final-python-checks/receipts.json)
and [native-report.md](evidence/native/native-report.md) describe commands, scope and
identities. Executed recipe bytes are preserved as `.py.txt` evidence, with a packaging path map.
The evidence retains failed development attempts, including a wrong test
premise about zero ACK phase, an empty-terminal-reader endpoint mistake in the draft
validator, and a test harness attribution-key error. Earlier fault/restoration attempts
reused stale Cargo executables despite restored source; those failed outputs are
preserved and excluded. Corrected final faults explicitly recompiled in an isolated
target; corrected mapped probes used a fresh target.

Rust checks used the accepted offline image
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`, accepted tools,
unchanged lock/features and accepted cache. All 1,719 cache files were reverified. Python
checks used the existing Lane A environment, recorded separately. No dependency was
installed or added. Private unit executable hashes identify test artifacts; they are
not a public BuildInputs/HostRecord or a reproducible component executable claim.

Installation must be one exact reviewed transition: protected ADR/contract/schema/tests,
B-owned /3 checker and CI overlay, and A-owned native/exporter bytes. The original
`installation-binding.json` and 106-case selection remain immutable. A separate required
`issue-amendment-binding.json` pins six exact replacements and six additions on top of
that historical binding. Its guard checks exact inventories, preimages, postimages,
old ADR prefix/suffix and the new appendix. The package manifest pins this new binding;
the binding pins the helper and tests, without a self-hash cycle or optional fallback.
The selected 56 U0002 support files and dependency manifests are byte-identical. This
comparison does not expand dependency-source acceptance or establish construction-read
closure. New source/model/checker identities need explicit prospective joins, not an
inherited fixed-delay or candidate04 runtime identity.

The following decisions remain outside this package:

1. B review of these exact checker and CI postimages, the reservation/ordering law and
   prospective control selection. A published an initial peer request at `1bd0ea9` and
   this package supplies the concrete batch. The available session tools cannot reach
   the separate B session; no direct B response or approval has been received. Prior
   B arithmetic and audits must not be represented as acceptance of this amendment.
2. Exact human approval/installation of the protected amendment and version choice.
   No human worksheet, protected live file or sealed original root was edited.
3. Later authorized component source/build/root placement and HostRecord, selector,
   profile/registry and public campaign bindings. All current successful runs are
   private synthetic tests. Public entry points remain unchanged and unauthorized.
   The existing refusal-only D3 transport proposal still needs exact authorization:
   finite immutable raw negative-case IDs must exercise native semantic refusal
   without a positive-loader bypass or self-authorizing hash. Absent/wrong authority,
   model/version mismatch and stale/wrong observation bindings remain required public
   negative controls, not public tests claimed by this package.
4. Existing construction/read-audit gaps remain: two unknown debug syscall records and
   one unfinished release `sched_getaffinity`. No trace build was repeated and strict
   coverage remains unaccepted. Public replay/first use, genuine L1 workings,
   U-P11b phase-B acceptance, U4/G3a closure and performance qualification remain open.
   H-L1-GEMM-01/H-L1-DMA-01 need human workings. Generic spill/traffic monotonicity remains
   R if consumed there, otherwise T; decoder/RoPE/KV/casts/steady-priming, reference
   precision, mesh and broader product/FP8/ragged scope stay deferred under the existing
   phase-B limits. No R/TPU run or fabricated L1 result is included.
