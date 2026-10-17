# B review of A's exact issue-edge amendment

The final-source evidence gap is closed for the twelve selected mapped probes. One new
ordering disagreement remains: **B-ISSUE-ORDER-01**. The exact proposal is not yet coherent
across native scheduling and the independent checker. This is author verification and
peer reconciliation, not independent adversarial acceptance or installation permission.

The subject is A's published package `ddd299ca59a27098da9ce4de1359d43f966aab20`,
`docs/reviews/U4-A-issue-edge-amendment-v1/`. B integrated that commit normally. The private
source is base `e259d2d8f2f0389e14bdb92a3a2cc5ec056ab1ea` plus these patches in manifest order:

| Patch | SHA256 |
| --- | --- |
| contract-and-export.patch | `b8d51372323bc948f77284cab363c50d645af8428b70de36e4bfa726ff71da80` |
| checker-and-identity.patch | `8e14e7db11398973ddde5ff2fa6c180c74ea653b39ca9dfa8b5c2428006e66c1` |
| native.patch | `a1be64f5dfa7ddc4c321bb52533465dd5987604686ed647a40d08996f8e97ad3` |

[reconstruction.json](reconstruction.json) verifies all 20 preimages/postimages (11 modifications, nine additions), ordered
apply checks, reverse checks, and nine historical byte controls. A's package verifier
also passed: 366 artifacts, three patches, twelve private joins. Its successful joins
are inherited evidence; B's executions below establish the final-source result evidence.

**Implementation finding — B-ISSUE-ORDER-01 (must reconcile before installation).**
Start from A's exact `gap-cap1` job. Preserve all tasks, buffers, routes, hardware and
policy choices. Change dependencies to `a-unicast → b-barrier` and `a-unicast → r00`;
`r01` is initially ready. The existing unicast has zero hops and completes at 0 ps.
Rebind graph/point/profile/bundle/job hashes under an explicitly synthetic private profile.
[inline_ready_probe.py](inline_ready_probe.py) constructs this input and the paired control.
It passes the proposed job carrier and component completeness checks, then reaches real
Rust admission, execution and result construction in both final binaries.

| Case | r00 reservation/issue/complete (ps) | r01 reservation/issue/complete (ps) | Structural / independent |
| --- | --- | --- | --- |
| r00 becomes ready through inline unicast | 60000 / 60000 / 120000 | 0 / 0 / 60000 | pass / `earliest reservation / ready tie` refusal |
| Paired control: r01 becomes ready through inline unicast | 0 / 0 / 60000 | 60000 / 60000 / 120000 | pass / pass |

Both job-ready timestamps are 0 in both cases. Native `Runtime::reserve` reserves the
initially ready request before executing the inline zero-hop predecessor. The checker
sorts the entire observed population by `(ready_ps, request_id)` and therefore expects
r00 first in both cases. This is a behavioral disagreement, not a hash/profile refusal
or an invalid raw input. Full debug/release output bytes agree for each case.

There is also an observation constraint on a checker-only fix: the reservation state
change is not an event with its own ordinal. In the failing output the unicast dispatch /
completion ordinals are 0/1, while r01's first issue-alignment ordinals are 5/6. Reservation
actually happened before the unicast; using the alignment dispatch ordinal as reservation
order would invent a different history. Merely disabling the recurrence, accepting any
current order, or changing the expected tuple is not a correction.

**Correction proposal for A.** Reconcile the exact meaning of an eligibility opportunity.
The appendix's operational “at each actual eligibility opportunity” rule supports the
current native result, whereas a timestamp-wide ready/request tie supports the checker.
The narrow choices are (a) preserve actual eligibility and supply/check an exact
reservation-order witness, including inline dependency completion, or (b) explicitly
require zero-time dependency readiness closure before credit reservations and implement
that ordering in the private native proposal. B prefers preserving the stated actual
eligibility rule; the witness must distinguish the two epochs at the same timestamp.
A should return one exact amendment with the chosen law and the paired mapped regression,
plus a forgery that swaps an ineligible request into the earlier epoch. Keep strict-wait
credit causes, capacity and ready/request ordering among simultaneously eligible requests.
No production source or protected amendment was changed here; no A correction or agreement
is represented as received. This published note is the concrete peer handoff.

