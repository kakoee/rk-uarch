"""Coordinator regression proposal: real H1 hardware, tiny workload, synthetic review context."""
import json
from pathlib import Path
import pytest
import yaml
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, spec_hash, content_hash
from rkuarch.table.build import capture, build_table
from rkuarch.workload.prepared import physical_assumptions
from tests.integration.test_u2_a_replay import companions
from tests.unit.test_u2_a_loader import reviewed
from tests.unit.test_u2_a_shapes import inputs, prepare

@pytest.mark.parametrize('order', ['canonical', 'reversed'])
def test_real_h1_condition_order_does_not_change_table(order):
    hardware = HardwareSpec.model_validate(yaml.safe_load(Path('hw/designs/npu-l4.yaml').read_text()))
    raw = hardware.model_dump(mode='json')
    if order == 'canonical':
        raw = json.loads(canonical_json(raw))
    else:
        def reverse(v):
            if isinstance(v, dict):
                return {k: reverse(v[k]) for k in reversed(v)}
            if isinstance(v, list):
                return [reverse(x) for x in v]
            return v
        raw = reverse(raw)
    reordered = HardwareSpec.model_validate(raw)
    assert hardware == reordered and spec_hash(hardware) == spec_hash(reordered)
    intent, _ = inputs()
    intent = intent.model_copy(update={'hardware_spec_hash': spec_hash(hardware)})
    tables = []
    for hw in (hardware, reordered):
        captured = capture(prepare(intent, hw), assumptions=physical_assumptions())
        context, card, store = companions(captured)
        registry = dict(store[context.family_registry_hash])
        registry['entries'] = [dict(e, hardware_spec_hash=spec_hash(hw)) for e in registry['entries']]
        reviewed(registry, 'registry_hash', store)
        context = context.model_copy(update={'family_registry_hash': registry['registry_hash']})
        context = context.model_copy(update={'context_hash': content_hash(context, exclude=('context_hash',))})
        tables.append(build_table(captured, context=context, model_card=card, artifacts=store).table)
    assert tables[0].rows == tables[1].rows
    assert canonical_json(tables[0]) == canonical_json(tables[1])
