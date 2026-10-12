# Lane B verification readiness under U0005

Assessment and proposed tests, **not execution evidence, independent U-REVIEW, G2
acceptance or implementation authorization**. Javid is the acting human decision-maker.
Baseline: `1f2beb9b477e796f5f2457ed2f6a3fe3ea45d992`, integrated by fast-forward into
B's clean independent clone. No local changes needed preservation. Read current CLAUDE,
CODEOWNERS, accepted U0005/U0006/U0022, U-P6/U-P8/U-P12 and their supporting context.
The old mandatory fork and Python contention-engine fallback are superseded by U0005.

## Completed lifecycle and evidence boundaries

Human adoption `ed9d7bb02a37ce83e93c9fb6d003553ffeacbdc0` and activation
`fa8716b07f50ccd56d006293677b08fd292e91fd` are ancestors. The [final local receipt](../U3-final-local-validation-v1/README.md)
records **1,701 passed / 29 skipped** on `3a148a0`; the [publication receipt](../U3-runtime-publication-v1/receipt.json)
records hosted CI success on `456215c` (Python 1,691 passed / 29 skipped / 10 deselected;
strict contracts 681 passed). These are inherited results, not reruns by B here.
The 28 rotary admission cases are activated. Adoption is complete; no generation,
placement, protected-test activation or artifact refresh is proposed again.

Current strict vendor/support verification was executed here and passed. The adopted
manifest is `1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a`;
input digest `27c6238d42e57dc4f2b1baf0c8846c11f1eec2968176dcefcdc463beb64bc80f`.
The [completed audit](../U3-artifact-adoption-v1/audit.json) preserves the 1,008 nominal
rows, four precision refusals and absent channels. rk-sim's pinned nominal channels
still do not model physical RoPE; adoption establishes currentness, not v2 oracle parity.

## Coverage and gaps

| Scope | Existing evidence and observable behavior | Remaining coverage / limit |
|---|---|---|
| Analytic v1, aggregate and per_op | `uarch-engine/1`, `resolved-ops/1`, `physical-resolved/1`; fixed BF16 d4 decode/prefill counts, rollup, attribution, nulls, refusals, saved replay; DRAM relations, aggregate clock, mode order; separate producer batch/context checks | Captured graph excludes RoPE rotation/conversion and coefficient traffic. No executed-work, queue, DMA, placement or history telemetry. Bounded fixture/rate domains do not establish every supported model/precision/rank. |
| Standalone v1 reports | [Original handoff](../U3-B-standalone-report-handoff.md) binds `eab89e07b0c7e41f7a2a0ee236dd1b00f78228c6`; [SR-C1 handoff](../U3-B-SR-C1/README.md) binds `85a5ad29820bc1c8638d844e192c6e4d778c107b`. Both modes, fixed corpus, two identical sequential replays, external pins, all five named mutants | Both whole rungs remain **partial/not_run**. Original clock coverage 21/24; SR-C1 22/24. Neither historical identity is replaced by current main. No production attachment or accepted independent review follows. |
| Analytic RoPE v2, aggregate and per_op | `uarch-engine/2`, `resolved-ops/2`, `physical-resolved/2`; explicit coefficient closure, Q/new-K work, casts and traffic; full-count literals and producer-disabled replay in `tests/rotary_v2/test_boundary.py`; preparation/rank/repeat/context, identity/dispatch, pairing-reference and adversarial tests in that directory; activated contract admission tests | No standalone v2 report/profile or v2 U-P6 property/mutant catalogue yet. Existing six rotary count-literal cases call the count helper; two full-result controls cover the public capture path. Scalar pairing tests are a test-only normative reference, not numerical engine execution. Result validation shares production arithmetic: consistency is useful, not independent proof. |
| Future native stages | U0005/U-P5 design obligations; build-spec clock and event rules; existing analytic baseline can supply a matched roofline comparison | No runnable native engine, admitted mapped boundary, stage corpus or observed resource behavior. U4a/U4b/U6 requirements await A's exact stage proposal and human decisions; no invented native input/output fields here. |

Historical SR-C1 reports contain L0 **14 pass / 14 skip / 0 not_run** and L0m
**9 pass / 13 skip / 5 not_run**. L0's duration-purpose projection passes; its other
purposes and L0m duration do not. Required 24-case mutant controls pass separately
for off_by_one_matrix, double_attribution, zero_unmodelled_diagnostic,
nondeterministic_output and wrong_bandwidth_field, each in both modes. This establishes
those assertions' discrimination, not queue/allocator fault detection. SR-C1 also retains
malformed JSON, NaN/nonfinite/opaque outputs, ordinary exceptions and malformed identities
as errors/not_run with finish events; they never count as valid examples or mutant kills.