The exact reproduction inputs/output hashes and commands are in
[inline-readiness-finding.json](inline-readiness-finding.json) and
[inline-readiness-control.json](inline-readiness-control.json). These two cases are new
prospective synthetic fixtures, not edits to any historical fixture or expectation.

**Contract assessment, separate from that implementation finding.**

- The additive `native-intervals` model 2 / `uarch-native-observations/3` boundary is explicit.
  Model 1 / observations 2 and fixed-delay model 1 / observations 1 remain separate.
  The typed native seam refuses both cross-version inputs before execution. Python model
  and result controls pass. Protocol, input graph and profile/2 promises are unchanged.
  No public selector or executable invocation bypass was added.
- Pending plus acquired occupancy is bounded per flattened DMA engine. The capacity-one,
  capacity-two and independent-engine mapped cases agree with B's prior arithmetic.
  Pending conversion removes the reservation and inserts acquired state within one
  transition, without another reservation opportunity between those operations.
  Payload-port service remains independently contended. No issue rate cap is introduced.
- Positive scheduled completions precede phase-2 grants. Inline zero-duration endpoints
  remain phase 2 with earlier cause ordinals. Explicit zero alignment and zero service,
  the three distinct ledger populations and null ledger clocks are present. Ordinary
  activity clocks remain core clocks. Neither issue activity creates resource busy time.
  The new ordering finding concerns readiness arising *inside* phase 2, not phase-0 order.
- Strict credit causes use reservation time, actual prior saturation, a tight same-engine
  acquired release and reservation strictly later than job readiness. The unchanged
  59999/60000/60001 ps boundary literals are supported by the focused native read/write
  controls and independent checker units. Alignment delay alone is not credit waiting.
- Job/allocation starts follow reservation; producer allocation does not imply produced
  data. O2 remains genuinely transient: bacc allocates at 547000 and frees at 2188000 ps,
  after both final consumers; total duration remains 2735000 ps. @1 persistence remains.
- Read/write gap reservation/issue/completion are 26667/27000/86000 ps. Read attribution
  memory/NoC/sync is 51749/7584/26667; write is 52082/7251/26667. The exact channel duration
  is `256 * 8 * 78 / 71 = 159744/71 ps`, derived from the declared channel bandwidth and
  refresh factor. All intermediate phase endpoints match B's pre-amendment literals.
  The evidence checks mechanisms, not just a makespan partition.

**New execution and discrimination evidence.** Fresh empty debug/release Cargo targets
used the accepted offline image, toolchain, lock/features and cache; all 1719 cache files
were reverified. No intermediate executable was reused. [build-bindings.json](build-bindings.json)
contains source inventories before/after the explicitly added cfg(test) B harness,
compiler commands, monitor limits and exact artifact hashes. The executable hashes are:

| Mode | Final patched source's private unit binary SHA256 |
| --- | --- |
| debug | `d6bb6b62c94535e8611911008783ba68e08fdc1f5699f19fd73396ff72cf6225` |
| release | `14047d9074a20bfc643d0e86966ad4452837ebb1574be226dcf59b0ec20e75a9` |

The twelve mapped cases C02, D01, D02, D07, D14, O2, issue-gap, gap-write, gap-cap1,
gap-cap2, gap-cap2-pair and gap-independent ran once per mode: **24 fresh private
processes**. All reach Rust admission/execution, pass both Python consumers, match B's
applicable unchanged literals and match A's twelve recorded intermediate results in full.
The two inline-readiness cases add **four** focused processes. No native full selection
or trace build was repeated. Source is not mounted into the executing probe containers.

The nine focused proposal tests pass in each final binary, including three historical
full-result byte controls, version refusal, typed strict-wait/capacity/33-issue probes and
the /3 event bound. Typed post-admission state construction is explicitly synthetic and
is not counted as full mapped admission. A's six native guard-fault controls are inherited,
not relabeled as B-executed faults.

[consumer-controls.json](consumer-controls.json) records **15 synthetic output attacks**.
Thirteen stop in structural validation and also fail the independent checker; these are
not later checker kills. A joined duration-law forgery and a fully joined late-issue
forgery pass structural validation but fail independent mechanism checks. Their hashes
are valid, so the refusal is not an identity mismatch.

[checker-fault.json](checker-fault.json) records overlapping issue-edge defenses: removing
only the explicit edge guard exposes receiving-clock alignment; removing both exposes
clock-witness binding. Removing all three issue-specific defenses permits the 10000 ps
late-issue forgery. The valid control passes throughout and exact restored bytes reject
again. No single one of these redundant defenses is claimed individually essential.

