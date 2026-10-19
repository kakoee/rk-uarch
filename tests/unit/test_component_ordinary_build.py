"""Synthetic ordinary-build planning; no command, Docker, native or startup execution."""

from pathlib import Path

import pytest

from native.tools import component_ordinary_build as ordinary
from rkuarch.engines.native.component_construction import FLAGS, construction_modes
from rkuarch.engines.native.component_records import ComponentBuildInputsV3


def inputs() -> ComponentBuildInputsV3:
    pin = "sha256:" + "1" * 64
    source = "native/tools/component_runtime_candidate.py"
    return ComponentBuildInputsV3.model_validate(
        {
            "format": "uarch-component-build-inputs/3",
            "source_commit": "1" * 40,
            "source_files": [{"path": source, "byte_hash": pin, "role": "config"}],
            "trust_hash": pin,
            "trust_file": {"path": "trust.json", "byte_hash": pin},
            "tool_inputs_hash": pin,
            "tool_inputs_file": {"path": "tools.json", "byte_hash": pin},
            "model_source_paths": [source],
            "model_inputs_hash": pin,
            "mode_configs": construction_modes(FLAGS),
            "generated_identity_output_paths": ["native/crates/uarch-engine/generated/identity.rs"],
        }
    )


@pytest.mark.parametrize("mode", ["debug", "release"])
def test_ordinary_plan_keeps_exact_command_without_tracing(tmp_path: Path, mode: str) -> None:
    root, output = tmp_path / "prepared", tmp_path / "first" / mode
    plan = ordinary.plan(root, output, mode, inputs())
    args = plan["container_argv"]
    assert args[-len(plan["child_argv"]) :] == plan["child_argv"]
    assert args.count(f"link-arg=-Wl,-Map=/receipts/{mode}.map") == 1
    assert plan["environment"]["C2_RUN_TAG"] == mode + "-build"
    assert len(plan["environment"]) == 11
    assert not any("strace" in arg or "canary" in arg for arg in args)
    assert "capture-child" not in args
    assert not output.exists()
    assert plan["limits"]["timeout_s"] == 600
    assert plan["layout"]["target"] == str(output / "target")
    assert plan["layout"]["artifact"] == str(output / "target" / mode / "uarch-engine")


@pytest.mark.parametrize("kind", ["relative", "source", "cache", "parent", "comma"])
def test_ordinary_output_cannot_alias_inputs(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "prepared"
    choices = {
        "relative": Path("relative"),
        "source": root / "source" / "output",
        "cache": root / "cache",
        "parent": tmp_path,
        "comma": tmp_path / "bad,root",
    }
    with pytest.raises(ValueError, match="ordinary build roots"):
        ordinary.plan(root, choices[kind], "debug", inputs())


def test_fresh_outputs_refuse_existing_targets(tmp_path: Path) -> None:
    output = tmp_path / "first" / "debug"
    plan = ordinary.plan(tmp_path / "prepared", output, "debug", inputs())
    ordinary.create_outputs(plan)
    assert sorted(p.name for p in output.iterdir()) == ["receipts"]
    (output / "receipts" / "stale").write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        ordinary.create_outputs(plan)
    assert (output / "receipts" / "stale").read_bytes() == b"preserve"


@pytest.mark.parametrize("explicit", [True, False])
def test_guardian_environment_is_forwarded_without_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    explicit: bool,
) -> None:
    """Only Popen is replaced; no child process, Docker or startup path executes."""
    import json
    import subprocess
    from typing import Any

    from native.tools import component_container_guard as guardian

    calls: list[dict[str, Any]] = []

    class Process:
        def __init__(self, argv: list[str], **kwargs: Any) -> None:
            calls.append(kwargs)
            directory = Path(argv[-2])
            guardian.save(directory / "cleanup.json", {"stopped": True, "removed": True})

        def wait(self, *, timeout: float) -> None:
            assert timeout == 635

    monkeypatch.setattr(subprocess, "Popen", Process)
    env = ordinary.HOST_ENVIRONMENT if explicit else None
    result = guardian.run_container(tmp_path / "synthetic", ["inert"], timeout=600, environment=env)
    assert result == {"stopped": True, "removed": True}
    assert calls[0]["env"] == env
    intent = json.loads((tmp_path / "synthetic/intent.json").read_bytes())
    assert ("environment" in intent) == explicit
    if explicit:
        assert intent["environment"] == env
