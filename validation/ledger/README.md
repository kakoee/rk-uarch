# ledger — the only thing that can promote a model card

One entry per (benchmark × prediction source): question, granularity, applicability
dimensions (family, op class, precision, shape regime, load regime, mapping match), predicted,
measured, signed relative error, engine and spec versions. A duplicate key with a different
prediction is refused. Promotion is scoped to exactly what the entries cover; never by hand;
never by averaging across classes. Workload-fidelity entries (FLOPs and bytes vs the
compiler's counts) and diagnostic-fidelity entries (row diagnostics vs device counters) never
promote a duration card. Failing verdicts are published like passing ones.
