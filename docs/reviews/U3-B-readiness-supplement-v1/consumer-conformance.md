# Proposed bounded test-only consumer conformance

No implementation or test execution in this subtask. Target the committed upstream pin
`1e5706e0ebfcc67c1a7333079a35b75f693e9963`, current adopted manifest and U0001 name seam.
Use the existing `contract/tests/vendor_support.py::VendorLoader` from B-owned tests,
never an installed/imported production `rk` package or an upstream checkout. New protected
vectors, if needed, are a separate unapplied proposal. At most two admitted analytic v1
jobs (decode/prefill), one literal case plus one discriminating mutation per rule below;
no matrix sweep, table generation, external tool or currentness exception.

| Build-spec §7.2 rule | Proposed positive / negative case | What actually exercises vendored code |
|---|---|---|
| 1. One shard, divisor 1 | Test adapter returns saved per-rank duration unchanged at matching tp; reject an extra /tp | Adapter scaffolding. The real IterationCost `_time_s` is replica-oriented and divides by tp; a separate literal invocation documents that difference, never prices a shard by this path. |
| 2. Canonical compositions/errors | A uniform prepared query retains batch/total-context or prefill sums; adapter exposes present error metadata and missing estimates as unavailable | Actual decode/prefill method signatures and nominal count algebra are callable; composition/interpolation/error propagation is scaffolding until implemented. Ragged U0022 work is not invented for this test. |
| 3. Envelope | One in-envelope query accepted, one beyond bound refused | Adapter/contract checks, not a claim that vendored IterationCost has the future table reader. |
| 4. DVFS | Exact declared frequency point; missing frequency axis refuses a changed frequency | Scaffolding; do not multiply cached time by 1/f and claim table-axis support. |
| 5. Channel names/nulls | Use `translate_count_names`; four exact unique channel names, no scale; unknown key refuses; null stays null | Actual vendored Channel literals and IterationCounts. Actual decode_counts exposes writes=None, vector=None; preserve raw fields. Its `modelled_memory_bytes` internally sums known channels and must not replace the missing exported write channel with zero. |
| 6. One chip/facts | Matched spec hash/derived params; changed bandwidth or spec hash refuses even with rehashed payload | Existing local derivation/binding validators and adapter scaffold; no physical cross-model parity inferred. |
| 7. Steady state | Synthetic *test intent* for steady consumer check; cold analytic fixture refuses R1 admission | Scaffolding/refusal only. Analytic stateless equality supplies no warm-up/steady observation. Never change the original fixture's state to claim execution. |
| 8. KV block | Equal block sizes accepted; differing block size refuses | Contract/scaffolding. IterationCost's abstract KV channels do not verify a future paged table reader. |
| 9. TP | Exact matching tp accepted; mismatched tp refuses, never rescale counts | Scaffolding with real method signature/count observations as above; no replica/shard semantic laundering. |

Separate admission test: the proposed future **C2-only** consumer must reject C0/C1 and
inconsistent composite/subsystem/sync detail before pricing. Small analytic fixtures remain
C0 and are valid positive controls for the test adapter/name seam, **negative controls for
C2 admission**. There is no truthful executed C2 positive control today. A constructed
C2 carrier, if used at all, is labelled schema-only and cannot establish native capability.

Build the real vendored IterationCost only through its `iteration_cost()` constructor using
permitted synthetic ModelSpec/Accelerator inputs, matching its own precision/scope. Do not
hand-assemble its coefficient dataclass or substitute physical-v2 counts into its nominal
formula. Record real method calls/results separately from adapter assertions. No hardware
accuracy or independent L2 claim follows from this same pinned nominal code.

Implementation acceptance proposal: execute all admitted named cases, retain intended
assertion/refusal versus setup error, demonstrate no `rk` registration/sys.path change,
strict support and production isolation, and list unimplemented interpolation/serving/
orchestrator paths explicitly as not_run. Missing C2 positive coverage is not a passed
consumer admission verdict. B owns this later test-only work after scope approval; A owns
future result/table interfaces. Real U10 integration requires the separately accepted
rk-sim boundary, G5-correctness plus G6/G3b, full table behavior and complete consumer tests.
