"""Hash/import checks only; no build, campaign, capture or startup-integrity verification."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from native.tools import component_runtime_candidate as preparation
from validation.component import capture_monitor, ordinary_eof_campaign
from validation.component.ordinary_eof_acceptance import verify_closure

A = "docs/reviews/U4-A-activation-combined-preparation-v1"
root = Path.cwd()
observation_root = Path(sys.argv[1])
old_payload = json.loads(
    (observation_root / "private-component/prospective-payload.json").read_bytes()
)
observation = old_payload["consumers"]["observation_contract"]
assert (
    "sha256:" + hashlib.sha256((observation_root / observation["path"]).read_bytes()).hexdigest()
    == observation["byte_hash"]
)
result = preparation.imports(root, observation_root=observation_root)
assert result["independent_binding"]["path"] == A + "/activation-consumer-bindings.json"
pins = json.loads((root / result["independent_binding"]["path"]).read_bytes())["files"]
inventory = {row["path"]: row["byte_hash"].removeprefix("sha256:") for row in result["files"]}
assert all(inventory.get(path) == pin for path, pin in pins.items())
assert inventory[capture_monitor.PARSER] == capture_monitor.PARSER_HASH
assert ordinary_eof_campaign.cleanup_owned is capture_monitor.cleanup_owned
verify_closure({"source": str(root), "pins": pins})
refusals = {}
for module in ("ordinary_eof_campaign", "capture_monitor"):
    path = f"validation/component/{module}.py"
    bad = dict(pins)
    del bad[path]
    try:
        verify_closure({"source": str(root), "pins": bad})
    except ValueError as error:
        assert "complete matching consumer/structural closure" in str(error)
        refusals["missing:" + path] = str(error)
    else:
        raise AssertionError("missing module accepted")
bad = dict(pins)
bad["native/tools/component_runtime_candidate.py"] = (
    "5eb07277a2f062ae07a7c6abbf23d750fe3094e5bab6c93fcadc2dd05a0d6717"
)
try:
    verify_closure({"source": str(root), "pins": bad})
except ValueError as error:
    assert "consumer source mismatch: native/tools/component_runtime_candidate.py" in str(error)
    refusals["stale:B-preparation"] = str(error)
else:
    raise AssertionError("stale preparation accepted")
origins = {}
for name, module in sorted(sys.modules.copy().items()):
    if name.split(".")[0] in ("native", "rkuarch", "uarch_contract", "validation"):
        origin = getattr(module, "__file__", None)
        if origin:
            path = Path(origin).resolve()
            assert path.is_relative_to(root), (name, path)
            origins[name] = {
                "path": str(path.relative_to(root)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
record = {
    "format": "A-combined-executed-preparation-check/1",
    "independent_binding": result["independent_binding"],
    "runtime_consumer_pins": len(pins),
    "project_import_files": len(inventory),
    "project_import_inventory": inventory,
    "external_files": len(result["external_files"]),
    "python_executable": result["python_executable"],
    "inherited_observation": observation,
    "missing_and_stale_refusals": refusals,
    "origin_checks": origins,
    "campaign_or_capture_execution": False,
    "new_build_identity": None,
}
Path(sys.argv[2]).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(
    json.dumps(
        {k: v for k, v in record.items() if k not in ("origin_checks", "project_import_inventory")},
        indent=2,
    )
)
