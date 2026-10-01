# workload — one iteration's operator graph

Input: rk-sim ModelSpec + ModelShape (parity ≤ 1% or loading fails) + precision + a canonical
query (decode: B sequences of T/B; prefill: n prompts of L). Output: an operator graph using
contract/operators.py only. A multiply-add is two operations. Layer reuse must be declared in
the graph, and its error is measured by table/. KV is read in pages of the request's
block_size_tokens. MoE is active-parameter dense-equivalent only. `omissions` lists routing,
imbalance, all-to-all, host/runtime time, address translation, coherence and mixed
prefill/decode iterations; they become table warnings. FLOP parity against rk-sim's own counts
runs on every change; every deviation above 0.5% has a name and a reason in deviations.py.
`uarch characterize` reports FLOPs, bytes, operational intensity and shape regime per op
across the grid; L3 suites and workload suites pick shapes from it.
