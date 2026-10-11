"""Discriminating future admission tests; none is runtime evidence yet.

Remove this explicit skip only under later runtime authorization when the new A validator
exists. The unmodified positive control must pass before each counterexample is refused.
"""

import importlib

import pytest
from uarch_contract.rotary_v2 import PreparedBundleV2

from contract.tests.rotary_v2_cases import RUNTIME_REFUSALS, examples, runtime_counterexample


@pytest.mark.parametrize("case", RUNTIME_REFUSALS)
def test_counterexample_is_carrier_valid_not_runtime_admitted(case: str) -> None:
    # This demonstrates why parsing is insufficient. It certifies no execution admission.
    PreparedBundleV2.model_validate(runtime_counterexample(case))


@pytest.mark.skip(reason="PENDING: authorized v2 runtime admission validator is not implemented")
@pytest.mark.parametrize("case", RUNTIME_REFUSALS)
def test_future_full_admission_refuses_counterexample(case: str) -> None:
    boundary = importlib.import_module("rkuarch.workload.prepared_v2")
    admitted = boundary.validate_execution_bundle(examples()["bundle"])
    assert admitted.format == "uarch-prepared/2"
    with pytest.raises(ValueError):
        boundary.validate_execution_bundle(runtime_counterexample(case))
