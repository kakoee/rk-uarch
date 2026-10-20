"""Bounded ordinary executable checks; an explicit locally built binary is required."""

import os
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, content_hash, strict_json_loads
from uarch_contract.ordinary import OrdinaryJob

from rkuarch.engines.native.ordinary import consume, replay, run
from tests.unit.test_ordinary_native import job_data, production_data

pytestmark = pytest.mark.native


@pytest.fixture(scope="module")
def executable():
    value = os.environ.get("ORDINARY_NATIVE")
    if value is None:
        pytest.skip("explicit ordinary binary required")
    return Path(value)


def invoke(executable, raw, test_only=False):
    return subprocess.run(
        [str(executable), "--protocol", "uarch-engine/4"] + (["--test-only"] if test_only else []),
        input=raw,
        capture_output=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("fixture", [False, True])
def test_positive_and_replay(executable, tmp_path, fixture):
    raw = job_data() if fixture else production_data()
    saved, output = tmp_path / "job.json", tmp_path / "result.json"
    saved.write_text(canonical_json(raw))
    result = run(saved, executable=executable, test_only=fixture)
    output.write_text(canonical_json(result))
    assert replay(saved, output, test_only=fixture) == result
    assert result.duration_ps == (121000 if fixture else 656000)
    # New valid data need no compiled inventory or per-case approval.
    raw["seed"] = 167
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    assert invoke(executable, canonical_json(raw).encode(), fixture).returncode == 0


@pytest.mark.parametrize(
    "fault,code",
    [
        ("model", "InvalidCarrier"),
        ("hash", "ContentHashMismatch"),
        ("owner", "InvalidResource"),
        ("old", "UnsupportedProtocol"),
        ("profile", "InvalidCarrier"),
        ("fixture", "AdmissionMismatch"),
    ],
)
def test_native_discriminating_refusals(executable, fault, code):
    raw = production_data()
    if fault == "model":
        raw["engine"]["model"]["version"] = "1"
    elif fault == "hash":
        raw["job_hash"] = "sha256:" + "0" * 64
    elif fault == "owner":
        raw["owners"][0]["resource"] = "unknown"
    elif fault == "old":
        raw["protocol"] = "uarch-engine/3"
    elif fault == "profile":
        raw["profile"] = {}
    elif fault == "fixture":
        raw = job_data()
    if fault != "hash":
        raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    result = invoke(executable, canonical_json(raw).encode())
    assert result.returncode == 2 and not result.stdout
    assert strict_json_loads(result.stderr)["code"] == code


def test_wrong_results_and_independent_laws(executable):
    from rkuarch.engines.native.ordinary import UNREPRESENTED
    from rkuarch.verification.component.observations_v3 import check_v3

    job = OrdinaryJob.model_validate(production_data())
    process = invoke(executable, canonical_json(job).encode())
    assert process.returncode == 0
    result = strict_json_loads(process.stdout)
    for kind in ("model", "binding", "duration", "observation"):
        bad = deepcopy(result)
        if kind == "model":
            bad["engine"]["model"]["version"] = "1"
        elif kind == "binding":
            bad["job_hash"] = "sha256:" + "0" * 64
        elif kind == "duration":
            bad["duration_ps"] += 1
        else:
            bad["observations"]["format"] = "uarch-native-observations/2"
        bad["result_hash"] = content_hash(bad, exclude=("result_hash",))
        with pytest.raises(ValueError):
            consume(canonical_json(bad).encode(), b"", 0, job=job)
    # Exercise the independent checker itself, without leaning on data hashes/schema.
    bad = deepcopy(result)
    phase = next(
        x
        for x in bad["observations"]["activities"]["records"]
        if x["kind"] == "service" and x["subphase"] == "compute_wave"
    )
    phase["end_ps"] += 1
    with pytest.raises(ValueError):
        check_v3(job.model_dump(mode="json"), bad, {"unrepresented": UNREPRESENTED})
