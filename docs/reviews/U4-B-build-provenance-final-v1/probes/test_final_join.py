"""Independent synthetic final joins. No compiler, Docker, trace or startup activity."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from uarch_contract.hashing import sha256

from native.tools import component_runtime_candidate as prep
from native.tools.component_startup_inventory import project_files
from rkuarch.engines.native import component_build_review as adapter
from rkuarch.engines.native import component_host, component_review
from rkuarch.engines.native.records import FileBinding
from tests.unit import test_component_build_review as a_fixture
from validation.component.runtime_checks import verify_sources

joined = a_fixture.joined
put = a_fixture.put

A = "docs/reviews/U4-A-build-provenance-final-v1"


def test_final_inventory_and_consumer_join(tmp_path: Path) -> None:
    path = tmp_path / "private-component/observation-contract.json"
    path.parent.mkdir()
    path.write_text('{"synthetic":true,"authority":null}')
    value = prep.imports(prep.ROOT, observation_root=tmp_path)
    expected = json.loads((prep.ROOT / A / "source-transition.json").read_bytes())
    assert len(expected["prospective_source_files"]) == 259
    for name, pin in expected["prospective_source_files"].items():
        assert sha256((prep.ROOT / name).read_bytes()) == "sha256:" + pin
    imported = {item["path"]: item["byte_hash"] for item in value["files"]}
    assert len(imported) == len(value["files"]) == 190
    assert imported == {
        str(p.relative_to(prep.ROOT)): sha256(p.read_bytes()) for p in project_files(prep.ROOT)
    }
    binding_path = A + "/activation-consumer-bindings.json"
    assert value["independent_binding"] == {
        "path": binding_path,
        "byte_hash": sha256((prep.ROOT / binding_path).read_bytes()),
    }
    pins = json.loads((prep.ROOT / binding_path).read_bytes())["files"]
    assert len(pins) == 90 and all(imported[k] == "sha256:" + v for k, v in pins.items())
    verify_sources(prep.ROOT, pins)
    for key in (
        "native/tools/component_ordinary_build.py",
        "src/rkuarch/engines/native/component_build_review.py",
        "src/rkuarch/engines/native/component_review.py",
        "validation/component/ordinary_build_acceptance.py",
        "validation/component/ordinary_build_receipt.py",
    ):
        missing = dict(pins)
        del missing[key]
        with pytest.raises(ValueError, match="complete matching consumer/structural closure"):
            verify_sources(prep.ROOT, missing)
    stale = dict(pins)
    stale["native/tools/component_runtime_candidate.py"] = (
        "24271b51ffe564b01455059ca49e1831fe3576c99764b0f276755f1e97a61d58"
    )
    with pytest.raises(ValueError, match="consumer source mismatch"):
        verify_sources(prep.ROOT, stale)
    inherited = json.loads(
        (
            prep.ROOT
            / "docs/reviews/U4-A-construction-declarations-final-v1"
            / "inherited-external-inventory.json"
        ).read_bytes()
    )
    original = "home/jjaff/AI-infra-simulation/rk-uarch-u4-a/.venv/"
    current = "home/jjaff/AI-infra-simulation/rk-uarch/.venv/"
    normalized = []
    for row in inherited["external_files"]:
        assert sha256((Path("/") / row["path"]).read_bytes()) == row["byte_hash"]
        normalized.append(
            {
                **row,
                "path": row["path"].replace(original, current, 1)
                if row["path"].startswith(original)
                else row["path"],
            }
        )
    assert value["external_files"] == sorted(normalized, key=lambda row: row["path"])
    assert len(normalized) == 821 and value["python_executable"] == inherited["python_executable"]


def review_fixture(value: dict[str, Any]) -> tuple[dict[str, Any], FileBinding]:
    root, expected = value["root"], value["expected"]
    # These records are explicitly synthetic shape evidence, never genuine assurance.
    launcher = put(root, "synthetic-launcher", b"not executable: synthetic launcher")
    support = put(root, "synthetic-startup-evidence", {"synthetic": True, "authority": None})
    startup = put(
        root,
        "synthetic-startup",
        {
            "format": "uarch-component-startup-assurance/1",
            "subject": {k: expected[k] for k in ("runtime_payload_byte_hash", "consumer_hash")},
            "verdict": "accepted",
            "launcher": launcher,
            "manifest": put(root, "synthetic-manifest", {"synthetic": True}),
            "evidence": [support],
        },
    )
    return {
        "format": "uarch-component-runtime-review/2",
        "subject": {"runtime_payload_byte_hash": expected["runtime_payload_byte_hash"]},
        "build_provenance": put(root, "synthetic-provenance", value["record"]),
        "startup_assurance": startup,
        "selected_support_current": True,
        "selected_support_evidence": [support],
        "optional_read_evidence": None,
    }, FileBinding.model_validate(launcher)


def test_actual_provenance_review_without_trace_still_requires_startup(
    joined: dict[str, Any],
) -> None:
    record, launcher = review_fixture(joined)
    root, expected = joined["root"], joined["expected"]
    good = component_review.check_runtime_review(root, record, expected=expected, launcher=launcher)
    assert good.optional_read_evidence is None
    assert any(item.path.endswith("ordinary-build-receipt.json") for item in good.required_files)
    bad = dict(record)
    del bad["startup_assurance"]
    with pytest.raises(ValueError):
        component_review.check_runtime_review(root, bad, expected=expected, launcher=launcher)
    (root / record["startup_assurance"]["path"]).unlink()
    with pytest.raises(OSError):
        component_review.check_runtime_review(root, record, expected=expected, launcher=launcher)


def test_incomplete_optional_trace_stays_incomplete(joined: dict[str, Any]) -> None:
    record, launcher = review_fixture(joined)
    root = joined["root"]
    raw = b'{"read_audit_complete":false,"status":"NONE CAPTURED"}'
    record["optional_read_evidence"] = put(root, "optional-investigation.json", raw)
    checked = component_review.check_runtime_review(
        root, record, expected=joined["expected"], launcher=launcher
    )
    assert checked.optional_read_evidence is not None
    assert (root / "optional-investigation.json").read_bytes() == raw


def test_absent_active_startup_state_refuses_without_invocation() -> None:
    assert "_rkuarch_trusted_startup" not in sys.modules
    with pytest.raises(ValueError, match="startup assurance/active manifest join"):
        component_host.require_reviewed_startup("sha256:" + "0" * 64)


@pytest.mark.parametrize(
    "relative", ["inputs/source/.cargo/config.toml", "inputs/cache/config.toml"]
)
def test_untracked_staged_configuration_must_refuse(joined: dict[str, Any], relative: str) -> None:
    root = joined["root"]
    baseline = adapter.consume_provenance(root, joined["record"], joined["expected"])
    assert baseline
    path = root / "debug" / relative
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"# synthetic untracked configuration; never executed\n[build]\njobs = 1\n")
    # Exact source/cache provenance must reject an extra build-visible input.
    # No outer record/hash is changed; no native execution is attempted.
    with pytest.raises(ValueError):
        adapter.consume_provenance(root, joined["record"], joined["expected"])
