# Decisions requested from Javid

This is a reviewable design proposal, not an implementation authorization or G2 verdict.
Approve, revise or reject each item independently; approval must name the reviewed commit.

1. **Stage:** accept checkpoints M → K → B → T and the exact npu-l4/BF16/TP1 component
   scope in [README](README.md). Accept explicit decoder/v2/steady/spill refusals at B.
   Preserve full G3 requirements, including RoPE; a GEMM demonstration cannot close G3.
2. **Interface:** accept the additive `uarch-prepared/3` mapped envelope,
   `uarch-taskgraph/1` and `uarch-engine/3` design in [interface](interface.md), including
   component versus complete-model scope, test-only fixture admission, completion-derived
   observations, stable results versus operational receipts, immutable v1/v2 handling,
   and the field/fixture inventory. Authorize preparation of an installable protected
   carrier/schema/test patch next; review and human commit that exact patch before K.
   Do not widen analytic roots or install this prose as if it were a tested schema.
3. **Model assumptions:** accept the explicit WS interval law, NoC-0 infinite bandwidth,
   DRAM-0 latency/derating and DMA service/arbitration definitions in
   [verification](verification.md). These are model conventions requiring verification,
   not claims of hardware accuracy. A different convention changes expectations and
   assumption identity prospectively, never to fit an observed answer.
4. **Verification:** accept the stage matrix, U0006 reductions and mandatory public-boundary
   faults. Ask B to author/review the frozen corpus and arrange two genuinely human-worked
   L1 fixtures (including latency-bound DMA). This author's derivations do not meet the
   human or independent-review requirement. Reconcile remaining U-P6 coverage separately.
5. **Environment and budgets:** accept the prospective allocations/ceilings in
   [delivery](delivery.md), conditional on an authorized performance host. Resolve exact
   Rust release, base digest, lock and transitive license inventory before build; authorize
   a separate reviewed tool/license pin proposal, not a blanket dependency exception.
   The current task neither grants a host reservation nor claims license closure.
6. **Runner policy:** decide whether to accept the coordinator's recommended narrower
   prerequisite in a separate human amendment. Recommended separation: correctness builds
   on approved Linux CI; performance only on a designated controlled Linux host;
   self-hosted `uarch` registration/manual nightly for that automation. Until installed,
   U0005's stronger prerequisite still governs all native implementation/build/performance.
   This proposal does not itself change U0005, CLAUDE.md, prompts or workflows.
7. **Expansion dependencies:** commission B's explicit sourced hardware extension for
   output-stationary and FP8, and an exact precision/RoPE decision for the required FP8
   table. U0022 refuses FP8 activation/KV; neither dropping RoPE nor calling BF16-only a
   complete table is acceptable. Select supplied coefficient/profile provenance, complete
   70B-class model identity and error-experiment coverage before T. No default theta/table.

If accepted, the next bounded work is M's installable schema/fixture proposal and
coordinated verification design, subject to existing ownership and runtime prerequisites.
Human-owned [proposed U0011](proposed-U0011.md) must be installed by the human, with exact
schema and environment follow-ups completed before their dependent work. No sprint closure,
badge, artifact lifecycle, silicon campaign or external reference admission is bundled
into this decision.
