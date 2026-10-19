"""Independent final-join controls: hash/read and synthetic data only, no workers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
from uarch_contract.hashing import canonical_json, sha256

from native.tools import component_runtime_candidate as preparation
from validation.component import capture_monitor as capture
from validation.component import ordinary_eof_campaign as campaign
from validation.component import test_capture_monitor as fixtures
from validation.component.ordinary_eof_acceptance import verify_closure

PACKAGE = "docs/reviews/U4-A-activation-combined-preparation-v1"


def test_actual_imports_cover_exact_final_pins(tmp_path: Path) -> None:
    observation = tmp_path / preparation.OUTPUT / "observation-contract.json"
    observation.parent.mkdir()
    observation.write_text('{"synthetic":true,"authority":null}')
    value = preparation.imports(preparation.ROOT, observation_root=tmp_path)
    selected = value["independent_binding"]
    assert selected["path"] == PACKAGE + "/activation-consumer-bindings.json"
    assert selected["byte_hash"] == (
        "sha256:245b0dd9330b736304eeb9f6e9b50001358388b882fcc17b6103d0fc3ea1a983"
    )
    pins = json.loads((preparation.ROOT / selected["path"]).read_bytes())["files"]
    inventory = {v["path"]: v["byte_hash"].removeprefix("sha256:") for v in value["files"]}
    assert len(value["files"]) == len(inventory) == 180
    assert len(pins) == 83
    assert {name: inventory[name] for name in pins} == pins
    assert inventory[capture.PARSER] == capture.PARSER_HASH
    for name in ("ordinary_eof_campaign", "capture_monitor"):
        assert f"validation/component/test_{name}.py" in inventory
        assert f"validation/component/test_{name}.py" not in pins
    assert campaign.cleanup_owned is vars(capture)["cleanup_owned"]
    print(
        "FINAL-IMPORTS",
        json.dumps(
            {
                "project_files": len(inventory),
                "pins": len(pins),
                "external_files": len(value["external_files"]),
                "binding": selected,
            },
            sort_keys=True,
        ),
    )


def test_missing_and_stale_bindings_are_identity_refusals() -> None:
    pins = json.loads(
        (preparation.ROOT / PACKAGE / "activation-consumer-bindings.json").read_bytes()
    )["files"]
    verify_closure({"source": str(preparation.ROOT), "pins": pins})
    for name in ("ordinary_eof_campaign", "capture_monitor"):
        bad = dict(pins)
        del bad[f"validation/component/{name}.py"]
        with pytest.raises(ValueError, match="complete matching consumer/structural closure"):
            verify_closure({"source": str(preparation.ROOT), "pins": bad})
    bad = dict(pins)
    bad["native/tools/component_runtime_candidate.py"] = (
        "5eb07277a2f062ae07a7c6abbf23d750fe3094e5bab6c93fcadc2dd05a0d6717"
    )
    with pytest.raises(
        ValueError, match="consumer source mismatch: native/tools/component_runtime_candidate.py"
    ):
        verify_closure({"source": str(preparation.ROOT), "pins": bad})


def test_current_recipe_rejects_extra_builder_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = cast(Any, fixtures.plan).__wrapped__(tmp_path, monkeypatch)
    capture.verify_plan(plan)
    original = list(plan["child_argv"])
    plan["child_argv"] += ["--", "-C", "link-arg=-Wl,-Map=/receipts/debug.map"]
    with pytest.raises(ValueError, match="exact construction argv"):
        capture.verify_plan(plan)
    plan["child_argv"] = original
    recipe_path = Path(plan["inputs"]["construction_recipe"]["path"])
    recipe = json.loads(recipe_path.read_bytes())
    recipe["permitted_environment"]["RUSTC_WRAPPER"] = "/controls/rustc-wrapper.sh"
    recipe_path.write_text(canonical_json(recipe))
    plan["inputs"]["construction_recipe"]["byte_hash"] = sha256(recipe_path.read_bytes())
    with pytest.raises(ValueError, match="recipe cannot override BuildInputs"):
        capture.verify_plan(plan)


def test_stderr_policy_retains_bytes_and_refuses_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = cast(Any, fixtures.plan).__wrapped__(tmp_path, monkeypatch)
    root = tmp_path / "synthetic-capture"
    (root / "traces").mkdir(parents=True)
    (root / "container").mkdir()
    (root / "traces/debug.trace.100").write_text(
        '1.000 execve("/bin/sh", ["sh"], []) = 0\n1.001 +++ exited with 0 +++\n'
    )
    stderr = root / "container/stderr"
    stderr.write_bytes(b"")
    observed = capture.analyze(root, plan, 0)
    assert not observed["read_audit_complete"]
    assert "not an independent loss counter" in observed["loss_state"]
    for diagnostic in (
        b"cat: /canary/absent: No such file or directory\n",
        b"strace: records lost\n",
    ):
        stderr.write_bytes(diagnostic)
        with pytest.raises(ValueError, match="explicit loss and diagnostic reconciliation"):
            capture.analyze(root, plan, 0)
        assert stderr.read_bytes() == diagnostic
