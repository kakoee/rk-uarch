# Proposed U0009 — The large-core reference and what it can support

Status: proposal for human installation as
`docs/decisions/U0009-the-large-core-reference-and-what-it-can-support.md`.
This review file does not install or approve a protected ADR.

The first silicon reference is Google Cloud TPU v5e: one TensorCore with four large
systolic MXUs sharing local memory and an aggregate HBM path. Freeze the accepted 52
microbenchmark envelopes and their exact prepared inputs before any measurement. Use the
installed R native interval model and retained U-C0 aggregate/per-op baseline, with every
unpublished parameter represented as a disclosed STUB claim. The legacy YAML path is
superseded for this task by the accepted reference API route.

Future L3 evidence can support **few-large-systolic-core architectures**, only within
actually compared operator/fusion, precision, shape, state and mapping domains. It cannot
support **mesh-shaped architectures**, distributed-core NoC routing or congestion,
per-tile SRAM behavior, bank/channel mechanisms absent from this model, inter-chip
collectives, or unmeasured target chips. A future mesh reference has its own preparation,
prediction, measurement and evidence scope. Similar peak throughput is not family equivalence.

All current comparisons are compiler-chosen: local ws-rowsplit/3 mapping is not evidence
of XLA correspondence. Unknown hardware parameters, mapping mismatch and method error
remain confounded unless later evidence separates them. Device-only durations and compiler
work/byte counts are separate observations; unverified diagnostic allocation cannot establish
causes. Error remains unknown, calibration stub and energy unverified before actual L3
comparison. Determinism and L0–L2 verification do not promote those labels.

Javid's 2026-10-22 acceptance replaces outstanding lane signatures for the unchanged suite
and moves compiler/device correspondence into U5 measurement work. It authorizes neither
pilots nor tuning. Incomparable envelopes keep the old prediction; changed subjects require
an explicit prospective disposition and new immutable prediction identity. No successful G4
verdict or full-table prerequisite is imposed. U0024 infrastructure deferrals remain pending.

The frozen archive and unknown-parameter inventory are the concrete subject of this
proposal. Hardware access, spending and measurement execution require their separate
existing authorization. No protected contract, engine model or evidence threshold changes.
