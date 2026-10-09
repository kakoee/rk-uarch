"""U2 has no measured error experiments; unknown is never serialized as zero error."""

from uarch_contract.table import MeasuredError


def unmeasured_errors() -> MeasuredError:
    sample = dict(median_rel=None, max_rel=None, n_samples=0)
    return MeasuredError.model_validate(
        dict(
            interpolation_loo=dict(sample, weighted_median_rel=None),
            composition_reduction=dict(decode=sample, prefill=sample, n_samples=0),
            layer_reuse=sample,
            cold_vs_steady=dict(sample, priming_2_vs_1_max_rel=None),
        )
    )
