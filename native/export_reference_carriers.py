"""Export the additive native R input shape from the protected carrier definition."""

import argparse
import json
from pathlib import Path
from typing import Any

from uarch_contract.reference import ReferenceJob


def main() -> Any:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = (
        Path(__file__).resolve().parents[1]
        / "native/crates/uarch-engine/src/reference_carriers.json"
    )
    text = json.dumps(ReferenceJob.model_json_schema(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if path.read_text() != text:
            parser.exit(1, "Stale native reference carrier\n")
    else:
        path.write_text(text)
    print(
        "Native reference carrier checked." if args.check else "Native reference carrier exported."
    )


if __name__ == "__main__":
    main()
