"""Final proposal joins only: synthetic output, hashes and enumeration, no capture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from uarch_contract.hashing import sha256

from native.tools import component_runtime_candidate as preparation
from native.tools import component_startup_inventory as startup
from validation.component import capture_diagnostics as diagnostic
from validation.component import capture_monitor as monitor
from validation.component import ordinary_eof_campaign as campaign
from validation.component import test_capture_diagnostics as records
from validation.component.ordinary_eof_acceptance import verify_closure

A = "docs/reviews/U4-A-construction-declarations-final-v1"
B = "docs/reviews/U4-B-capture-diagnostics-v1"
BINDING = "sha256:bcd940c0bdebe0f0f9edf48e8bef987eba6204c3f6f989a3d21d779a0b6fffda"
POLICY = "sha256:0b184913e4d13ea7be2f16ff131dafde2322657d649d2dad22d515a8efa2d6e8"


def test_final_import_startup_consumer_join(tmp_path: Path) -> None:
    # Synthetic observation bytes exercise imports() only; no payload/authority created.
    observation = tmp_path / preparation.OUTPUT / "observation-contract.json"
    observation.parent.mkdir()
    observation.write_text('{"synthetic":true,"authority":null}')
    value = preparation.imports(preparation.ROOT, observation_root=tmp_path)
    assert value["independent_binding"] == {
        "path": A + "/activation-consumer-bindings.json",
        "byte_hash": BINDING,
    }
    pins = json.loads((preparation.ROOT / A / "activation-consumer-bindings.json").read_bytes())[
        "files"
    ]
    inventory = {row["path"]: row["byte_hash"] for row in value["files"]}
    assert len(inventory) == len(value["files"]) == 183
    assert len(pins) == 85
    assert all(inventory[path] == "sha256:" + pin for path, pin in pins.items())
    startup_paths = startup.project_files(preparation.ROOT)
    assert len(startup_paths) == len(set(startup_paths)) == 183
    assert {
        str(path.relative_to(preparation.ROOT)): sha256(path.read_bytes()) for path in startup_paths
    } == inventory
    inherited = json.loads(
        (preparation.ROOT / A / "inherited-external-inventory.json").read_bytes()
    )
    # Same accepted dependencies, different clone-local venv roots: prove and report,
    # never relabel this B invocation as A's exact environment or rebind a binary.
    a_prefix = "home/jjaff/AI-infra-simulation/rk-uarch-u4-a/.venv/"
    b_prefix = "home/jjaff/AI-infra-simulation/rk-uarch/.venv/"
    expected = []
    relocated = 0
    for row in inherited["external_files"]:
        assert sha256((Path("/") / row["path"]).read_bytes()) == row["byte_hash"]
        path = row["path"]
        if path.startswith(a_prefix):
            path = b_prefix + path[len(a_prefix) :]
            relocated += 1
        expected.append({"path": path, "byte_hash": row["byte_hash"]})
    assert value["external_files"] == sorted(expected, key=lambda row: row["path"])
    print(f"EXTERNAL-PATH-TRANSITION: {relocated} clone-local venv paths; all byte hashes exact")
    assert value["python_executable"] == inherited["python_executable"]
    assert len(value["external_files"]) == 821
    assert campaign.cleanup_owned is vars(monitor)["cleanup_owned"]
    assert inventory[monitor.PARSER] == "sha256:" + monitor.PARSER_HASH
    print(
        "FINAL-JOIN: 183 imports/startup paths; 85 consumers; "
        "821 inherited external files; exact interpreter"
    )


def test_final_closure_identity_controls() -> None:
    pins = json.loads((preparation.ROOT / A / "activation-consumer-bindings.json").read_bytes())[
        "files"
    ]
    verify_closure({"source": str(preparation.ROOT), "pins": pins})
    for name in ("capture_monitor", "capture_diagnostics"):
        missing = dict(pins)
        del missing[f"validation/component/{name}.py"]
        with pytest.raises(ValueError, match="complete matching consumer/structural closure"):
            verify_closure({"source": str(preparation.ROOT), "pins": missing})
    stale = dict(pins)
    stale["native/tools/component_runtime_candidate.py"] = (
        "98857a5fbc07fe1c702753fb0bda130136ce365fa3cdc24152bac7686ddc6b1e"
    )
    with pytest.raises(
        ValueError, match="consumer source mismatch: native/tools/component_runtime_candidate.py"
    ):
        verify_closure({"source": str(preparation.ROOT), "pins": stale})


@pytest.mark.parametrize("mode", ["debug", "release"])
def test_actual_empty_policy_refuses_even_truthfully_traced_progress(
    tmp_path: Path, mode: str
) -> None:
    root, plan = records.fixture(tmp_path, mode)
    # Paired synthetic classifier proves this otherwise complete record is valid.
    assert diagnostic.inspect_capture(root, plan, 0)["diagnostics_accepted"]
    policy = preparation.ROOT / B / "diagnostic-policy-proposal.json"
    assert sha256(policy.read_bytes()) == POLICY
    assert json.loads(policy.read_bytes())["build_stderr_lines"] == {"debug": [], "release": []}
    plan["inputs"]["capture_diagnostic_policy"] = {"path": str(policy), "byte_hash": POLICY}
    before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    result = diagnostic.inspect_capture(root, plan, 0)
    assert not result["diagnostics_accepted"], result
    assert any("unclassified child diagnostic" in error for error in result["errors"]), result
    assert {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    assert not result["read_audit_complete"] and result["authority"] is None
