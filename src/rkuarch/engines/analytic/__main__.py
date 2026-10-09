"""One strict EngineJob on stdin, one EngineResult on stdout; failures go to stderr."""

import sys

from uarch_contract.hashing import canonical_json, strict_json_loads

from rkuarch.engines.protocol import EngineJob

from .core import run_analytic


def main() -> int:
    try:
        job = EngineJob.model_validate(strict_json_loads(sys.stdin.buffer.read()))
        sys.stdout.buffer.write(canonical_json(run_analytic(job)).encode() + b"\n")
    except (ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
