# U0006 proposal: what analytic verification can and cannot establish

Status: **PROPOSED; bounded Lane B preparation, not an accepted ADR.** Javid
(@jjaffari) is the acting human decision-maker for both lanes. No Reza approval,
independent review, U3 start, G2 decision or sprint exit is asserted. The human-owned
`docs/decisions/` path is unchanged.

Basis: published annotated `u02-end` peels to
`79bc1f014306e520aacba3491d60ae6c644b26a8`; accepted U0003, U0004, U0019 and U0021;
`docs/prompts/U-P6-L0-invariants-and-L0m-metamorphic.md`; build-spec §2.7;
execution-plan U3/G2; the actual U2 protocol and analytic implementation. Historical
prompt wording does not create fields that the accepted protocol lacks.

## Proposed rationale

L0 and L0m can find contradictions and broken relations within the declared model.
L1 checks limits; L2 compares compatible abstractions. None supplies silicon
observations. Agreement with oneself or another simulator does not establish
hardware accuracy, an error distribution or confidence intervals. L0–L2 alone
leave model evidence at **stub**. U0004's stipulated conditions, worst real claim,
proposed-design ceiling, unknown error and separately unverified energy remain
settled policy, not new approval questions.

A successful test means its named relation held over its executed domain. A skip
means it was not tested, with a reason. A failing observable invariant is a finding,
never a warning or automatic scope waiver. Byte identity proves reproducibility,
not correctness. A content hash authenticates content identity, not human approval.

## Actual engine matrix and input boundary

| Engine / mode | Accepted seam | Bounded local coverage | Remaining boundary |
| --- | --- | --- | --- |
| U-C0 aggregate | `EngineJob` → `EngineResult`, `uarch-engine/1`, `resolved-ops/1`, `physical-resolved` model version 1 | Fixed BF16 independent decode/prefill work; generated hardware rates; aggregate roofline and invariants | No event/resource observations |
| U-C0 per_op | Same seam, serial sum of isolated operator rooflines | Same fixed work, bounds, counts, attribution, determinism, memory response | Whole-query reciprocal clock scaling needs a stronger premise |
| Fork | Not representable by current `EngineIdentity.name: Literal["analytic"]`; no runnable adapter in this baseline | **Not run**, not a dummy analytic alias | Lane A and human-owned schema decisions, pinned image/adapter and G2 same-work evidence |
| Native | No accepted runnable implementation here | **Not run** | Later authorized work; no native test assertion is fabricated |

Both current modes accept `mapping_scope=analytic_ops`, `analytic-ops@1`, fidelity
compute/NoC/DRAM 0 and exact synchronization; `state_model=stateless_roofline`.
They receive resolved operands, dimensions, repeats and hardware peaks. They do
not receive a detailed placement/TaskGraph, queue statistics or cycle trace.
`per_op` is a pricing decomposition, not a timed execution trace.

`validation/strategies.py` reads the existing independent synthetic d4 fixture
without editing it. All varied hardware numbers remain sourced **stub claims with
source null** in a synthetic reference spec; these are not proposed real hardware
facts or approved design stipulations. Generated core frequency is 1 MHz–2 GHz,
BF16 MAC and vector rates 1–64 per core cycle, DRAM bandwidth 1,000–10^12 bytes/s;
geometry, capacity, model and BF16 storage are fixed. The memory-bound branch uses
1,000–10,000 bytes/s. These ranges explore arithmetic, not physical plausibility.

Fixed-work tests validate the complete prepared bundle, bind current physical
assumptions/model identity, resolve hardware and authenticate the job through the
accepted preparation seam. Changing hardware updates its spec hash, intent hash,
bundle hash, reconstructed request hash and job hash. Point hashes and graph bytes
remain unchanged. No runtime engine mutation or hidden producer call is permitted.
Saved JSON replay disables the standalone producer. Separate refusal regressions
exercise stale hashes and a rehashed positive-dimension graph that contradicts the
supplied model; both must fail without re-preparation.

Producer checks live separately in `test_analytic_frontend.py`. They explicitly
regenerate standalone graphs for batch 1–8 or context 1–64, then compare against a
doubled axis (up to batch 16/context 128), updating envelope and grid. Those checks
cover the combined producer/engine path; they cannot be cited as engine invariants
on unchanged work or independent proof of every producer count. Existing U2
physical count, rank, half-byte, precision and replay regressions remain required.

## Relations, preconditions and explicit non-coverage

