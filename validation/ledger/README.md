# ledger — the only thing that can promote a model card

One entry per (benchmark × prediction source): question, granularity, applicability
dimensions, predicted, measured, signed relative error, engine and spec versions. A duplicate
key with a different prediction is refused. Promotion is scoped to the family and classes the
entries cover; never by hand; never by averaging across classes. Failing verdicts are
published like passing ones.
