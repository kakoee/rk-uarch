# engines — one protocol, three engines

Every engine: EngineJob JSON in, EngineResult JSON out, as a subprocess or in-process pure
function. No foreign-function interface.
- analytic/  U-C0: our roofline of the spec. aggregate mode reproduces rk-sim C0 to ±0.1%;
             per_op mode is always ≥ aggregate. Anchors every L1 test.
- fork/      the pinned published simulator in the engine container. Its mapping is its own,
             recorded as fork:<name>-default@<sha>. Fields it cannot represent are listed.
- native/    the Python side of our Rust engine (native/ at the repo root).
Cycles live here and in native/, and nowhere else. EngineResult carries duration_ps, a
critical-path attribution that sums to it, and diagnostics that are null wherever the level
does not model them, never 0.
