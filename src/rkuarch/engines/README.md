# engines — one protocol, three engines

Every engine: EngineJob JSON in, EngineResult JSON out, as a subprocess or in-process pure
function. No foreign-function interface.
- analytic/  U-C0: our roofline of the spec. aggregate mode prices resolved physical work; nominal compatibility is test-only;
             per_op mode is always ≥ aggregate. Anchors every L1 test.
- fork/      the pinned published simulator in the engine container. Its mapping is its own,
             recorded as fork:<name>-default@<sha>. Fields it cannot represent are listed.
- native/    the Python side of our Rust engine (native/ at the repo root).
Cycles live here and in native/, and nowhere else. EngineResult carries duration_ps, a
critical-path attribution that sums to it, and diagnostics that are null wherever the level
does not model them, never 0.

Prepared-input ownership (build-spec §2.5.1): engines consume validated resolved work,
not high-level model recipes that invoke a builder. U2 analytic jobs carry resolved OpSpecs
and an explicit analytic scope; U4 detailed jobs carry mapped TaskGraphs. U2 establishes
versioned protocol fixtures for later fork/Rust consumers. Replay requires neither local
producer execution nor a compiler. Fork-delegated mapping is explicit and supplied mappings
that it cannot honor are refused. Resource timing and contention remain simulation outputs.

U0003 S boundary: physical-resolved runs authoritative prepared work and has independent
correctness/replay tests plus complete physical-versus-nominal discrepancy reports. The
separately identified nominal-rk-compatibility candidate is test-only; its unchanged count
and stored-duration thresholds replace the former physical nominal-parity gate explicitly.
Report inputs include complete comparison/evidence/registry/recipe closure. Default STUB
magnitudes are hidden; explicit finite-prediction opt-in requires complete contributors and
visible unvalidated labels on every surface. No live timestamps, null-as-zero or ambient
artifact lookup. Exported extended hardware truth and five-field test projections are distinct.
