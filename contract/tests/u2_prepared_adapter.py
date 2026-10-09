"""Test-only comparison adapter: select captured physical work, never nominal counts."""

from __future__ import annotations

from uarch_contract.assumptions import AssumptionSet
from uarch_contract.model_shape import ModelShape, ModelSpec
from uarch_contract.precision import Precision
from uarch_contract.prepared import PreparedBundle, Query

from rkuarch.engines.protocol import EngineJob, EngineResult
from rkuarch.workload import prepared


def evaluate_captured(
    bundle: PreparedBundle,
    *,
    model: ModelSpec,
    model_shape: ModelShape,
    query: Query,
    precision: Precision,
    tp: int,
    component_id: str,
    assumptions: AssumptionSet,
    frequency_ratio: float = 1.0,
) -> tuple[EngineJob, EngineResult]:
    """Require exact selection identity and A-F12 before the shared physical boundary."""
    bundle = PreparedBundle.model_validate(bundle)
    intent = bundle.intent
    if (intent.model, intent.model_shape, intent.precision, intent.tp, intent.component_id) != (
        model,
        model_shape,
        precision,
        tp,
        component_id,
    ):
        raise ValueError("CapturedSelectionMismatch: model/shape/precision/tp/component")
    if model.kv_heads < tp or model_shape.vocab_size % tp:
        raise ValueError("ProjectionScope: A-F12 replicated KV or padded vocabulary")
    points = [p for p in bundle.points if p.query == query and p.frequency_ratio == frequency_ratio]
    if len(points) != 1:
        raise ValueError("CapturedSelectionMismatch: exact query/frequency")
    point = points[0]
    if any(
        p.physical != p.logical for g in point.graph.groups for o in g.ops for p in o.padding
    ) or any(r.replicas != 1 for g in point.graph.groups for o in g.ops for r in o.replication):
        raise ValueError("ProjectionScope: A-F12 captured padding/replication")
    return prepared.execute_prepared_point(bundle, point.payload_hash, assumptions=assumptions)
