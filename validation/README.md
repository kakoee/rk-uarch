# validation — the evidence

L0_invariants/    conservation, bounds, Little's law, causality, determinism, SRAM capacity,
                  attribution sums, energy conservation
L0m_metamorphic/  relations that must hold without an answer key (property tests)
mutants/          deliberately broken engines each suite must catch (nightly)
L1_limits/        closed forms where exact, the U-C0 floor, and hand/ fixtures worked on paper
L2_differential/  BookSim 2, Ramulator 2, SCALE-Sim v3, Gemmini/Verilator, tt-npe, native↔fork,
                  Accelergy (energy), Timeloop (mapping reference, optional)
L3_silicon/       frozen predictions and immutable results per reference chip
ledger/           one entry per comparison; the only source of a model card's rung
perf/ sync/       simulator metrics; the error-vs-quantum curve

Verified (L0–L2) is not validated (L3+). Suites run through the engine protocol against every
engine; never relax a suite because an engine fails it — that is a finding.
