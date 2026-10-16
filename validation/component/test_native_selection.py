"""Native positives stay outside ordinary unit selections until released result inputs exist.

This consumes six actual public-run outputs, not synthetic expectations. It launches no
engine: the component runner and first-use release are still upstream dependencies.
The supplied directory is an evidence input, never authority; these assertions alone
cannot authenticate execution or replace review of the genuine operational receipts.
"""

import json
import os
from pathlib import Path

import pytest
from uarch_contract.mapped import MappedEngineJob, MappedEngineResult

from validation.component.corpus import build
from validation.component.selection import assert_case, assert_replays


@pytest.mark.native
def test_released_public_component_observations():
    location = os.environ.get("RKUARCH_B_COMPONENT_RESULTS")
    if location is None:
        pytest.skip("B-native: actual released component engine/build/authority/results absent")
    directory = Path(location)
    corpus = build()
    # Complete selection is required; no caller-selectable passing subset.
    for name, item in corpus["items"].items():
        if item["expected"]["outcome"] != "success":
            continue  # Refusals require the released admission/runner path, tracked separately.
        case = directory / name
        job = MappedEngineJob.model_validate_json((case / "job.json").read_bytes())
        observations = json.loads((case / "observation-contract.json").read_bytes())
        outputs = {
            (mode, run): (case / f"{mode}-{run}.json").read_bytes()
            for mode in ("debug", "release")
            for run in range(3)
        }
        assert_replays(outputs)
        for raw in outputs.values():
            assert_case(job, MappedEngineResult.model_validate_json(raw), item, observations)
