# U-P6 · U3 · Lane B — L0 invariants and L0m metamorphic relations

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, validation/README.md, build-spec §2.7 (the ladder), tests/README.md,
src/rkuarch/engines/README.md (the engine protocol every suite runs through). From rk-sim
READ-ONLY: tests/properties/ (the house style for property tests).

PREPARATION BOUNDARY (build-spec §2.5.1, approved direction 2026-10-06):
ADR: docs/decisions/U0019-standalone-preparation-and-prepared-input-replay.md.
Exercise saved prepared jobs as well as the standalone frontend. Keep tests of the
producer's counts/shape resolution separate from engine invariants on fixed inputs. Apply
metamorphic graph/mapping changes explicitly, update their content identity, and never let
an engine repair a deliberately invalid mapping through hidden re-preparation.

PHASING (U0023): dispose each outstanding analytic obligation by its first consumer:
native roofline checks, U5/U8 baseline predictions, reports or later capability. Required
checks pass before reliance; unrelated report completion does not block K1. Keep previous
outcomes, missing coverage and U0006 reductions. Do not blanket-pause C1–C5, lower case
counts or call unobservable mechanisms verified. Native checks follow admitted mechanisms.
Provide the dependency disposition before a revised execution selection is authorized.
U0011 records the accepted U3 design/shared semantics, not permission to start U4. At B use
independent component bounds; no full-model analytic job masquerades as a component API.
B owns real Linux CI preparation before K1 evidence, once U4 and exact tool/license pins
are authorized. Current artifact enforcement stays active until a separately approved migration.

TASK: the rungs that establish that the simulator does not contradict itself, and relations
that must hold even though nobody knows the right answer. They run against ANY engine through
the engine protocol: today U-C0, the progressively admitted native engine later. Write
them once.

1. validation/L0_invariants/ — per engine run:
   - MACs executed == MACs in the operator graph (from the workload graph, not re-derived);
   - For each represented DMA boundary, direction and declared byte unit,
     freeze the request population and half-open observation window [t0,t1). With no cancellation
     or loss, verify `in_flight_end = in_flight_start + issued_bytes - completed_bytes` from actual
     issue/completion observations, including requests crossing either boundary. Start/end state
     is immediately before events at t0/t1 respectively. Payload versus
     transaction/padding bytes, multicast duplication, partial completion, cancellation and
     retry semantics require explicit ledger terms before the applicable check. Verify local
     resident capacity separately from distinct allocation/lifetime/alias observations. Compute
     operand consumption is not a conserved transfer-byte inventory: reuse and newly produced
     outputs forbid a general `DMA in = compute consumed + written back` identity. Missing
     required observations leave the represented stage unverified; analytic absence remains
     unsupported and cannot produce a positive check.;
   - no resource utilisation > 1 over any window;
   - finite-window membership, clipped residence and conservation for represented queues
     at B, including initial/terminal members; stationary Little's law within 1% at its
     first qualifying claim (normally U6 or earlier reliance), with frozen population,
     window, boundary/censoring and nonzero-flow premises; missing observations never pass;
   - causality: no event or interval begins before the one it depends on (for engines that
     emit traces);
   - byte-identical reruns;
   - per-core SRAM occupancy ≤ sram.bytes at every event (engines that report placement);
   - attribution_s parts sum to duration_s within 1e-9 relative;
   - energy = Σ counts × coefficients + static power × duration, on every row that reports
     energy;
   - null, not zero: a diagnostic of a subsystem running at a level that does not model it is
     null.
2. validation/L0m_metamorphic/ — relations over PAIRS of runs:
   - doubling any bandwidth (DRAM, NoC link, SRAM port) never increases duration;
   - For k>1, compare f with k*f using identical admitted resolved work,
     precision, assumptions and all non-compute rates, including fixed DRAM bandwidth; validate
     both transformed hardware inputs. For the analytic max/sum model require `T/k <= T' <= T`.
     Exact `T'=T/k` needs aggregate compute dominance at the faster clock, or compute dominance
     for every op at that clock in per_op mode. Exact `T'=T` needs aggregate memory dominance at
     the base/slower clock, or memory dominance for every op at that clock in per_op mode.
     State speedup as T/T', with positive durations: strict speedup <k requires a strictly
     binding fixed memory term at the faster clock (a tie alone is insufficient). Mixed-bound
     and memory-only-op domains cannot inherit exact reciprocal scaling by tolerance. Preserve
     all failures, unsupported premises, budgets and historical reason codes.;
   - decode duration is non-decreasing in batch and in context;
   - permuting core ids on a symmetric topology (torus, or mesh with a symmetric mapping)
     leaves duration unchanged;
   - adding an idle core (one the mapping does not use) changes nothing;
   - a stipulated-parameter change that the mapping does not touch changes nothing;
   - raising any latency (router, DRAM timing, job overhead, barrier) never shortens duration;
   - lowering dma.max_outstanding never shortens duration;
   - a cold run is never faster than the steady run at the same point.
3. Write them as HYPOTHESIS PROPERTY TESTS over generated HardwareSpecs and queries, with
   strategies in validation/strategies.py that only generate valid specs. Examples alone
   prove only the examples. A relation an engine cannot express (U-C0 models no latency and
   no initial state, for example) SKIPS for that engine with its reason; it never passes.
4. Each suite writes a machine-readable report (JSON, hashed) that the model card cites under
   verification.L0 / verification.L0m. A card may cite only a report produced by the same
   engine version.
5. POWER, DEMONSTRATED NOT ASSERTED: for at least five relations, commit a deliberately
   injected bug under validation/mutants/ (a bandwidth read from the wrong field; an
   off-by-one tile count; a queue that drops requests; an attribution that double-counts
   overlap; an allocator that ignores SRAM capacity), and a test that runs the suite
   against the mutant and asserts it FAILS. Mark these tests so they run nightly.

ACCEPTANCE TESTS:
1. Every required applicable L0/L0m case passes before its declared use; aggregate/per_op
   and version scopes stay explicit. Unsupported/not_run cases prevent whole-rung claims.
2. Every committed mutant is caught, by name.
3. Reports are hash-stable across runs.
4. When the bounded native stage lands (U4a), run every applicable case through its public
   protocol. Add it to the capability matrix; a failure there is a finding for Lane A,
   not a test to relax.

GUARDRAILS: These rungs are about RELATIONS. Do not assert a numerical value that someone
would have to believe. Do not downgrade a failing invariant to a warning. Ever. Do not make
L0/L0m depend on an external fork: they must run on the analytic engine alone.
Apply accepted U0006 reductions: unsupported cases are explicit not_run, never passing evidence.

ADR: docs/decisions/U0006-what-verification-can-and-cannot-establish.md. State plainly that
L0–L2 evidence never lifts a model above stub, and why: agreement with yourself, or with
another simulator, is not agreement with silicon.
```
