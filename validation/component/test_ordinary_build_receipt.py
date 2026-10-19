"""Injected mock transport only. No actual build or container lifecycle."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from validation.component import ordinary_build_acceptance as acceptance
from validation.component import ordinary_build_receipt as harness
from validation.component.test_ordinary_build_acceptance import fixture


def setup(root: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    expected, _ = fixture(root)
    saved = {
        name: (root / name).read_bytes() for name in ("stdout", "stderr", "outputs/uarch-engine")
    }
    for name in saved:
        (root / name).unlink()
    (root / "outputs").rmdir()
    return expected, saved


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "exit",
        "exception",
        "timeout",
        "incomplete",
        "oversize",
        "missing",
        "changed-input",
        "truncated",
        "unknown-log-status",
    ],
)
def test_retained_mock_attempt(tmp_path: Path, failure: str | None) -> None:
    expected, saved = setup(tmp_path)
    ticks = iter([1.0, 602.0 if failure == "timeout" else 2.0])

    def transport(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
        assert spec["argv"] == expected["declaration"]["argv"]
        assert spec["environment"] == expected["declaration"]["environment"]
        assert not list((root / "outputs").iterdir())
        for name, data in saved.items():
            if failure == "missing" and name == "stderr":
                continue
            (root / name).write_bytes(
                data
                if not (failure == "oversize" and name == "stderr")
                else b"x" * (expected["stderr_bytes"] + 1)
            )
        if failure == "changed-input":
            (root / expected["declaration"]["inputs"]["source_files"][0]["path"]).write_bytes(
                b"changed"
            )
        if failure == "exception":
            raise RuntimeError("synthetic transport failure")
        return {
            "exit_code": 1 if failure == "exit" else 0,
            "completed": failure != "incomplete",
            "timed_out": False,
            "resource_failure": None,
            "stream_complete": {
                name: failure != "unknown-log-status" for name in ("stdout", "stderr")
            },
            "stream_truncated": {name: failure == "truncated" for name in ("stdout", "stderr")},
            "observed_bytes": {
                name: len((root / name).read_bytes())
                for name in ("stdout", "stderr")
                if (root / name).exists()
            },
        }

    receipt = harness.record_attempt(
        tmp_path,
        expected["declaration"],
        {k: expected[k] for k in ("timeout_s", "stdout_bytes", "stderr_bytes")},
        transport,
        clock=lambda: next(ticks),
    )
    assert (tmp_path / "ordinary-build-receipt.json").is_file()
    if failure is None:
        assert acceptance.consume_build(tmp_path, receipt, expected)["clean_build_success"]
    else:
        with pytest.raises(ValueError):
            acceptance.consume_build(tmp_path, receipt, expected)
        assert (tmp_path / "stdout").is_file()
    if failure == "exception":
        assert (tmp_path / "transport-failure.json").is_file()
    if failure == "oversize":
        assert (tmp_path / "stderr").stat().st_size == expected["stderr_bytes"] + 1


def test_existing_target_refuses_before_transport(tmp_path: Path) -> None:
    expected, _ = setup(tmp_path)
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs/stale").write_bytes(b"old cargo output")

    def forbidden(*args: Any) -> Any:
        raise AssertionError("transport must not start")

    with pytest.raises(FileExistsError):
        harness.record_attempt(
            tmp_path,
            expected["declaration"],
            {k: expected[k] for k in ("timeout_s", "stdout_bytes", "stderr_bytes")},
            forbidden,
        )
    assert (tmp_path / "outputs/stale").read_bytes() == b"old cargo output"
