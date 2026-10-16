# ruff: noqa: E402
# Imports deliberately follow sealed-runtime and origin checks.
"""Explicit private imports, sealed runtime, genuine resolver, Python-only replay."""

import importlib.metadata
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/campaign")
import entrypoint as frozen

sys.path.insert(0, "/checks")
from checks import sha

START = time.perf_counter()


def deny(event, args):
    if event in {
        "subprocess.Popen",
        "os.system",
        "os.exec",
        "os.posix_spawn",
        "os.spawn",
        "os.fork",
        "os.forkpty",
    }:
        raise RuntimeError("Python diagnostic prohibits process execution: " + event)


sys.addaudithook(deny)


def forbidden(*args, **kwargs):
    raise RuntimeError("Python diagnostic prohibits process execution")


subprocess.Popen = forbidden
assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
assert sys.version_info[:3] == (3, 12, 14)
assert Path(sys.executable) == Path("/python/bin/python3.12")
assert os.getuid() == os.geteuid() == 1000
for root in [
    "/",
    "/python",
    "/site",
    "/candidate",
    "/campaign",
    "/manifests",
    "/proposal",
    "/saved",
    "/checks",
]:
    assert os.statvfs(root).f_flag & os.ST_RDONLY, root
frozen.frozen_tree("/campaign", frozen.read_json(Path("/manifests/campaign-files.json")))
runtime = frozen.read_json(Path("/campaign/runtime.json"))
for name, root in [("python-files.json", "/python"), ("site-files.json", "/site")]:
    data = (Path("/manifests") / name).read_bytes()
    assert sha(data) == runtime["inventories"][name]
    frozen.frozen_tree(root, json.loads(data))
for path, expected in runtime["image_libraries"].items():
    assert sha(Path(path).read_bytes()) == expected
sys.path[:0] = [
    "/site",
    "/proposal/src",
    "/proposal/contract",
    "/candidate/docs/reviews/U4-B-K2-construction-audit-v1",
]
sys.meta_path.insert(0, frozen.NoProducers())
for name, expected in runtime["package_versions"].items():
    assert importlib.metadata.version(name) == expected
from deployment import verify_bytes

verify_bytes(
    Path("/candidate"),
    frozen.read_json(Path("/campaign/candidate-layout.json"))["files"],
    sealed=True,
)

from rkuarch.engines.native import host, runner

for name, module in tuple(sys.modules.items()):
    f = getattr(module, "__file__", None)
    if f and name.startswith(("rkuarch", "uarch_contract")):
        assert Path(f).is_relative_to("/proposal"), (name, f)
answers = json.loads(
    Path("/candidate/docs/reviews/U4-A-K2-construction-v1/corpus/expectations.json").read_bytes()
)
samples = []
for case in ["K01", "K02", "K03-owner", "K04"]:
    row = json.loads((Path("/saved/calls") / ("debug-0-" + case + ".json")).read_bytes())
    sample = {"case": case, "answer": answers[case], "receipt": row["receipt"]}
    for field in ["request", "stdout", "stderr"]:
        data = (Path("/saved") / row[field]).read_bytes()
        assert sha(data) == row[field + "_hash"]
        sample[field] = data
    assert row["status"] == 0
    samples.append(sample)
report = {
    "kind": "Python-only saved-output replay; zero native executions",
    "source_hashes": {
        str(p.relative_to("/proposal")): sha(p.read_bytes())
        for p in Path("/proposal").rglob("*.py")
    },
    "test_hashes": {p.name: sha(p.read_bytes()) for p in Path("/checks").glob("*.py")},
    "runtime": runtime,
    "startup_seconds": time.perf_counter() - START,
}


def save():
    Path("/receipts/report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


save()
print("Verified sealed runtime and private imports; resolving genuine debug host", flush=True)
start = time.perf_counter()
bound = host.resolve_host(mode="debug")
report["debug_resolver_seconds"] = time.perf_counter() - start
report["host"] = {
    "selector": bound.selector.model_dump(mode="json"),
    "executable": bound.executable.model_dump(mode="json"),
}
save()
from authority_controls import authority_controls

report["authority_controls"] = authority_controls(runner, bound, samples)
save()
print("Authority controls", [x["equivalent"] for x in report["authority_controls"]], flush=True)
