# Proposed U0005 — Defer the pinned fork routes; design a source-based U-C1 amendment

**DRAFT, NOT ACCEPTED.** This is review text, not a file under docs/decisions/.
Decision owner: Javid (@jjaffari), acting for both lanes. Author inspection is not
independent U-REVIEW. Proposed basis: this package's final publication revision;
Javid must identify the exact revision if accepting. No measured G2 verdict exists.

## Context

The required one-chip diagnostic includes complete prepared rank-local work: embeddings,
projections, fused paged GQA, append/cache state, explicit RoPE Q/new-K work, norms,
residuals, gated FFN, final norm and vocabulary head. A faithful adapter preserves physical
padding/replication/repeats, BF16 operand semantics and FP32 arithmetic, and must expose
independent completed-work evidence. Modelled device latency differs from simulation host
wall time. Work omitted by a simulator cannot be listed as an unrepresented hardware field.

U0022's additive runtime is published at
`456215cdf9ec4ec383ce2604a483ee4bfa7f5991` (tree
`2570682d1af20a0860b70b9bbd79a0ec75ad1a4b`). It resolves missing RoPE declaration and
analytic accounting, not candidate execution. ONNXim
`a1e86296e080fa1c82f8ad3f1b6de1079c192afc` has source contradictions in both native and
ONNX routes. PyTorchSim `5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3` has a stopped example
route, hard-coded FP32 matrix templates, unestablished fused/paged execution and incomplete
executed-work observations. Its TOG interface requires externally established compute
latencies; absent latency can fall back to 10 cycles. The [source record](source-evidence.md)
contains exact paths and distinguishes contradictions from unknowns. Neither tool was built,
run or empirically timed; neither has passed or empirically failed the five-part G2 gate.

The execution plan invokes U-C1 after both candidates fail G2. Choosing it on source
infeasibility is a different trigger and requires an explicit plan amendment. This draft
proposes a bounded design step to make that decision concrete; it does not pretend that
the existing fallback implementation is already authorized or complete.

## Existing accepted rules retained

U0002 human-owned source-bound artifact lifecycle; U0003 physical/nominal separation,
rank conservation and prepared inputs; U0004 badge/display limits; U0006 actual execution,
complete coverage, failures and independent review; U0019 replay without resharing or hidden
preparation; U0022 exact RoPE semantics all remain. Unsupported exact mapping is refused,
fork mapping delegation is explicit, no unnamed DRAM preset is selected, unknown quantities
stay null. U-P5's prohibition on changing engine behavior to obtain parity remains in force.
Any exception needs a distinct decision and is not part of this draft.

## Proposed decision

1. Record **source feasibility blocked at the stated pins**, with no defensible complete
   adapter-only route established. Defer U-P5 implementation/build/evaluation; do not select
   a newer source pin, relax the workload or relabel the result “both failed G2.” No continuing
   broad simulator search is commissioned.
2. Commission the [bounded U-C1 design action](next-decision.md): A/B produce a complete-work
   contention model proposal, execution/evidence boundary, literal acceptance cases, exact
   plan/prompt amendments and implementation estimate. Expected 16–28 combined engineering
   hours, capped at 28, plus 4–8 separate reviewer/decision hours. Stop on design contradictions
   or cap exhaustion. No engine, schema or public product implementation is released.
3. Require a **subsequent human decision** to authorize a source-based fallback trigger and
   accept the precise U-C1 design/plan changes. Until then U4/U5/fork-based U6 dependencies
   remain unresolved. If accepted later, record “C2 via fork: unbuilt” and loss of the
   independent published-fork reference explicitly. Do not automatically grant C1 to an
   analytic roofline model.
4. Separate approvals for instrumentation, semantic/compiler extensions, diagnostic/gate
   changes, licences, host allocation, builds and experiments. Package publication grants
   none of them. A later capability experiment is not G2 or implementation acceptance.

## Exact downstream questions for the amendment

The later amendment must replace U3's prerequisite to U4 with an explicit accepted and
verified U-C1 exit, preserving full-workload admission/counts and reproducibility evidence.
U4/G3 must specify table precisions/coverage, mapped-input replay, policies appropriate to
the new engine, fidelity, byte-identical workers, interpolation/composition/layer/state errors
and independent L1/L2 scope. FP8/full-grid feasibility is UNRESOLVED; no reduced scope is
silently accepted. No U-P7 execution follows this design authorization.

