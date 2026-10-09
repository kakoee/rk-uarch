# table — request in, hashed UarchCostTable out

Builds the grid from the request's envelope (and refuses a request whose grid does not cover
it), runs points in a process pool (parallel across points only; byte-identical at any worker
count), interpolates exactly as declared, and measures its own errors: leave-one-out
interpolation (also weighted by rk-sim's visit density when the request supplies it),
batch-composition reduction, layer reuse, and cold vs steady. It reports them; it never
corrects them. Outside the grid is an error, never a clamp or an extrapolation.

U0003 S boundary: physical-resolved runs authoritative prepared work and has independent
correctness/replay tests plus complete physical-versus-nominal discrepancy reports. The
separately identified nominal-rk-compatibility candidate is test-only; its unchanged count
and stored-duration thresholds replace the former physical nominal-parity gate explicitly.
Report inputs include complete comparison/evidence/registry/recipe closure. Default STUB
magnitudes are hidden; explicit finite-prediction opt-in requires complete contributors and
visible unvalidated labels on every surface. No live timestamps, null-as-zero or ambient
artifact lookup. Exported extended hardware truth and five-field test projections are distinct.
