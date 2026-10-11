"""Separate received historical20 and current adopted48; neither is a synthetic oracle."""

import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

import pytest

from contract.tests import nominal_candidate
from contract.tests.historical_snapshot import (
    HISTORICAL_MANIFEST,
    authenticate_historical,
    historical_snapshot,
)
from scripts import u2_inputs as ui
from scripts import vendor_rk as vr
from tests import u2_comparison, u2_refresh

ROOT = Path(__file__).resolve().parents[2]
CURRENT_MANIFEST = "20eee19b0e864ad07a7b122da7544e385116fdd50d279e1fac1bfbbf03a697ad"
REVIEW_SHA256 = "55787e09a751b67b28b90835ad96041040b1a0dd9cb85ba16538c27fb7597861"


def test_historical_fixture_is_complete_and_relocatable(tmp_path: Path) -> None:
    source = historical_snapshot()
    destination = tmp_path / "cold-clone" / "historical"
    shutil.copytree(source, destination)
    assert authenticate_historical(destination) == destination
    assert hashlib.sha256((destination / "MANIFEST.json").read_bytes()).hexdigest() == (
        HISTORICAL_MANIFEST
    )
    assert len(json.loads((destination / "parity/fixtures.json").read_bytes())) == 864
    assert len(json.loads((destination / "parity/refusals.json").read_bytes())) == 2
    with pytest.raises(ValueError, match="fingerprint"):
        vr.check_generator(destination)


@pytest.mark.parametrize("mutation", ["member", "missing", "extra", "rehashed"])
def test_historical_fixture_refuses_changed_bytes_or_inventory(
    tmp_path: Path, mutation: str
) -> None:
    destination = tmp_path / "historical"
    shutil.copytree(historical_snapshot(), destination)
    path = destination / "schema.json"
    if mutation == "missing":
        path.unlink()  # Negative control in a new temporary copy only.
    elif mutation == "extra":
        (destination / "extra.json").write_text("{}")
    else:
        path.write_bytes(path.read_bytes() + b"\n")
        if mutation == "rehashed":
            manifest = json.loads((destination / "MANIFEST.json").read_bytes())
            manifest["files"]["schema.json"] = hashlib.sha256(path.read_bytes()).hexdigest()
            (destination / "MANIFEST.json").write_bytes(vr.canonical(manifest))
    with pytest.raises(ValueError, match="historical test"):
        authenticate_historical(destination)


def test_current_canonical_is_exact_adopted_1008_four_real_refusals() -> None:
    root = ui.ADOPTED
    assert vr.digest((root / "MANIFEST.json").read_bytes()) == CURRENT_MANIFEST
    assert root == ROOT / "contract/vendor" / f"rk-sim@{vr.PIN}"
    assert not (root / "SYNTHETIC-REFERENCE").exists()
    audit = u2_refresh.audit_candidate(root)
    assert audit["rows"] == 1008 and audit["adopted"] is False
    rows = json.loads((root / "parity/fixtures.json").read_bytes())
    assert len({row["id"] for row in rows}) == 1008
    assert Counter(row["query"]["phase"] for row in rows) == {"prefill": 504, "decode": 504}
    assert all("vector_ops" not in row["counts"] for row in rows)
    assert all(
        row["counts"]["memory_write_bytes"] is None
        for row in rows
        if row["query"]["phase"] == "decode"
    )
    events = json.loads((root / "parity/refusals.json").read_bytes())
    assert len(events) == 4
    assert {
        (Path(e["component_params_file"]).name, e["compute"], e["kv_cache"]) for e in events
    } == {
        ("asic_placeholder.yaml", "bf16", "bf16"),
        ("asic_placeholder.yaml", "fp8", "fp8"),
        ("npu-l4.yaml", "fp16", "fp16"),
        ("npu-l4.yaml", "fp8", "fp8"),
    }
    source_hash = vr.digest((root / "rk/engine/f0/compute.py").read_bytes())
    for event in events:
        assert event["callable_source_sha256"] == source_hash
        assert event["component_params_sha256"] == vr.digest(
            (root / event["component_params_file"]).read_bytes()
        )
        assert event["rk_sha"] == vr.PIN and event["execution"] == "refused"
        assert event["exception"] == "UnsupportedPrecision"
        assert event["boundary"] == "Accelerator.peak_op_per_s"
    review = ROOT / "tests/fixtures/u2_b/received-adoption-review.json"
    assert vr.digest(review.read_bytes()) == REVIEW_SHA256
    accepted = u2_refresh.adoption_authority(root, review, REVIEW_SHA256)
    assert accepted.reviewed_subject_hashes == ("sha256:" + CURRENT_MANIFEST,)


def test_historical_guard_refuses_current_canonical_before_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert vr.digest((ui.ADOPTED / "MANIFEST.json").read_bytes()) == CURRENT_MANIFEST
    directory = tmp_path / "inputs"
    inputs = ui.load_inputs(directory, ui.prepare_inputs(directory))
    monkeypatch.setattr(
        nominal_candidate, "evaluate_nominal", lambda *a: pytest.fail("candidate called")
    )
    with pytest.raises(ValueError, match="historical adopted identity changed"):
        u2_comparison.run_historical(inputs)
