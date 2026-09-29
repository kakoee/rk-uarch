# U-P6 · U3 · Lane B — L0 invariants and L0m metamorphic relations

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, build-spec §2.7 (the ladder), tests/README.md,
src/rkuarch/engines/README.md (the engine protocol every suite runs through). From rk-sim
READ-ONLY: tests/properties/ (the house style for property tests).

TASK: the rungs that establish that the simulator does not contradict itself, and relations
that must hold even though nobody knows the right answer. They run against ANY engine through
the engine protocol: today U-C0, the fork when U-P5 lands, the native engine later. Write
them once.

1. validation/L0_invariants/ — per engine run:
   - MACs executed == MACs in the operator graph (from the workload graph, not re-derived);
   - DMA bytes moved in == bytes consumed by compute plus bytes written back;
   - no resource utilisation > 1 over any window;
   - Little's law within 1% on every queue the engine reports (mean occupancy vs arrival
     rate × mean residence);
   - causality: no event or interval begins before the one it depends on (for engines that
     emit traces);
   - byte-identical reruns.
2. validation/L0m_metamorphic/ — relations over PAIRS of runs:
   - doubling any bandwidth (DRAM, NoC link, SRAM port) never increases duration;
   - scaling every core-domain clock by k scales a compute-bound query's duration by 1/k
     within 1%, and changes a DRAM-bound one by less than k;
   - decode duration is non-decreasing in batch and in context;
   - permuting core ids on a symmetric topology (torus, or mesh with a symmetric mapping)
     leaves duration unchanged;
   - adding an idle core (one the mapping does not use) changes nothing;
   - a stipulated-parameter change that the mapping does not touch changes nothing.
3. Write them as HYPOTHESIS PROPERTY TESTS over generated HardwareSpecs and queries, with
   strategies in validation/strategies.py that only generate valid specs. Examples alone
   prove only the examples.
4. Each suite writes a machine-readable report (JSON, hashed) that the model card cites under
   verification.L0 / verification.L0m. A card may cite only a report produced by the same
   engine version.
5. POWER, DEMONSTRATED NOT ASSERTED: for at least three relations, commit a deliberately
   injected bug under validation/mutants/ (a bandwidth read from the wrong field; an
   off-by-one tile count; a queue that drops requests), and a test that runs the suite
   against the mutant and asserts it FAILS. Mark these tests so they run nightly.

ACCEPTANCE TESTS:
1. Every L0 and L0m suite passes against U-C0 (aggregate and per_op).
2. Every committed mutant is caught, by name.
3. Reports are hash-stable across runs.
4. When the fork lands (U-P5), the same suites run against it with no code change. Add the
   fork to the engine matrix and record the result; a failure there is a finding for Lane A,
   not a test to relax.

GUARDRAILS: These rungs are about RELATIONS. Do not assert a numerical value that someone
would have to believe. Do not downgrade a failing invariant to a warning. Ever. Do not make
L0/L0m depend on the fork: they must run on the analytic engine alone.

ADR: docs/decisions/U0006-what-verification-can-and-cannot-establish.md. State plainly that
L0–L2 evidence never lifts a model above stub, and why: agreement with yourself, or with
another simulator, is not agreement with silicon.
```
