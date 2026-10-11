"""Small durable C04/C09 controls; no oracle invocation or hardware resizing."""

import copy

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.request import RequestIntent

from contract.tests import u2_prepared_adapter as adapter
from contract.tests.test_u2_a2_export_consumer import inputs
from rkuarch.workload import prepared
from rkuarch.workload.prepared import physical_assumptions
from scripts.vendor_rk import validate_u2_component_inputs
from tests.unit.test_u2_a_shapes import inputs as physical_inputs
from tests.unit.test_u2_a_shapes import prepare


def test_C04_padded_vocab_refuses_before_physical_call(monkeypatch):
    intent, hw = physical_inputs(tp=2)
    data = intent.model_dump(mode="json")
    data["model_shape"]["vocab_size"] = 7
    data["model"].update(total_params=364, active_params=364)
    intent = RequestIntent.model_validate(data)
    bundle = prepare(intent, hw, synthetic_assignment=True, rank_index=0)
    assert bundle.intent.model_shape.vocab_size == 7 and bundle.intent.tp == 2
    monkeypatch.setattr(
        prepared, "execute_prepared_point", lambda *a, **kw: pytest.fail("engine called")
    )
    with pytest.raises(ValueError, match="ProjectionScope: A-F12"):
        adapter.evaluate_captured(
            bundle,
            model=intent.model,
            model_shape=intent.model_shape,
            query=bundle.points[0].query,
            precision=intent.precision,
            tp=intent.tp,
            component_id=intent.component_id,
            assumptions=physical_assumptions(),
        )


@pytest.mark.parametrize("field", ["compute", "kv_cache"])
@pytest.mark.parametrize("invalid", ["fp128", "FP16", "bf16+fp8", "", 16])
def test_C09_invalid_explicit_descriptor_formats_refuse(field, invalid):
    entry, descriptors, artifacts = inputs()
    assert (
        len(validate_u2_component_inputs([entry], descriptors, artifacts, require_full=False)) == 1
    )
    bad = copy.deepcopy(entry)
    bad["precisions"][0][field] = invalid
    bad["precision_hash"] = content_hash(bad, exclude=("precision_hash",))
    with pytest.raises(ValueError):
        validate_u2_component_inputs([bad], descriptors, artifacts, require_full=False)
