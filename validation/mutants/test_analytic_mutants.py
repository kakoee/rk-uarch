"""Local execution of nightly-marked discrimination, with a valid control per mutant."""

import pytest
from hypothesis import given

from rkuarch.engines.analytic.core import run_analytic
from validation.analytic_checks import (
    check_attribution,
    check_bandwidth_response,
    check_counts,
    check_determinism,
    check_nulls,
)
from validation.mutants.analytic import mutant
from validation.strategies import MODES, bounded, fixed_bundle, hardware_specs, jobs

pytestmark = pytest.mark.nightly
NAMES = (
    "off_by_one_matrix",
    "double_attribution",
    "zero_unmodelled_diagnostic",
    "nondeterministic_output",
    "wrong_bandwidth_field",
)


def exercise(name, engine, bundle):
    if name == "wrong_bandwidth_field":
        check_bandwidth_response(engine, bundle)
        return
    for job in jobs(bundle):
        if name == "nondeterministic_output":
            check_determinism(engine, job)
        else:
            result = engine(job)
            if name == "off_by_one_matrix":
                check_counts(job, result)
            elif name == "double_attribution":
                check_attribution(result)
            elif name == "zero_unmodelled_diagnostic":
                check_nulls(result)
            else:
                raise AssertionError(f"Unregistered mutant: {name}")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("name", NAMES)
@bounded
@given(hardware=hardware_specs(memory_bound=True))
def test_named_mutant_is_rejected(name, mode, hardware):
    bundle = fixed_bundle(mode, hardware)
    exercise(name, run_analytic, bundle)
    with pytest.raises(AssertionError, match=name):
        exercise(name, mutant(name), bundle)
