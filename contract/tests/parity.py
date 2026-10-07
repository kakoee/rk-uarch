"""Reusable U-P2 comparison harness. No workload implementation lives here.

Callable signature: (ModelSpec, ModelShape, precision, query) -> counts.
The adapter supplied by U-P3 may validate the JSON arguments into Lane A's models.
query includes tp. Candidate counts are one rank; stored IterationCounts are replica-wide,
so the harness projects numeric oracle counts by tp only after checking supported scope.
Replication/padding is unsupported until a component-aware rule is reviewed. This is
not a reimplementation of rk-sim formulas or a physical-correctness certification.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

TOLERANCE = 0.005


@dataclass(frozen=True)
class Deviation:
    id: str
    channel: str
    deviation_rel: float
    reason: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.reason.strip() or not self.channel.strip():
            raise ValueError("a deviation requires an id, channel and reason")
        if not math.isfinite(self.deviation_rel) or abs(self.deviation_rel) > 0.05:
            raise ValueError("no single declared deviation may exceed 5%")


def compare_counts(
    fixture_id: str,
    actual: Mapping[str, float | None],
    expected: Mapping[str, float | None],
    deviations: Sequence[Deviation] = (),
    *,
    details: dict[str, Any] | None = None,
) -> float:
    if set(actual) != set(expected):
        raise AssertionError(f"{fixture_id}: count keys {set(actual)} != {set(expected)}")
    if len({d.id for d in deviations}) != len(deviations):
        raise ValueError("duplicate deviation ids")
    if any(d.channel not in expected for d in deviations):
        raise ValueError("deviation names an untested channel")
    worst = 0.0
    for key, reference in expected.items():
        value = actual[key]
        message = f"{fixture_id}: {key}: actual={value!r}, expected={reference!r}"
        adjustments = [d.deviation_rel for d in deviations if d.channel == key]
        signed = math.fsum(adjustments)
        absolute = math.fsum(abs(d) for d in adjustments)
        if details is not None:
            details[key] = {
                "actual": value,
                "reference": reference,
                "unit": "op" if key in ("matrix_ops", "vector_ops") else "byte",
                "reference_state": (
                    "unmodelled" if reference is None else "zero" if reference == 0 else "positive"
                ),
                "raw_rel": None,
                "signed_adjustment_rel": signed,
                "absolute_adjustment_rel": absolute,
                "residual_rel": None,
            }
        if (
            details is not None
            and reference is not None
            and math.isfinite(reference)
            and reference > 0
            and value is not None
            and math.isfinite(value)
            and value >= 0
        ):
            raw = (value - reference) / reference
            details[key].update(raw_rel=raw, residual_rel=raw - signed)
        if absolute > 0.05:
            raise ValueError(message + "; total absolute adjustments exceed 5%")
        if adjustments and (reference is None or reference == 0):
            raise ValueError(message + "; adjustments require a positive reference")
        if reference is None:
            if value is not None:
                raise AssertionError(message + "; unknown is not zero")
            continue
        if value is None or not math.isfinite(value) or value < 0:
            raise AssertionError(message)
        if not math.isfinite(reference) or reference < 0:
            raise AssertionError(message + "; invalid reference")
        if reference == 0:
            if value != 0:
                raise AssertionError(message + "; nonzero against zero")
            continue
        relative = (value - reference) / reference
        if adjustments and abs(relative) <= TOLERANCE:
            raise ValueError(message + "; unnecessary adjustments inside raw tolerance")
        residual = relative - signed
        if details is not None:
            details[key].update(raw_rel=relative, residual_rel=residual)
        if abs(residual) > TOLERANCE:
            raise AssertionError(message + f"; delta={relative}, declared={signed}")
        worst = max(worst, abs(relative))
    return worst


def rank_counts(fixture: dict[str, Any]) -> dict[str, float | None]:
    # This is rk-sim's aggregate/tp approximation, NOT general rank-local sharding.
    # Diagnostic arithmetic only: run_parity checks scope before calling this helper.
    # This helper alone must never establish workload-parity eligibility.
    return {
        key: None if value is None else value / fixture["tp"]
        for key, value in fixture["counts"].items()
    }


def projection_incompatibilities(fixture: dict[str, Any]) -> list[str]:
    """Conservative uniform-/tp eligibility, not a replacement for A's validation.

    A legitimately admits balanced KV replication and vocabulary padding; neither
    can be represented by dividing every aggregate channel by tp. Other declared
    shard dimensions must divide evenly as well. No new component-aware formula
    or physical correctness certificate is inferred from passing this guard.
    """
    tp = fixture.get("tp")
    if type(tp) is not int or tp < 1:
        return ["missing or invalid positive integer tp"]
    model, shape = fixture.get("model", {}), fixture.get("model_shape", {})
    dimensions = {
        "n_heads": model.get("n_heads"),
        "kv_heads": model.get("kv_heads"),
        "d_ff": shape.get("d_ff"),
        "vocab_size": shape.get("vocab_size"),
    }
    if shape.get("expert_d_ff") is not None:
        dimensions["expert_d_ff"] = shape["expert_d_ff"]
    reasons = []
    for name, size in dimensions.items():
        if type(size) is not int or size < 1:
            reasons.append(f"missing or invalid positive integer {name}")
        elif name == "kv_heads" and size < tp:
            reasons.append(
                f"kv_heads={size} requires replication at tp={tp}; uniform /tp incompatible"
            )
        elif size % tp:
            reasons.append(
                f"{name}={size} is not divisible by tp={tp}; padding/unequal shards incompatible"
            )
    return reasons


class ParityFailure(AssertionError):
    """A nonpassing run with complete fixture coverage, including unsupported scope."""

    def __init__(self, report: dict[str, Any]) -> None:
        self.report = report
        messages = [
            f"{name}: {entry['status']}: " + "; ".join(entry["reasons"])
            for name, entry in report["coverage"].items()
            if entry["status"] != "passed"
        ]
        super().__init__("\n".join(messages))


def run_parity(
    fixtures: Sequence[dict[str, Any]],
    candidate: Callable[..., Mapping[str, float | None]],
    *,
    deviations: Mapping[str, Sequence[Deviation]] | None = None,
    self_test: bool = True,
) -> dict[str, Any]:
    if not fixtures:
        raise ValueError("empty parity fixture set")
    ids = {fixture["id"] for fixture in fixtures}
    if len(ids) != len(fixtures):
        raise ValueError("duplicate fixture ids")
    unknown = set(deviations or {}) - ids
    if unknown:
        raise ValueError(f"deviations reference unknown fixture ids: {sorted(unknown)}")
    comparisons: dict[str, Any] = {}
    coverage: dict[str, Any] = {}
    for fixture in fixtures:
        name = fixture["id"]
        reasons = projection_incompatibilities(fixture)
        if reasons:
            coverage[name] = {"status": "unsupported_projection", "reasons": reasons}
            continue  # retain coverage; never call/compare an ineligible workload
        comparisons[name] = {}
        try:
            query = deepcopy(fixture["query"]) | {"tp": fixture["tp"]}
            actual = candidate(
                deepcopy(fixture["model"]),
                deepcopy(fixture["model_shape"]),
                deepcopy(fixture["precision"]),
                query,
            )
            compare_counts(
                name,
                actual,
                rank_counts(fixture),
                (deviations or {}).get(name, ()),
                details=comparisons[name],
            )
        except Exception as error:
            # Preserve implementation/numerical errors as failures, never unsupported.
            coverage[name] = {"status": "failed", "reasons": [f"{type(error).__name__}: {error}"]}
        else:
            coverage[name] = {"status": "passed", "reasons": []}
    passed = all(entry["status"] == "passed" for entry in coverage.values())
    raw = [
        abs(c["raw_rel"])
        for cs in comparisons.values()
        for c in cs.values()
        if c["raw_rel"] is not None
    ]
    report = {
        "kind": "harness self-test (not workload parity)" if self_test else "workload parity",
        "comparison_kind": "harness_self_test" if self_test else "workload_parity",
        "reference_basis": "rk_sim_aggregate_divided_by_tp",
        "authenticity": "caller-declared; harness does not authenticate the callable",
        "outcome": "passed" if passed else "failed",
        "coverage": coverage,
        "comparisons": comparisons,
        "n_fixtures": len(fixtures),
        "max_rel": max(raw, default=0.0),
        "declared_deviations": {
            fixture_id: [asdict(deviation) for deviation in declared]
            for fixture_id, declared in (deviations or {}).items()
        },
    }
    if not passed:
        raise ParityFailure(report)
    return report


def contract_payload(
    report: dict[str, Any],
    *,
    fixture_set_id: str,
    candidate_identity: str,
    oracle_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    """Serialize this comparison through A's actual carrier; never rerun the callable.

    Classification is structured and caller-declared. A human-readable summary label
    cannot upgrade self-test evidence into a workload comparison.
    """
    from uarch_contract.table import FlopParity

    kind = report.get("comparison_kind")
    if kind not in ("harness_self_test", "workload_parity"):
        raise ValueError("explicit structured comparison classification required")
    coverage = report.get("coverage", {})
    if (
        report.get("outcome") != "passed"
        or not coverage
        or set(coverage) != set(report["comparisons"])
        or len(coverage) != report["n_fixtures"]
        or any(entry["status"] != "passed" for entry in coverage.values())
    ):
        raise ValueError(
            "complete passing coverage required; "
            "unsupported/failed runs cannot use the success carrier"
        )
    comparisons = []
    for fixture_id, channels in report["comparisons"].items():
        for channel, quantities in channels.items():
            deviations = [
                {key: d[key] for key in ("id", "deviation_rel", "reason")}
                for d in report["declared_deviations"].get(fixture_id, [])
                if d["channel"] == channel
            ]
            comparisons.append(
                quantities
                | {
                    "fixture_id": fixture_id,
                    "channel": channel,
                    "declared_deviations": deviations,
                }
            )
    raw = [abs(c["raw_rel"]) for c in comparisons if c["raw_rel"] is not None]
    payload = {
        "kind": kind,
        "reference_basis": report["reference_basis"],
        "fixture_set_id": fixture_set_id,
        "candidate_identity": candidate_identity,
        "oracle_manifest_sha256": oracle_manifest_sha256,
        "n_fixtures": report["n_fixtures"],
        "max_rel": max(raw) if raw else None,
        "comparisons": comparisons,
    }
    return FlopParity.model_validate(payload).model_dump(mode="json")
