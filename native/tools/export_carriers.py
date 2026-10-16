"""Export installed carrier shapes as owned Rust validation input, not new semantics.

Semantic joins remain explicit Rust code. No protected schema is changed. Run with
this repository's verified contract environment; --check never rewrites outputs.
"""

import argparse
import json
from pathlib import Path

from uarch_contract.mapped import MappedEngineJob

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
schema = MappedEngineJob.model_json_schema()
# Restrict the executable's schema to the supported K2 branch, without modifying
# the installed DTO or dropping validation of any admitted branch.
# Unsupported branches are refused explicitly before shape validation.
for name in ("MappedBundle",):
    schema["$defs"][name]["properties"]["source"] = {"type": "null"}
    schema["$defs"][name]["properties"]["scope"] = {"$ref": "#/$defs/KernelScope"}
schema["$defs"]["TaskGraph"]["properties"]["jobs"]["items"] = {"$ref": "#/$defs/FixedDelay"}


# Prune unreachable definitions, leaving every field of the admitted closure.
def refs(value):
    if isinstance(value, dict):
        if "$ref" in value:
            yield value["$ref"].split("/")[-1]
        for k, child in value.items():
            if k != "$defs":
                yield from refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs(child)


seen = set()
pending = list(refs(schema))
while pending:
    key = pending.pop()
    if key not in seen:
        seen.add(key)
        pending.extend(refs(schema["$defs"][key]))
schema["$defs"] = {k: schema["$defs"][k] for k in sorted(seen)}
output = root / "crates/uarch-engine/src/carriers.json"
data = (json.dumps(schema, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
if args.check:
    assert output.read_bytes() == data, "Installed carrier export changed"
else:
    output.write_bytes(data)