The 29 inherited pytest skips are not the report's relation totals: 14 L0 unobservable,
12 L0m unrepresented/stateless, two deferred stipulation fixtures and one per-op exact
clock premise. Reports additionally expose deferred DRAM-clock cells and distinct-case
shortfalls. No skip becomes a pass merely because the test process exits successfully.

## Prospective analytic work proposal (not implemented)

**C1 — clock coverage.** Keep `analytic.aggregate_clock/1:aggregate:d4-bf16-v1`
and both historical outcomes intact. Discovery draws bandwidth, then `build_inputs`
replaces it with 10^18 bytes/s; distinct draws can collapse to identical admitted
bundle pairs. Hypothesis' 24 bodies are not 24 distinct cases. The SR-C1 discovery
ledger retains two duplicates; this is a selection/coverage defect, not a clock
counterexample. No favorable reruns or reduced requirements.

Propose a new profile/selection revision with a prospectively fixed 24-anchor floor
**plus** the existing bounded Hypothesis campaign (24 examples, generate/shrink,
derandomize, database=None). For anchor i=0..23, set core Hz to
`1_000_000 + floor(i*1_999_000_000/23)`, BF16 MACs/cycle to `1+i`, vector ops/cycle
to `64-i`, factor to `2+(i mod 3)`, and DRAM bandwidth to 10^18. Keep the existing
fixed graph/geometry and synthetic stub provenance. Frequencies survive transformation
and are distinct, including range endpoints; authenticate final pairs and independently
check compute dominance at the faster frequency for **both fixture points** before
crediting any case. A false premise remains explicit and blocks the intended coverage.
Do not infer it solely from the candidate's computed timing fields.

Keep the required count at 24 distinct passing pairs and the 240-call cap per cell per
ledger. With two points and two jobs per point, anchors require 96 calls; 24 ordinary
Hypothesis bodies require another 96, leaving at most 48 for extra replay/shrink calls
in discovery. Count every actual call; reaching the cap is incomplete/not_run, never a
reason to discard an early failing example. Declare anchor and generated budgets
separately in the new plan; Hypothesis internal rejected-draw counts stay unavailable.
Freeze all first-occurrence concrete pairs (not a chosen best 24), failures and omissions
before two qualifying replays. A separate profile version/domain-selection identity and
validator/test revision are required; the current registrar does not accept this plan.
This design proposes additional required inputs, not a silent edit of `/1` source bytes.

Require an unchanged-clock-output mutant on exactly the 24 prospective anchors:
24 controls plus 24 fault pairs cost 192 calls in its separate mutant ledger, within 240. Scaling memory with
core is C2's separate required mutant; a matrix-only timing fault is an additional
targeted test proposal, not three 24-pair mutants squeezed into one 240-call ledger.
Repeated transformed inputs must fail coverage even if every executed relation passes;
omitted anchors, cap exhaustion, surviving mutants and discovery failure followed by
passing replay must remain visible. Keep current tolerances (1e-9 relative for these
analytic relations); do not widen them to repair a shortfall.

**C2 — DRAM-bound clock (both modes).** Replace the ambiguous phrase “changes by less
than k” in the *proposed relation definition*, not protected policy: for k>1, fixed
work and independently fixed DRAM bandwidth, a memory-dominated aggregate has T'=T;
per_op has T'=T when **every** op is memory-dominated. More generally monotonic
`T/k <= T' <= T` holds for this max/sum model; strict speedup <k needs a positive
memory floor that binds the sum or an op. Use the existing 1,000–10,000 bytes/s domain
with factors 2..4, prove the relevant premises from literal counts/rates, and freeze
24 distinct pairs/mode with the same call cap (use C1's 24 distinct frequency
anchors with bandwidth fixed at 1,000, plus the bounded generated campaign).
Require a mutant that wrongly scales DRAM bandwidth with the core clock. A mixed-bound query is a separate domain; it
cannot satisfy an exact whole-query reciprocal-clock assertion by tolerance.

