"""Selectors bind declared RoPE/cache inputs without attaching evidence or raising badges."""

from __future__ import annotations

from rkuarch.engines.analytic.rotary_v2 import metric_contributors
from rkuarch.table.capture_v2 import capture
from rkuarch.workload.prepared_v2 import physical_assumptions

from .test_boundary import active_bundle


def test_count_dependencies_include_authenticated_rotary_and_cache_content():
    c = capture(active_bundle(), assumptions=physical_assumptions())
    selected = metric_contributors(c.jobs[0], c.bundle, assumptions=c.assumptions)
    for name in ("matrix_ops", "vector_ops", "memory_read_bytes", "memory_write_bytes"):
        selectors = selected["/counts/" + name]
        paths = {s.json_pointer for s in selectors if s.kind == "prepared_content"}
        assert {"/coefficients", "/intent/position_encoding", "/rank", "/points/0"} <= paths
        assert all(
            s.artifact_hash == c.bundle.bundle_hash
            for s in selectors
            if s.kind == "prepared_content"
        )
        assert any(
            s.artifact_hash == c.assumptions.assumptions_hash
            for s in selectors
            if s.kind == "model_assumption"
        )
    for i, op in enumerate(c.results[0].per_op):
        assert selected[f"/per_op/{i}/counts/vector_ops"] == selected["/counts/vector_ops"]
        assert any(s.kind == "hardware_leaf" for s in selected[f"/per_op/{i}/duration_ps"])
        assert op.scope.mapping_match is None