[capacity-fault.json](capacity-fault.json) isolates the new structural capacity guard.
The forged cap1 second request reserves at 26667 but still acquires at 86000; acquired
intervals do not overlap, while pending plus acquired capacity is two. All endpoint,
clock, cause, job/allocation and ledger joins are repaired consistently to the forged times.
The intended structural capacity refusal occurs. Removing only that guard permits unsafe
structural acceptance; the independent reservation check still refuses. Exact restoration
rejects again and the valid control passes. This is synthetic output testing, never a
native successful resource-negative job.

**Identity and selected-support closure.** The original 106-case selection, original
installation binding, /2 checker and snapshots, dependency manifests and prior evidence
remain byte-identical. The exact new overlay has six replacements and six additions;
manifest → overlay → helper/tests is acyclic. There is no optional fallback or adoption
of an arbitrary current hash. Identity tests cover preserved installed K2 text, the
reviewed component suffix, exact appendix, omission/tamper and required test/helper pins.
The ADR prefix is exactly 48294 old bytes plus the exact 9474-byte appendix. All 56 selected
U0002 support files/import closure are unchanged, hash
`sha256:676b12509606b7a519d9597dc406f8fe66d141af4c86425a5baf3a2e3825358a`.
No affected support transition requires human U0002 generation. That is not permission
to install protected source. Future corrections require new prospective postimages and
bindings; historical selection/review bytes must stay frozen.

One affected Python/static batch passed **34 tests**, schema generation, all three native
snapshot modes, Ruff on ten proposed files, and strict mypy on six source files.
[python-checks.json](python-checks.json) binds commands/results. Later private capacity
faults restored exact bytes and reran only their affected valid/negative controls.
[checks.json](checks.json) distinguishes new executions from inherited evidence.

Development-only harness corrections are retained in private logs: an erroneous new
rounded-bandwidth assertion was corrected to the already-declared exact 71/78 refresh
law; an unicast row was excluded from a DMA-only literal comparison; the first inline
input omitted a required barrier participant edge and stopped in Python; the first
pending-overbook forgery retained a zero-alignment phase after making it positive and
stopped structurally. None is reported as a native/model failure or a successful guard
kill. A preliminary two-guard fault found the third defense and restored exact bytes.
[recipe-transitions.json](recipe-transitions.json) separates executed recipe bytes from
formatting and the additional targeted control; raw archives were not republished.

**Reproduction and remaining decisions.** Use pinned existing dependencies with
`PYTHONPATH=PRIVATE/contract:PRIVATE/src:PRIVATE` and explicit cwd/config. Run
`reconstruct.py /tmp/NEW`, then `build_private.py /tmp/NEW/source /tmp/NEW-BUILD`, then
`run_final.py /tmp/NEW-BUILD /tmp/NEW-RUNS`. The consumer takes RUNS, SOURCE, and a fresh
output path. The inline probe and fault recipes identify their prerequisite private
receipt paths explicitly; adapt those paths to the newly reconstructed run, never a live
source tree. Raw private evidence is hash-bound in
[private-receipt-inventory.json](private-receipt-inventory.json). No build/runtime authority
or cross-build reproducible public executable is claimed by a unit-binary hash.

A must reconcile B-ISSUE-ORDER-01 and publish exact corrected postimages before a coherent
candidate can be handed onward. Human approval of the version/semantic amendment and
protected installation remains pending. Actual human H-L1-GEMM-01/H-L1-DMA-01 workings,
public build/root/runtime/profile/registry/selection bindings and the refusal-only D3
mechanism remain separate. Old K2 authority cannot authorize these component outputs.
Historical D13 and its separate corrected prospective fixture are untouched. TPU's 70-row
proposal and reference readiness remain separate; no measurement or reference access was
performed or made prerequisite to bounded model work.

The prior read audit remains limited by `debug.trace.450:11`, `debug.trace.452:9` unknown
syscalls and unfinished `release.trace.482:10` sched_getaffinity. No trace was captured or
rebuilt and full construction-read closure remains unaccepted. There was no protected
live installation, runtime placement, public component execution, authority change,
artifact adoption, qualification, U-P11b acceptance, or G3a/U4 closure.