| U-P6 relation | Observable analytic check / disposition |
| --- | --- |
| MACs executed equal graph MACs | **Executed conservation skipped.** Prepared graph has operand shapes, not an independent executed-MAC counter. `Counts.matrix_ops` counts two ops per MAC. This preparation checks independent literal fixture counts plus per-op/total reconciliation; it does not rename them execution telemetry. |
| DMA conservation | **Skipped.** Operand read/write bytes are modeled traffic under once-per-operand/no-retention assumptions, not DMA measurements. The prompt equation needs a defined boundary; see decisions below. |
| Utilization ≤1 over every window | **Skipped.** All busy-time/diagnostic fields are null. Ratios of roofline demands are not window utilization. |
| Little's law within 1% | **Skipped.** No queue observations, arrival rate, residence distribution or stationary observation interval. |
| Timed causality | **Skipped.** Dependency validation is structural; `trace` is null. |
| Byte-identical reruns | Executed for both modes and both fixed points, including hashes, with unchanged jobs. Saved file replay also executes with producer disabled. No thread/worker scalability claim. |
| SRAM occupancy at every event | **Skipped.** No placement/events; partial weight/KV capacity checks are not peak SRAM occupancy. |
| Attribution sums to duration | Executed in protocol picoseconds with 1e-9 relative tolerance and no absolute tolerance for these nonzero fixtures. Same relation after unit conversion. Zero unrepresented critical-path contributions are legal; they are not measured zero utilization. |
| Energy conservation | **Skipped.** No energy value exists in `EngineResult`; energy remains unverified. |
| Unmodeled diagnostics null | Executed for all accepted diagnostics and busy-time fields, plus null trace/simulator metrics. |
| DRAM bandwidth ×2 never slower | Executed with identical prepared work/counts. A companion memory-bound check requires every operator remain memory-bound after doubling and then requires duration ÷2 (1e-9 relative). This catches reading an unrelated constant field, which monotonicity alone would miss. |
| NoC/SRAM bandwidth ×2 | **Skipped.** These bandwidths are unrepresented. Unchanged timing cannot verify their model. |
| Core clocks ×k | Executed for aggregate, k=2–4, fixed nominal-frequency points and non-scaling DRAM/NoC, high fixed bandwidth 10^18 bytes/s. Post-change compute-bound premise is checked. `per_op` exact whole-query relation **skipped** because embedding is memory-only. |
| DRAM-bound clock response | Deferred as a separate relation. Proposed precise form: unchanged duration if all priced terms stay memory-bound and DRAM service rate is unchanged; do not use ambiguous “changes by less than k.” |
| Decode batch/context non-decreasing | Executed on the separately labeled standalone producer path, BF16, tp=1, fixed model/mapping policy/fusion/precision/hardware. No arbitrary imported graph monotonicity claim. |
| Core-ID symmetry / idle core | **Skipped.** No placement/core IDs; all spec cores enter resolved peak. Increasing core count cannot be described as adding an unused mapped core. |
| Untouched stipulated parameter | Deferred, visible skip: the generated reference fixture has no stipulations. No blanket invariance claim across re-preparation. |
| Latency increases / fewer outstanding DMA | **Skipped.** Neither latency nor request concurrency enters U-C0 timing. |
| Cold never faster than steady | **Skipped.** Accepted stateless equality is absence of a history model, not verification of warmup or steady-state behavior. |
| Additional accepted analytic relation | Both modes preserve counts and per-op predictions, and `per_op.duration_ps >= aggregate.duration_ps` for the same point/hardware. |

The independent fixed-count tuple is `(matrix_ops, vector_ops, reads, writes)`:
decode `(1184, 572, 1296, 288)` and prefill `(672, 252, 1040, 288)`. The prefill
point has one token and T=1 instead of T=17: the two repeated attention operators
remove 512 matrix ops, 320 vector ops and 256 read bytes; writes remain unchanged.
These expectations are integer arithmetic over the fixed supplied graph, not calls
to `_counts`, `prepare` or the nominal compatibility oracle.

## Discrimination plan implemented in this preparation

`validation/mutants/analytic.py` injects five independent test-only faults. It never
registers another production engine. Returned objects conform to the accepted
carrier and have refreshed result identities; a stale hash alone cannot kill them.
Valid controls and mutants use the same named assertion. Each parametrized test
runs 24 deterministic Hypothesis examples per mode; failures must be
`AssertionError` with the corresponding mutant name, not incidental exceptions.

