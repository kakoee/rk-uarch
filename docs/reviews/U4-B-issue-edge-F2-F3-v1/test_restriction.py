"""Synthetic policy controls plus exact reconstructed/historical inputs; no native jobs."""

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("f2_restriction", HERE / "restriction.py")
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


def raw(directions, engines, version="1", **extra):
    return json.dumps(
        dict(
            engine=dict(model=dict(name="native-intervals", version=version)),
            mapped_point=dict(
                task_graph=dict(
                    jobs=[
                        dict(
                            id=str(i),
                            kind="dma",
                            direction=d,
                            dma_engine_id=e,
                            fragments=[dict(request_id=str(i))],
                        )
                        for i, (d, e) in enumerate(zip(directions, engines, strict=True))
                    ]
                )
            ),
            **extra,
        )
    ).encode()


@pytest.mark.parametrize("name", ["cc0-v1", "ww0-v1"])
def test_exact_affected_reproducers_blocked(name):
    r = policy.classify((HERE / "reproducers" / f"{name}.json").read_bytes())
    assert r["status"] == "blocked_affected" and not r["execution_authorized"]


@pytest.mark.parametrize(
    "directions", [("read", "write"), ("write", "read"), ("write", "write"), ("read", "read")]
)
@pytest.mark.parametrize(
    "asserted", ["affected_same_instant", "unclassified", "classified_safe_by_direction"]
)
def test_direction_labels_or_caller_safety_claim_cannot_admit(directions, asserted):
    r = policy.classify(raw(directions, [0, 0], claimed_classification=asserted))
    assert r["status"] == "blocked_unclassified"
    assert r["broader_conservative_policy"] and not r["execution_authorized"]


@pytest.mark.parametrize("directions", [("write", "write"), ("read", "read"), ("read", "write")])
def test_static_absence_requires_engine_inventory_not_direction(directions):
    r = policy.classify(raw(directions, [0, 1]))
    assert r["status"] == "outside_F2_static_proof"
    assert r["proof"]["request_count_by_engine"] == {0: 1, 1: 1}
    assert not r["execution_authorized"]


@pytest.mark.parametrize("directions", [("write", "write"), ("read", "write")])
def test_model2_route_unaffected(directions):
    assert policy.classify(raw(directions, [0, 0], version="2"))["status"] == "outside_F2_model2"


def test_missing_engine_inventory_is_blocked():
    j = json.loads(raw(["write", "write"], [0, 1]))
    del j["mapped_point"]["task_graph"]["jobs"][1]["dma_engine_id"]
    assert policy.classify(json.dumps(j).encode())["status"] == "blocked_unclassified"
