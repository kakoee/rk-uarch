"""Generate/check the additive reference schema mirrors; no vendor snapshot mutation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .reference import ReferenceBundle, ReferenceJob, ReferenceResult, TpuV5eReference

ROOTS = (ReferenceBundle, ReferenceJob, ReferenceResult, TpuV5eReference)
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "schema/reference"


def schemas() -> Any:
    result = {}
    for model in ROOTS:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        result[model.__name__ + ".json"] = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    return result


def generate(output: Any = DEFAULT_OUTPUT, *, check: Any = False) -> Any:
    expected = schemas()
    actual = {p.name: p.read_text() for p in output.glob("*.json")}
    stale = sorted(k for k in expected.keys() | actual.keys() if expected.get(k) != actual.get(k))
    if not check:
        if actual.keys() - expected.keys():
            raise ValueError("Unexpected reference schema files")
        output.mkdir(parents=True, exist_ok=True)
        for name, text in expected.items():
            (output / name).write_text(text)
    return stale


def main() -> Any:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = generate(check=args.check)
    if args.check and stale:
        parser.exit(1, "Stale reference schemas: " + ", ".join(stale) + "\n")
    print("Reference schemas checked." if args.check else "Reference schemas generated.")


if __name__ == "__main__":
    main()
