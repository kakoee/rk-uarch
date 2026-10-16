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

import importlib.util
import resource

from checks import outcome
from startup_checks import fingerprint, session_checks
from startup_profile import Phases

spec = importlib.util.spec_from_file_location(
    "rkuarch.engines.native.startup_baseline",
    "/sources/baseline/src/rkuarch/engines/native/host.py",
)
baseline = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = baseline
spec.loader.exec_module(baseline)
report["baseline_session_discriminator"] = session_checks(baseline, runner, samples, {})
assert report["baseline_session_discriminator"]["expected_session_available"] is False
expected = {}
phase_reports = []
for mode in ["debug", "release"]:
    phases = Phases()
    restore = phases.install(baseline)
    phases.phase("selector")
    start = time.perf_counter()
    try:
        bound = baseline.resolve_host(mode=mode)
    finally:
        phases.finish()
        restore()
    expected[mode] = fingerprint(bound)
    phase_reports.append(
        {
            "api": "baseline-public",
            "mode": mode,
            "seconds": time.perf_counter() - start,
            "phase_seconds": phases.rows,
            "read_subsets": phases.reads,
        }
    )
    report["startup_phases"] = phase_reports
    save()
    print("Baseline startup", mode, phase_reports[-1]["seconds"], flush=True)
phases = Phases()
restore = phases.install(host)
phases.phase("selector")
start = time.perf_counter()
try:
    with host.resolution_session() as select:
        common_seconds = time.perf_counter() - start
        phases.phase("mode_materialization_and_rehash")
        for mode in ["debug", "release"]:
            assert fingerprint(select(mode=mode)) == expected[mode]
finally:
    phases.finish()
    restore()
phase_reports.append(
    {
        "api": "shared-session",
        "seconds": time.perf_counter() - start,
        "common_seconds": common_seconds,
        "phase_seconds": phases.rows,
        "read_subsets": phases.reads,
    }
)
report["startup_phases"] = phase_reports
save()
print("Shared startup", phase_reports[-1]["seconds"], flush=True)
start = time.perf_counter()
assert fingerprint(host.resolve_host(mode="debug")) == expected["debug"]
report["candidate_public_debug_seconds"] = time.perf_counter() - start
report["candidate_public_invalid_mode"] = outcome(lambda: host.resolve_host(mode="DEBUG"))
assert report["candidate_public_invalid_mode"]["message"] == "explicit debug/release mode required"
save()
print("Fresh public resolution passed; running session fault/isolation controls", flush=True)
report["session_controls"] = session_checks(host, runner, samples, expected)
report["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
report["new_native_calls"] = 0
save()
print("Startup controls passed", flush=True)