**C3 — unused stipulation (both modes).** Propose a new synthetic proposed-design
fixture under `hw/designs/`, with an explicit rationale for a `tdp_w` stipulation.
Pair positive values 100 W and 200 W, with a fixed admitted graph, capacity, compute
rates and DRAM bandwidth. TDP is carried by the hardware/derivation but not consumed
by the analytic duration/count formulas. Check unchanged counts, per-op timing,
attribution, duration and null diagnostics; expect different spec/job/result identities,
not byte-identical full results. Include a used-bandwidth negative control and a fault
that introduces TDP into duration. Validate proposed/reference provenance rules and
all joins before running: mutating the current reference fixture into an unexplained
stipulation is not authorized. For a concrete 24-pair floor, use C1's frequency/rate
anchors, fixed bandwidth 10^9 bytes/s and those TDP values; supplement with bounded generated pairs and retain
the same 240-call cap. Freeze the complete domain and pairs/mode prospectively.
If no admissible fixture can be constructed without protected change, propose that
exact blocker; keep this relation deferred. No fixture is created in this task.

**C4 — retain explicit capability gaps.** For both analytic versions/modes, executed
MAC conservation, DMA conservation, window utilization, Little's law, timed causality,
SRAM placement and energy conservation remain unobservable. NoC/SRAM bandwidth,
core-ID permutation, an unused placed core, latency, outstanding-DMA limits and
cold/steady effects remain unsupported. Per-op exact whole-query clock scaling remains
inapplicable to the existing memory-only embedding. Do not delete these catalogue cells
or convert their dispositions into success to claim a passed rung. Rich skip/not_run
states reduce conservatively under U0006; applicable failure dominates partial coverage.

**C5 — separately authorize a v2 corpus.** Proposed cross-product: aggregate/per_op;
BF16/FP16/FP32; R=2 and full R; decode contexts 1/17/33 and prefill; adjacent/split;
local KV partition/replication; layer reuse/repeat; fused/unfused causal/full-square
attention. Use bounded stratified cases rather than imply exhaustive model coverage.
Freeze exact cells, budgets, tolerances, refusals, mutant targets and v2 implementation/
assumptions/coefficient identities before implementation/execution. Build independent
literal expectations at the public capture/dispatch boundary, plus separate producer
checks; extend hardware-rate properties only with proven v2 premises. Include omitted
casts, doubled repeats, Hq-for-Hkv, omitted tail traffic and per-head coefficient rereads
as valid-output fault probes. [Worked examples](worked-examples.md) give new candidate
answers. Existing v1 report machinery is explicitly v1; v2 is a separately reviewed
extension, not attachment or a profile-name relabel. A change to any bound support input
still follows U0002; today's completed lifecycle is not blanket permission for a new one.

## Checks actually executed and stop

- `git fetch origin`, `git merge --ff-only origin/main`, ancestor checks for `1f2beb9`,
  `ed9d7bb` and `fa8716b`: passed; starting tree/index clean.
- `uv run --no-sync python scripts/vendor_rk.py --check`: passed current manifest,
  matrix and strict support/compatibility verification. No oracle generation invoked.
- `uv run --no-sync python -` with the exact standard-library block in
  [worked-examples.md](worked-examples.md#arithmetic-cross-check): all assertions passed.
  Arithmetic only; no engine, producer, suite or reference simulator was invoked.
- Read-only SHA256 check of the two retained SR-C1 gzip reports against their handoff's
  raw-source hashes: matched. No historical report validator/replay/generator rerun.
- Local Markdown link existence and `git diff --check`: passed for this package.

No runtime/schema/profile/test implementation changed. Ruff/mypy/import/schema suites,
pytest/full suite and native/nightly were not rerun for this prose-only task; their
published receipts above retain their original scope. No new runtime pass is inferred.
No dependency installation, protected edit, review/card evidence attachment or host change.

Coordinator decisions requested: (1) approve/revise C1's additional deterministic floor
and separate future profile revision; (2) settle C2's exact premise and C3's admissible
fixture before enabling deferred cells; (3) authorize and bound C5 separately; (4) reconcile
A's proposed mapped boundary/stage matrix against the [native checklist](native-checklist.md),
assign owners and obtain the exact stage/schema decisions. These are future tasks, not
permission implied by this handoff. No reopening of U0003/U0004 or accepted RoPE semantics.

STUB, unknown error and unverified energy remain. The designated Linux/self-hosted
`uarch` runner, enabled schedule and successfully executed manual nightly prerequisites
in the published execution plan are **unchanged and pending**; discussion does not amend
them. They do not block this analytic/documentation preparation. No U-P6 completion,
independent-review verdict, G2 acceptance, native implementation release or U3 closure.
