# table — request in, hashed UarchCostTable out

Builds the grid from the request's envelope (and refuses a request whose grid does not cover
it), runs points in a process pool (parallel across points only; byte-identical at any worker
count), interpolates exactly as declared, and measures its own two errors: leave-one-out
interpolation error and batch-composition reduction error. It reports them; it never
corrects them. Outside the grid is an error, never a clamp or an extrapolation.
