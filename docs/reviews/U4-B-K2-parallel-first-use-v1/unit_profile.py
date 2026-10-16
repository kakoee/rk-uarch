"""Existing host pytest, explicit private roots, no public native selection."""

import argparse
import contextlib
import hashlib
import io
import json
import os
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--profile", choices=["fast", "broader"], required=True)
    args = p.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    helpers = Path(__file__).resolve().parent
    assert source.is_relative_to("/tmp") and helpers.is_relative_to("/tmp")
    assert sys.flags.isolated and sys.dont_write_bytecode
    assert all(
        k not in os.environ for k in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN")
    )
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    output.mkdir(exist_ok=False)
    config = output / "pytest.ini"
    config.write_text("[pytest]\n")
    sys.path[:0] = [str(source / "src"), str(source / "contract"), str(helpers)]
    import pytest

    selected = [helpers / "test_parallel.py"] + [
        source / "tests/unit" / name
        for name in ["test_u4_k2_process.py", "test_u4_k2_host_paths.py"]
    ]
    if args.profile == "broader":
        selected.append(source / "tests/unit/test_u4_k2_host_records.py")
    nodes = []

    class Collection:
        def pytest_collection_finish(self, session):
            nodes.extend(item.nodeid for item in session.items)

    argv = ["-q", "-c", str(config), "--rootdir", str(source), *map(str, selected)]
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        code = pytest.main(argv, plugins=[Collection()])
    (output / "pytest.txt").write_text(stream.getvalue())
    origins = {}
    sealed = Path("/var/lib/rkuarch/k2/candidate-04-first-use-v1/candidate")
    for name, module in sys.modules.copy().items():
        file = getattr(module, "__file__", None)
        if file and name.startswith(("rkuarch", "uarch_contract")):
            path = Path(file).resolve()
            assert path.is_relative_to(source), (name, path)
            relative = path.relative_to(source)
            assert path.read_bytes() == (sealed / relative).read_bytes(), relative
            origins[name] = {
                "path": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
    assert origins and nodes and len(nodes) == len(set(nodes))
    (output / "receipt.json").write_text(
        json.dumps(
            {
                "profile": args.profile,
                "pytest_argv": argv,
                "exit_code": int(code),
                "collected": len(nodes),
                "nodes": nodes,
                "origins": origins,
                "source": "24fa36803081e5077d5977baa91441a2c8534ec8",
                "native_mapped_calls": 0,
                "authority": "synthetic unit fixtures only if broader; none qualifies",
            },
            indent=2,
        )
        + "\n"
    )
    print(stream.getvalue())
    raise SystemExit(code)


if __name__ == "__main__":
    main()
