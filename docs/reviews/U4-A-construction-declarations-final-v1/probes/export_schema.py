"""Export proposed schema/spec data only; no real BuildInputs or construction recipe."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from rkuarch.engines.native.component_construction import (
    FLAGS,
    ConstructionMode,
    construction_modes,
)
from rkuarch.engines.native.component_records import ComponentBuildInputs, ComponentBuildInputsV3

out = Path(sys.argv[1])
out.mkdir(exist_ok=False)
for name, value in {
    "ComponentBuildInputs-v3.schema.json": ComponentBuildInputsV3.model_json_schema(),
    "ComponentBuildInputs-v2.schema.json": ComponentBuildInputs.model_json_schema(),
    "ConstructionMode.schema.json": ConstructionMode.model_json_schema(),
    "production-modes.json": {
        "format": "A-proposed-production-specification/1",
        "mode_configs": construction_modes(FLAGS),
        "authority": None,
    },
}.items():
    (out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
print(
    json.dumps(
        {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(out.iterdir())
        },
        indent=2,
    )
)
