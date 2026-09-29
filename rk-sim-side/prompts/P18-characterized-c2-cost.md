# P18 · post-S12 boundary · Lane A — Characterized C2 cost (from rk-uarch U-P19)

_From build-spec §8. One prompt, one fresh session. Requires the accepted boundary ADR admitting characterized C2 tables (draft: rk-uarch kit `rk-sim-side/decisions/DRAFT-admit-characterized-c2-tables.md`). When adopting, add this text block to build-spec §8 so `tests/unit/test_prompt_sync.py` holds._

```text
CONTEXT TO LOAD: rk-sim's CLAUDE.md, rk/engine/README.md, rk/engine/f0/compute.py (IterationCost
and iteration_cost, the seam this prompt substitutes behind), rk/engine/f0/power.py
(operating_point), rk/engine/registry.py, rk/engine/orchestrator.py (dispatch, _collectives,
_fidelity_map), rk/engine/f1/serving.py (how R1 consumes IterationCost), rk/schema/, ADRs 0011,
0015, 0016, 0018, 0021, and THE rk-sim BOUNDARY ADR ADMITTING CHARACTERIZED C2 TABLES. The
draft is in the uarch kit at rk-sim-side/decisions/DRAFT-admit-characterized-c2-tables.md.
It must be ACCEPTED, and its schema PR MERGED, before this prompt starts: build-spec §1.3 rules
out memoization surrogates for the prototype, and a characterization table is one. From
rk-uarch, READ-ONLY: docs/decisions/U0001 (the six rules), contract/schema/*.json at the
contract version the boundary ADR names, and one committed table.

TASK: a component whose effective compute fidelity is C2 is priced, every iteration, from a
uarch cost table instead of the C0 roofline, with the R1 DES unchanged.

1. rk/engine/characterized/ (new; engine layer; Lane A): loader.py reads a table file, verifies
   table_hash by recomputing it, checks the contract MAJOR version, checks the table's
   spec_hash against the component's characterization.spec_hash, and returns a frozen object.
   cost.py: CharacterizedIterationCost, satisfying EXACTLY the interface f1 already calls on
   IterationCost (decode_s, prefill_s, decode_counts, prefill_counts, collective_s, spill_s,
   power_point, kv_byte_per_context_token, tp, and whatever else f1 reads). If f1 annotates
   the concrete class, introduce a Protocol in f0/compute.py that both satisfy, and change
   ONLY the annotation in f1. The DES's behaviour does not change.
2. THE SIX RULES, each with its own test:
   a. A ROW IS ONE SHARD. THE TP DIVISOR IS 1. `_time_s` divides by tp today; carrying that
      into the table path double-counts tensor parallelism silently. Collectives still come
      from the orchestrator's _collective_coefficients, exactly as for C0.
   b. Canonical compositions: decode (B, T) maps to the table directly; prefill (T, Q) maps to
      n = T²/Q, L = Q/T. The table's measured composition_reduction error is copied into a
      run warning, stating its own provenance (ADR 0027).
   c. The envelope is checked at BUILD time, where UnsupportedPrecision is raised today, from
      the workload's reachable (B, T, Q) region. Never discovered mid-run; never extrapolated.
   d. DVFS: duration_at(f) interpolates the table's frequency axis. A plan that declares DVFS
      on a component whose table lacks a frequency axis is a HARD ERROR. Never evaluate at
      f = 1 silently.
   e. Counts map onto rk-sim's Channel names; ext_counts are carried through to channel
      diagnostics as coverage "unmodelled" until rk-sim adopts SRAM/NoC channels.
   f. One chip, one set of facts: the component's top-level params must equal
      derive_rk_params of the spec the table cites. Check the hash, not the numbers.
3. Registry: a C2 row for (compute_resource, compute, C2) naming
   rk.engine.characterized.cost, with requires=("characterization",). ADR 0016's three sets:
   C2 joins the ADMISSIBLE set via the schema PR; it is BUILT for a component only if that
   component carries a characterization. The orchestrator applies ADR 0011's asymmetry:
   system default C2 on an uncharacterized component → STUB with a warning naming the missing
   table; per-instance override C2 on it → NoTableForComponent, a hard error.
4. Badges: the uarch model is a named contributor whose badge is the table's model_card
   badge. Stipulated params are excluded from combine() and recorded in conditional_on (the
   schema PR landed the types; you wire them). A proposed design is capped at estimated. A run
   that mixes a C2 compute component with a C0 one emits a warning that says the comparison is
   biased AGAINST the detailed part, and why.
5. Fidelity map: the C2 row reports compute "C2", model_origin "uarch@<version>",
   fidelity_detail and table_hash (fields from the schema PR). config_hash includes the table
   hash through the component descriptor.
6. Golden: tests/golden/scenarios/asic_c2.yaml (lane-writable): 8 × a proposed ASIC at C2 from
   a committed fixture table under tests/fixtures/characterization/, R1 runtime. The expected
   file is human-owned; the test SKIPS WITH A REASON until `make golden-update` is run and
   committed with an ADR. Bump ENGINE_VERSION.

ACCEPTANCE TESTS (write first):
1. TP, HAND-COMPUTED: a two-row fixture table and tp = 8. decode_s equals the row's duration
   plus the collective, NOT duration/8 plus collective. The expected value is worked on
   paper and committed.
2. PLUMBING WITHOUT UARCH: generate a table from rk-sim's own C0 closed form on a grid. At grid
   points the characterized cost reproduces IterationCost exactly (==), and between points
   within the declared interpolation error. This proves the path independently of uarch's
   physics.
3. Envelope refusal at build time; spec-hash mismatch; contract-major mismatch; non-finite
   row; DVFS without a frequency axis: one test each, each raising the named error.
4. Default-degrades / override-raises asserted as a pair in one test.
5. Every existing golden is byte-identical. The C0 and R0/R1 paths are untouched.
6. R1 with a C2 component: determinism, Little's law and conservation (P5's tests) still hold.

GUARDRAILS: Never import rk-uarch; rk-sim reads files. Do not change f1's scheduling
semantics. Do not extrapolate, clamp, or refit a table. Do not edit tests/golden/expected/ or
CLAUDE.md. Do not touch web/: that is P19.
```
