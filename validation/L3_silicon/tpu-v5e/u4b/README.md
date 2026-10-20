# U4b consolidated reference and workload handoff

**Preparation complete; reference timing admission and G3a/U4 remain open.**
Baseline: `c6438fe42fe458fc8f75af884c9c04b95ff4f96a`. Author proposal, 2026-10-20.
No lane/human signatures, native extension, predictions or device observations are claimed.

Recommend **52 measured units** preserving all six original U-P9 classes and required
decoder work. Preserve the original 70-row proposal; every candidate has a disposition.
Recommend one TensorCore/four MXUs with shared local memory and explicit vector/scalar/HBM
work in the existing engine. Published data is insufficient for credible timing of the
complete suite: matrix startup/issue, vector service, memory latency/concurrency and device
startup remain consequential unknowns. Proceed with the specified structural/operator work;
keep numerical reference admission blocked until an independently justified timing model
is selected. Do not substitute npu-l4 properties or `--test-only` execution.

Read this as one package:

| Artifact | Purpose |
| --- | --- |
| [REFERENCE.md](REFERENCE.md) | Reconciled primary evidence, source conflicts, smallest representation and specific prediction blocker |
| [SUITE.md](SUITE.md), [suite-proposed.json](suite-proposed.json) | Finite 52-unit proposal; every unit's dimensions, mathematics, precision, native needs, fusion, mapping/state and device boundary |
| [DISPOSITIONS.md](DISPOSITIONS.md), [candidate-dispositions.json](candidate-dispositions.json) | All 70 historical rows retained, replaced, merged or omitted with a reason |
| [shape-regimes.json](shape-regimes.json) | Count-only U0001 bin worksheet, including the matrix-shape repair and decoder projection regimes; final characterize binding remains pending |
| [protected-amendments.patch](protected-amendments.patch) | Exact unapplied U0011 addition and narrow contract interface document; no protected file changed |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | Finite implementation order, reusable code/tests, independent arithmetic and behavioral checks, and U-P9 ordering ownership |
| [EVIDENCE.md](EVIDENCE.md) | Observed checks versus inherited evidence and remaining limitations |

## Decisions to resolve together

1. **Model/target:** retain TPU v5e with this complete workload and require independently
   justified pre-measurement timing laws before numerical admission (recommended). Approve
   source-independent implementation now. If no such model/source can be provided, explicitly
   defer the TPU prediction milestone or change the target/model requirement under U0023.
   A peak-only surrogate cannot predict the required vector/launch/gather behavior. This
   is the actual consequential blocker, not a request to choose arbitrary numbers.
2. **Protected representation and finite scope:** review the one unapplied patch together
   with the 52-unit suite. Recommend the scoped absolute-time interval representation,
   four MXUs/shared VMEM, raw INT8 dots with INT32 storage, BF16 decoder, fused attention and
   Q/K rotary envelopes, and 16/32-token page sizes. The contract patch is a concrete semantic
   document, **not generated Python/Rust carriers**. Human installation and later exact
   executable schema review are still required; no conditional runtime approval is invented.
   The two lane agreements remain unsigned. Confirm the consuming rk-sim plan's primary
   block size when agreeing scope; vendored code has no universal block-size default.

Runtime/compiler pinning, exact coefficient artifact bytes, allocation budgets and observed
fusion/state/counters are finite implementation/measurement-preparation work, not separate
requests for human answers to every field. If unavailable observability forces a scope
change, bring that concrete change back before prediction freeze. Device access/spend and
any pilot remain separately unauthorized; historical sample/warm-up proposals are not gates.

Ordinary runtime stays installed and unchanged. Preserve B laws and historical /2 restrictions.
No executable attestation, startup hardening, source tracing, host selectors, root deployment,
second engine, general hardware framework or campaign infrastructure is introduced.
Human L1 worksheets remain untouched. U0024 is still in force: native remote CI/nightly,
performance qualification and final closure remain pending; do not poll GitHub CI.
