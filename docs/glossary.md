# Glossary

| Term | Meaning |
|---|---|
| claim | A SourcedValue about the world: stub (source: null) or sourced |
| stipulation | A design choice on a proposed chip: rationale, no source, excluded from worst-of, listed in conditional_on |
| proposed / reference | A chip that does not exist (stipulations allowed) / a real chip (claims only) |
| U-C0 | uarch's own roofline of a spec; aggregate reproduces rk-sim C0; every C2 row must be ≥ it |
| level 0 / 1 / 1+ts / 2 / 3 | per-subsystem fidelity: analytic / contention-aware / contention-aware with cycle timestamps / cycle-approximate / reference only |
| composite | the single C0/C1/C2 reported to rk-sim, by the rule in build-spec §2.4 |
| canonical batch | equal-length sequences standing for a (B, T, Q) query; the reduction error measures the cost of that stand-in |
| fork | the pinned published simulator (ONNXim or PyTorchSim); the native engine's permanent L2 reference |
| native | our C++20 event-driven engine |
| L0 · L0m · L1 · L2 · L3 · L4 | invariants · metamorphic · analytical limits · differential · same-class silicon · target silicon |
| verified / validated | L0–L2 / L3+. Only validated evidence moves a badge |
| initial_state | `steady` (one priming iteration simulated, the second reported) or `cold` (empty SRAM, closed rows); a stipulation on every row |
| layer-reuse error | how far simulating one decoder layer × n_layers misses simulating every layer; measured on a seeded sample, never corrected |
| memory-level parallelism | bandwidth a requester can reach given `dma.max_outstanding` × `request_bytes` ÷ round trip |
| shape regime / load regime | applicability bins: operational intensity vs the ridge point × array fill; offered load vs saturation |
| mapping match | `matched` (silicon ran uarch's policy) or `compiler-chosen`; separate ledger classes |
| workload fidelity | the operator graph's FLOPs and bytes checked against compiler-reported counts |
| declared omissions | host/runtime time, address translation, coherence, mixed prefill/decode iterations, MoE routing: on every row |
| null, not zero | a quantity a level does not model is null and renders "not modelled" |
| DES | NOT this codebase — rk-sim's R1 serving simulation |
