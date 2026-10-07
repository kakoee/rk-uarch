# U-P5 · U3 · Lane A — Fork selection, the engine container, and the adapter

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, src/rkuarch/engines/README.md, third_party/README.md,
containers/README.md, build-spec §2.5 (the engine protocol) and §4 gate G2 in
docs/execution-plan.md. Read BOTH PAPERS IN FULL, not their abstracts. The planning documents
only had the abstracts and say so:
- PyTorchSim, MICRO 2025, doi 10.1145/3725843.3756045 (MIT; github.com/PSAL-POSTECH/PyTorchSim);
- ONNXim, IEEE CAL 2024, arXiv 2406.08051 (MIT; github.com/PSAL-POSTECH/ONNXim).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Consume the U2 prepared workload and preserve its already resolved rank shapes. The
adapter translates supported prepared operators to fork input; it does not independently
rebuild/shard the model. Keep the high-level CLI through the standalone producer. The fork's
internal tiling is a declared delegated-mapping mode, not proof it honored a supplied mapping.

TASK: get a published cycle-level NPU simulator driven by a uarch request, reproducibly, and
choose between the two candidates on pre-registered numbers.

1. BEFORE RUNNING ANYTHING, write docs/decisions/U0005-fork-selection.md's "pre-registered
   criteria" section and commit it. It holds G2's five criteria with the per-point wall-clock
   budget made concrete: derive it from the grid you intend (build-spec §2.3.3's default grid
   size) and a table build budget you state. A threshold chosen after seeing the number is a
   retrospective, not a gate.
2. containers/Dockerfile.engine — builds the candidate from a PINNED SHA, unattended, from a
   script. The image carries BookSim2 and Ramulator2 at the SHAs the fork's submodules pin.
   Build and run only on the Linux box, never on a laptop.
3. third_party/<fork>/: pinned SHA in third_party/LICENSES.md, with the licence of every
   component the image links (the fork, BookSim2, Ramulator2, and their dependencies). Local
   changes ONLY as numbered patches third_party/patches/NNNN-<slug>.patch, each with a
   one-line reason, applied at image build. CI job `patches` verifies they still apply.
4. src/rkuarch/engines/fork/ — the adapter. FILES IN, FILES OUT, NO FOREIGN-FUNCTION
   INTERFACE:
   - config_writer.py: HardwareSpec (a large-core design) -> the fork's config JSON. Every
     spec field the fork cannot represent is listed in the adapter's `unrepresented` output,
     which becomes a table warning. Never silently dropped. That includes the Rev-2 fields:
     the fork's dataflow, DRAM organisation and timing (its Ramulator config comes from the
     spec, never from the fork's default preset unless the spec names that preset),
     outstanding-request limits and per-job overhead are mapped where the fork has them and
     listed as unrepresented where it does not.
   - workload_writer.py: validated prepared workload -> the fork's LLM input format.
     Preserve its declared shapes, tp/rank scope, precision, fusion and omissions. Use
     provenance model metadata only when it faithfully represents those resolved operators;
     refuse inputs the fork format cannot express. ONNX or PyTorch graphs remain adapter
     outputs, never a new source-of-truth input language. No duplicate sharding logic.
   - runner.py: runs the container as a subprocess with a timeout, captures stdout/stderr
     and stats files, and records the image digest in the result.
   - stats_parser.py: fork stats -> EngineResult (build-spec §2.5): duration_ps, per-resource
     busy time, activity counts in contract channel names. MACs are converted to ops at
     2 per MAC (P7b) by a named function. Diagnostics are filled from the fork's stats where
     they exist and null otherwise; attribution follows the critical path and sums to the
     duration.
   - THE FORK'S MAPPING IS THE FORK'S. It tiles and schedules internally. Record it as
     mapping_policy "fork:<name>-default@<sha>", a stipulation on every row. Do not pretend
     uarch's mapping policies drove it.
   - initial_state: steady runs the query twice in one simulation where the fork allows it
     and reports the second; where it does not, initial_state is listed as unrepresented and
     the table warns. Never report a cold run as steady.
   - FIDELITY: place each of the fork's sub-models (compute, SRAM banks, NoC, DRAM) on
     build-spec §2.4's ladder, per configuration you run (its default, and any simpler NoC or
     DRAM mode it offers), from its source, cited by file and line. The table goes into ADR
     U0005. stats_parser emits that fidelity_detail, and the composite comes from §2.4's rule,
     never from the fork's name: if the fork models no SRAM bank conflicts, its compute is
     level 1 and its tables are C1. Record which sub-models ARE BookSim 2 or Ramulator 2, so
     U-P8 never compares them with themselves.
5. Evaluate ONNXim first (it is lighter). If it passes G2, you may skip PyTorchSim. Record
   that you skipped it and why. If it fails, evaluate PyTorchSim with the same criteria.
6. `uarch table ... --engine fork` for one-layer decode queries on npu-l4, driven from a
   ModelSpec end to end.

ACCEPTANCE TESTS (write first where they can be written first):
1. G2(a): `make image` from a clean clone builds the engine image unattended.
2. G2(b): three consecutive runs of the same query produce byte-identical stats files.
3. G2(c): decode matrix-op counts at B ∈ {1,8,32}, context/seq ∈ {512,4096} match rk-sim's
   parity fixtures within 0.5% after named deviations, no single deviation above 5%.
4. G2(d): wall-clock per one-layer decode query at or under the pre-registered budget.
5. G2(e): licence scan of the image green against the allow-list.
6. The adapter's `unrepresented` list is non-empty for npu-l4 if anything is unrepresented,
   and each entry appears as a table warning.
7. The fork's own default DRAM preset is never used silently: a spec whose timing_preset the
   fork cannot load is refused (UnnamedPreset) or listed as unrepresented.
8. ADR U0005 holds the fork's per-configuration ladder table with citations, and a table
   built by the fork reports exactly the composite §2.4's rule gives for those levels.

ADDITIONAL ACCEPTANCE — prepared inputs:
- Model-based preparation and replay of its saved bundle preserve identical workload
  semantics through the adapter, with independent shape/count checks at the fork boundary.
- A caller supplying an exact mapped TaskGraph that the fork cannot honor receives an
  explicit refusal. Selecting fork-delegated preparation is a separate declared choice.
- Result provenance identifies prepared content and pinned fork mapping/version; no claim
  of mapping equivalence is made without evidence of resolved correspondence.

GUARDRAILS: Do not patch the engine to make parity pass. Declare the deviation. Do not touch
anything under src/rkuarch/engines/native/. Do not start U-P7 until a fork has passed G2. If
BOTH fail, do not improvise a workaround: record the U-C1 fallback decision in ADR U0005
(build a Python contention-aware model, ship it labelled C1, record "C2 via fork:
unbuilt") and stop for the founders.

ADR: docs/decisions/U0005-fork-selection.md, with pre-registered criteria, every measured
number, the rejected candidate's numbers, the image digest, and the fork's ladder table.
```