U5/G4 remains gated by a revised verified G3, with C1 predictions frozen before silicon and
same evidence/badge rules. U6's external reference changes to U-C1 only under an accepted
amendment. Preserve G5's matched mapping and levels, 3% agreement on at least 95% of points,
1/N-worker determinism and measured speed factor unless explicitly changed in that amendment.
The U-C1 model/available configurations must make those comparisons meaningful. If no
matched-level case exists, name the deferred dependency and downstream G5 consequences;
never certify accuracy by comparing models sharing the same assumptions/code. Independent
external reference evidence remains absent even if native and U-C1 agree.

## Prospective preregistration retained, not accepted

The [earlier G2 proposal](../U3-U0005-proposal.md) and
[integer expectations](../U3-G2-physical-expectations.md) remain historical proposals:

| Item | Prospective value / unresolved obligation |
| --- | --- |
| Model | Synthetic g2-8b-shape-1layer, 1,268,789,248 parameters; full embedding/decoder/tail, not full 32-layer runtime |
| Matrix | B={1,8,32}, attended C={512,4096}, tp={1,8}, plus tp8/B1/rank1 at both C: 14 decode cases, three repetitions = 42 invocations/candidate |
| Prepared-only coverage | Seven bundles, each with n=1/L=8 prefill; no simulator prefill execution credited |
| Work/state | BF16/BF16, H1, block16, cold, seed7, frequency1, fused full-square convention, conserved local hit vectors, once-only head/tail |
| RoPE update needed | New v2 inputs; exact coefficients/producer/hash, R/pairing and candidate capability/refusal controls **UNRESOLVED** before acceptance; no implicit named-model table |
| Budget | **200 s unaccepted**, adapter validation through completed parse including point-specific compilation/latency work; derived from 24 h/336-point planning allocation, not measured full-table cost |
| Build/determinism/counts/licences | Unattended source build; complete byte-identical designated stats/results over three runs; exact independently observed per-op physical counts at 2 ops/MAC with all nonmatrix work preserved; complete allow-list inventory |
| Stable statistics alternative | Direct complete emitter and observation provenance require separate prospective acceptance; raw operational logs retained, no post-hoc stripping/sorting/rounding |
| Hardware/image | Exact config/DRAM binding, source/patch/compiler/assets, image digest, fidelity/state/mapping support **UNRESOLVED** |

No value is inferred from an unperformed measurement. No smaller or FP32-only diagnostic
replaces this proposal; such a benchmark would only characterize selected components and
would require an explicit different claim/gate. A later full G2 evaluation requires a
human-committed exact preregistration before measurements, alongside resolved semantics,
observations, licences and host prerequisites. A kernel capability discriminator cannot
satisfy any complete-work G2 finding.

## Measurement and acceptance record

- Chosen external simulator: **none**.
- Image/config/compiler/latency closure: **unbuilt / unresolved**.
- Measured device duration, host wall time, per-op executed counts: **not measured**.
- Three-run complete-statistics comparison: **not run**.
- Image licence inventory: **not built/scanned**.
- G2(a–e): **not evaluated**; source blockers are separately documented.
- C1 fallback implementation, public v2 product/report, native engine: **unbuilt**.
- Independent accepted review, card attachment, U3 closure: **not established**.

## Consequences and exclusions

This recommendation spends bounded design effort to decide whether a faithful C1 route is
worth building. It avoids assuming container availability fixes semantics. The main risk is
weaker independence for future native validation and additional internal model maintenance.
Conditional U-C1 implementation is estimated at 116–232 engineering/reviewer hours with low
confidence, excluding full U4 product/error campaigns; acceptance of that estimate is not
requested now. The alternative P extension program has no credible total-to-G2 estimate;
precision/fusion/paging/timing changes are material category-4 work, with separately blocked
licence/compiler assets and long-term ownership. See [cost breakdown](README.md#options-and-active-effort).

No implementation, support-bound byte, adopted artifact, historical result, accepted source
pin, threshold, badge, fidelity rule, licence allow-list, server or workflow changes here.
No simulator code/build/script execution or measurement authority; no numerical RoPE kernel,
silicon validation, full-model speed claim, independent acceptance or sprint closure.
The next dependency is coordinator reconciliation followed by Javid's exact design-task
choice; implementation and experiments remain stopped.
