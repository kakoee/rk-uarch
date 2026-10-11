# workload — one iteration's operator graph

Input: rk-sim ModelSpec + ModelShape (parity ≤ 1% or loading fails) + precision + tp + a
canonical query (decode: B sequences of T/B; prefill: n prompts of L). Output: the operator
graph of ONE rank of a tp-way tensor-parallel split (heads, KV heads, FFN and vocabulary
divided by tp; no collectives), using contract/operators.py only. Attention is one
attention_fused operator: scores stay on chip and never reach DRAM. A multiply-add is two
operations. Layer reuse must be declared in the graph; its experimental error is unknown
at U2 (zero samples, null estimates). KV traffic reads valid tokens, not page capacity.
For T=17 and block_size_tokens=16, two pages are allocated but only 17 tokens are read;
page-rounded capacity accounting remains separate. MoE is active-parameter dense-equivalent only. `omissions` lists routing,
imbalance, all-to-all, host/runtime time, address translation, coherence and mixed
prefill/decode iterations; they become table warnings. Independent physical correctness/discrepancy tests and separate nominal compatibility run
on every change; no nominal pass is claimed as physical parity.
`uarch characterize` reports FLOPs, bytes, operational intensity and shape regime per op
across the grid; L3 suites and workload suites pick shapes from it.

Preparation boundary (build-spec §2.5.1): this module is the standalone, versioned producer
and loader of prepared OpSpec graphs. Engines receive its resolved output. A supplied
rank-local graph bypasses model expansion and sharding; validate its identity, supported
scope, precision, dependencies and omissions. Keep the high-level convenience path usable
without rk-sim or a compiler. U-P3 adds export/import/replay; no second workload IR is added.

U0003 S boundary: physical-resolved runs authoritative prepared work and has independent
correctness/replay tests plus complete physical-versus-nominal discrepancy reports. The
separately identified nominal-rk-compatibility candidate is test-only; its unchanged count
and stored-duration thresholds replace the former physical nominal-parity gate explicitly.
Report inputs include complete comparison/evidence/registry/recipe closure. Default STUB
magnitudes are hidden; explicit finite-prediction opt-in requires complete contributors and
visible unvalidated labels on every surface. No live timestamps, null-as-zero or ambient
artifact lookup. Exported extended hardware truth and five-field test projections are distinct.
