"""Public legacy routing remains byte-identical; v2 uses an explicit closure."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, strict_json_loads
from uarch_contract.rotary_v2 import PreparedBundleV2

from rkuarch.engines.analytic.dispatch import execute
from rkuarch.engines.protocol import EngineResult
from rkuarch.engines.protocol_v2 import generate, validate_engine_result
from rkuarch.table.capture_v2 import capture, replay
from rkuarch.workload.prepared_v2 import physical_assumptions, validate_execution_bundle

from .test_boundary import CASES, active_bundle


def test_legacy_byte_identity_and_dispatch():
    from rkuarch.engines.analytic import core
    from rkuarch.table.build import capture as capture_v1
    from rkuarch.workload.prepared import physical_assumptions as assumptions_v1
    from rkuarch.workload.prepared import validate_execution_bundle as validate_v1

    assert hashlib.sha256(Path(core.__file__).read_bytes()).hexdigest() == (
        "fa3938f8c009c7b80700d35feba7504e4b4da06e628d2e387480c358963974ea"
    )
    b = CASES["literal"]("independent-bundle.json")
    b["intent"]["assumptions_hash"] = assumptions_v1().assumptions_hash
    CASES["rehash"](b)
    c = capture_v1(validate_v1(b), assumptions=assumptions_v1())
    for j, r in zip(c.jobs, c.results, strict=True):
        assert canonical_json(execute(j)) == canonical_json(r)
    with pytest.raises(ValueError):
        PreparedBundleV2.model_validate(b)
    with pytest.raises(ValueError):
        validate_execution_bundle(b)
    new = capture(active_bundle(), assumptions=physical_assumptions())
    with pytest.raises(ValueError):
        validate_v1(new.bundle.model_dump(mode="json"))
    with pytest.raises(ValueError):
        EngineResult.model_validate(new.results[0].model_dump(mode="json"))
    with pytest.raises(ValueError):
        validate_engine_result(
            c.results[0], new.jobs[0], new.bundle, new.request, assumptions=new.assumptions
        )
    wrong = c.jobs[0].model_dump(mode="json")
    wrong["engine"] = new.jobs[0].engine.model_dump(mode="json")
    CASES["seal"](wrong, "job_hash")
    with pytest.raises(ValueError):
        execute(wrong)


def test_v2_subprocess_equality_and_schema_mirrors(tmp_path):
    c = capture(active_bundle(), assumptions=physical_assumptions())
    assert generate(check=True) == []
    bundle = tmp_path / "bundle.json"
    assumptions = tmp_path / "assumptions.json"
    bundle.write_text(canonical_json(c.bundle))
    assumptions.write_text(canonical_json(c.assumptions))
    env = dict(
        os.environ,
        PYTHONPATH=os.pathsep.join((str(Path("src").resolve()), str(Path("contract").resolve()))),
    )
    command = [
        sys.executable,
        "-m",
        "rkuarch.engines.analytic.dispatch",
        "--bundle",
        str(bundle),
        "--assumptions",
        str(assumptions),
    ]
    outputs = [
        subprocess.run(
            command,
            input=canonical_json(c.jobs[0]),
            text=True,
            capture_output=True,
            env=env,
            check=True,
        ).stdout
        for _ in range(3)
    ]
    assert outputs == [canonical_json(c.results[0]) + "\n"] * 3
    imported = strict_json_loads(outputs[0])
    validate_engine_result(imported, c.jobs[0], c.bundle, c.request, assumptions=c.assumptions)
    # Full imported JSON replay does not depend on object identity or producer modules.
    j = [strict_json_loads(canonical_json(x)) for x in c.jobs]
    r = [strict_json_loads(canonical_json(x)) for x in c.results]
    assert (
        replay(
            strict_json_loads(canonical_json(c.bundle)),
            strict_json_loads(canonical_json(c.request)),
            j,
            r,
            assumptions=c.assumptions,
        )
        == c
    )
    for values in ((j[:-1], r[:-1]), (j[::-1], r[::-1]), (j + j, r + r)):
        with pytest.raises(ValueError):
            replay(c.bundle, c.request, *values, assumptions=c.assumptions)
