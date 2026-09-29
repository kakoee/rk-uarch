# workload — one iteration's operator graph

Input: rk-sim ModelSpec + ModelShape (parity ≤ 1% or loading fails) + precision + a canonical
query (decode: B sequences of T/B; prefill: n prompts of L). Output: an operator graph using
contract/operators.py only. A multiply-add is two operations. Layer reuse must be declared in
the graph. MoE is active-parameter dense-equivalent only; routing, imbalance and all-to-all are
listed in `omissions`, which become table warnings. FLOP parity against rk-sim's own counts
runs on every change; every deviation above 0.5% has a name and a reason in deviations.py.
