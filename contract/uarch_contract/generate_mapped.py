"""Generate/check only M's additive contract/schema/mapped mirrors.

Uses current dependencies, never vendors artifacts or writes v1 mirrors. Check is read-only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .mapped import SCHEMA_ROOTS

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "schema/mapped"


def schemas() -> dict[str, str]:
    result = {}
    for model in SCHEMA_ROOTS:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        result[model.__name__ + ".json"] = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    return result


def generate(output: Path = DEFAULT_OUTPUT, *, check: bool = False) -> list[str]:
    expected = schemas()
    actual = {p.name: p.read_text() for p in output.glob("*.json")}
    stale = sorted(k for k in actual.keys() | expected.keys() if actual.get(k) != expected.get(k))
    if not check:
        unexpected = sorted(actual.keys() - expected.keys())
        if unexpected:
            raise ValueError("Refusing unexpected schema files: " + ", ".join(unexpected))
        output.mkdir(parents=True, exist_ok=True)
        for name, text in expected.items():
            (output / name).write_text(text)
    return stale


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    stale = generate(args.output, check=args.check)
    if args.check and stale:
        parser.exit(1, "Stale mapped schemas: " + ", ".join(stale) + "\n")
    print("Mapped schemas are fresh." if args.check else "Generated mapped schemas.")


if __name__ == "__main__":
    main()
