"""Synthetic unapplied D3 wrapper regression; no native invocation or genuine session."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = ROOT / (
    "docs/reviews/U4-A-component-activation-final-join-v1/proposals/component_negative-v7.py.txt"
)


@pytest.mark.parametrize("final_time", [9, 10, 11], ids=["success", "exact-deadline", "expired"])
def test_d3_final_outcome_is_persisted_before_return_or_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, final_time: int
) -> None:
    # Baseline evidence explicitly selects the preserved v6 file. Default is the new proposal.
    source = Path(os.environ.get("U4_D3_PROPOSAL", str(PROPOSAL)))
    loader = SourceFileLoader("private_d3_finalization", str(source))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, loader.name, module)
    loader.exec_module(module)

    class SyntheticSession:
        _deadline = 10

        def claim(self, case_id: str) -> tuple[None, None]:
            assert case_id == "synthetic-wrapper-only"
            return None, None

    monkeypatch.setattr(module, "NegativeSession", SyntheticSession)
    clock = iter([2, final_time])
    monkeypatch.setattr(module, "time", SimpleNamespace(monotonic=lambda: next(clock)))
    receipt = tmp_path / "attempt.json"
    initial = {
        "validation_passed": True,
        "failure_stage": None,
        "status": 2,
        "runtime_entries": None,
        "retained_stream_sentinel": "unchanged synthetic evidence",
    }
    events: list[str] = []
    saves: list[bytes] = []
    actual_save = module._save

    def save(path: Path, value: Any) -> None:
        actual_save(path, value)
        saves.append(path.read_bytes())
        events.append("save")

    def core(*args: Any, **kwargs: Any) -> dict[str, Any]:
        assert kwargs["timeout_s"] == 8  # The call starts before expiry.
        assert kwargs["repetition"] == 2
        value = dict(initial)
        module._save(receipt, value)
        return value

    monkeypatch.setattr(module, "_save", save)
    monkeypatch.setattr(module, "_run_negative_image", core)
    if final_time > 10:
        with pytest.raises(ValueError, match="D3 session deadline exhausted"):
            try:
                module.run_negative(
                    "synthetic-wrapper-only",
                    session=SyntheticSession(),
                    evidence_root=tmp_path,
                    repetition=2,
                )
            except ValueError:
                events.append("raised")
                # Observe durable state at the exception boundary, before any recovery.
                retained = json.loads(receipt.read_bytes())
                assert retained["validation_passed"] is False
                assert retained["failure_stage"] == "session-finalization"
                assert retained["finalization_error"] == (
                    "HostBindingError('D3 session deadline exhausted')"
                )
                assert {
                    k: retained[k]
                    for k in initial
                    if k not in ("validation_passed", "failure_stage")
                } == {
                    k: initial[k]
                    for k in initial
                    if k not in ("validation_passed", "failure_stage")
                }
                raise
        assert events == ["save", "save", "raised"]
        assert json.loads(saves[0]) == initial
        assert saves[-1] == receipt.read_bytes()
    else:
        returned = module.run_negative(
            "synthetic-wrapper-only",
            session=SyntheticSession(),
            evidence_root=tmp_path,
            repetition=2,
        )
        events.append("returned")
        assert returned == json.loads(receipt.read_bytes()) == initial
        assert "finalization_error" not in returned
        assert saves == [receipt.read_bytes()]
        assert events == ["save", "returned"]