| Mutant | Fault | Required rejection |
| --- | --- | --- |
| `off_by_one_matrix` | Adds one MAC (two matrix ops) to an operator and reconciles the total | Fixed independent count expectation |
| `double_attribution` | Adds the full duration to overhead attribution | Attribution conservation |
| `zero_unmodelled_diagnostic` | Replaces null compute busy time with zero | Null diagnostic rule |
| `nondeterministic_output` | Adds a changing observation string to successive results | Full canonical result byte identity |
| `wrong_bandwidth_field` | Prices memory with vector throughput, retaining the original external job binding | Memory-bound bandwidth response |

These are bounded result/input fault wrappers, not proof against all possible
implementation defects. The nondeterminism wrapper changes metadata; it does not
exercise thread races. No queue-drop or SRAM-allocator mutant is committed because
U-C0 cannot expose the corresponding observation. Every committed mutant is marked
`nightly` but is explicitly run locally here. Local execution does not meet the
self-hosted nightly requirement.

## Report and version binding proposal

Keep the accepted carriers: `VerificationRecord` (`uarch-verification/1`) has rung,
purpose, outcome, scope, model_identity_hash, source_hash, review_hash and
verification_hash. `ModelCard.verification.L0/L0m` are content-hash references;
`ReportContext.verification_hashes` and the existing artifact/review closure must
bind the same records. Do not create a second evidence ledger or set card hashes
from an unreviewed pytest summary.

Proposed report source content must record each named relation's pass/fail/skip
and reason, actual example budget/domain and mutation outcome, fixed or producer
input path, both modes, exact engine/model implementation identity, protocol and
accounting version, assumptions, precision/rank/state scope, bundle/job/result
identities for retained cases, suite revision and Hypothesis version/settings.
A report must reject a claimed different engine/model version even if semantic
version strings match. Mutant controls are separately labeled and cannot be
promoted to engine evidence. A skipped relation contributes no positive result.
Use canonical JSON and content hashes for these reproducibility artifacts; exclude
wall-clock times, temporary paths and host-specific test durations from stable
content. Keep operational host/nightly receipts separate.

This task emits a local pytest JUnit receipt only. It does **not** implement the
proposed stable source payload, review it, attach a VerificationRecord or change a
model card. JUnit contains elapsed times and is not hash-stability evidence.
Stable report reruns, version-mismatch rejection and public card/report integration
remain future acceptance checks, after the exact source-content semantics and
scope are reviewed. This proposal does not expand public schema.

## Concrete decisions left to Javid / contract owner

1. Accept or revise the U0006 rationale and capability-scoped wording before a
   human commits the ADR. Proposed wording: “Check executed MAC/traffic conservation
   only where independently observed execution counters and corresponding prepared
   work exist; report analytic shape-accounting verification separately.” The
   current graph has no independent execution counter; do not silently claim it does.
2. Resolve the DMA equation's control volume before trace-engine tests. “DMA bytes
   moved in = compute consumed + written back” is generally not conservation:
   newly produced outputs need not have been transferred in, and resident/reused
   data changes traffic. Proposed obligation: direction-specific issued/completed
   transfer conservation including explicitly defined initial/final in-flight and
   resident inventories; compare compute accesses only under a declared residency,
   fusion and reuse policy. Exact observations belong in a human-approved protocol
   change; no queue/trace/placement extension is implemented here.
3. Approve/refine the precise clock premises above and stationary queue observation
   semantics (including finite-window boundary terms and zero-flow cases) before
   treating those future relations as universal. A failed premise is an explicit
   non-applicable relation, not a tolerance waiver.
4. Settle the exact canonical report source payload and scope aggregation under
   existing VerificationRecord/review closure. Partial analytic checks cannot set
   a blanket “all L0 passed” claim. Fork/native identity and diagnostic extensions
   require coordinated Lane A proposals and human contract decisions, not a private
   B adapter that pretends the analytic-only schema supports them.

No production semantics, protected file, adopted input or public schema changes
are proposed for this bounded commit. U0002 strict support currentness remains in
force; changing a bound input still needs human generation/adoption.

The designated host is `javid@152.53.209.203`; administrator Reza is unavailable,
container installation pending, runner state unverified and nightly paused. No
host/runtime/gate waiver exists. Remaining work includes the authorized host setup,
actual green self-hosted nightly, fork matrix execution with preserved same-work
G2(c) counts, independent review, report integration and all joint exits. This
preparation authorizes none of those actions and closes none of those gates.
