"""Proposed A-owned F8 adapter: human selection counts, no timing surface expansion."""

import copy

from rkuarch.workload.characterize import characterize, characterize_markdown
from tests.unit.test_u2_a_shapes import inputs, prepare


def test_characterization_scope_labels_and_raw_duration_preservation():
    intent, hw = inputs()
    raw = characterize(prepare(intent, hw))
    before = copy.deepcopy(raw)
    text = characterize_markdown(raw)
    assert "Duration ps" not in text and "U-C0 ps" not in text
    assert "1892000.0" not in text and "1584000.0" not in text
    assert "1184.0 · STUB" in text
    assert "1296.0 · STUB" in text
    assert "Intensity ops/byte" in text
    assert "Shape" in text and "Query:" in text
    assert "Energy: unverified" in text
    assert "timing estimates remain only in the raw JSON" in text
    assert raw == before
    assert raw["results"][0]["duration_ps"] == 1892000.0
