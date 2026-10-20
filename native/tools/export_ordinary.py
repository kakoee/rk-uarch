"""Export/check the ordinary /4 Rust carrier; no source identity generation."""
import argparse
import json
from pathlib import Path

from uarch_contract.ordinary import OrdinaryJob

parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
output = Path(__file__).resolve().parents[1] / "crates/uarch-engine/src/ordinary_carriers.json"
data = (json.dumps(OrdinaryJob.model_json_schema(), sort_keys=True, indent=2) + "\n").encode()
if args.check:
    if output.read_bytes() != data:
        parser.exit(1, "Ordinary native carrier is stale\n")
else:
    output.write_bytes(data)
