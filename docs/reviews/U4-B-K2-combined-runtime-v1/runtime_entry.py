"""Separate Python imports; original native source/authority and reviewed scheduler.

Only packaging hooks are replaced. Original authority(), replay() and all case,
fork, transport, semantic, independent-result and membership controls are retained.
"""

import importlib.metadata
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

import bindings as b

PROJECT = Path("/project")
HELPERS = Path("/combined")
RECORD = Path("/combined-record")
AUTHORITY = Path("/combined-authority")
OUT = Path("/receipts")
BASE = None
CONTEXT = None
BINDING = None
PRIVATE = False


def common():
    c, data, publication = b.check_payload(PROJECT, HELPERS, RECORD, sealed=not PRIVATE)
    b.old_bindings("/", c)
    b.need(os.getuid() == os.geteuid() == 1000, "UID1000 required")
    b.need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, "-I -S -B")
    b.need(sys.version_info[:3] == (3, 12, 14), "exact Python")
    b.need(
        Path(sys.executable) == Path("/python/bin/python3.12")
        and Path(sys.base_prefix) == Path("/python"),
        "mounted Python",
    )
    b.need(
        set(os.environ) <= {"PATH", "LC_ALL"} and os.environ.get("PATH") == "/usr/bin:/bin",
        "clean environment",
    )
    for root in (
        "/",
        "/python",
        "/site",
        "/candidate",
        "/campaign",
        "/manifests",
        "/project",
        "/combined",
        "/combined-record",
    ):
        b.need(os.statvfs(root).f_flag & os.ST_RDONLY, "read-only mount: " + root)
    BASE.frozen_tree("/campaign", b.read("/manifests/campaign-files.json"))
    runtime = b.read("/campaign/runtime.json")
    for name, root in [("python-files.json", "/python"), ("site-files.json", "/site")]:
        raw = (Path("/manifests") / name).read_bytes()
        b.need(b.digest(raw) == runtime["inventories"][name], "accepted runtime inventory")
        BASE.frozen_tree(root, json.loads(raw))
    for path, expected in runtime["image_libraries"].items():
        b.need(b.digest(Path(path).read_bytes()) == expected, "image library/search-state")
    # No old source path on sys.path. The unchanged B checker has its own bound path.
    paths = [
        "/site",
        str(PROJECT / "src"),
        str(PROJECT / "contract"),
        "/campaign",
        "/candidate/docs/reviews/U4-B-K2-construction-audit-v1",
    ]
    for path in reversed(paths):
        if path not in sys.path:
            sys.path.insert(0, path)
    b.need(
        "/candidate/src" not in sys.path and "/candidate/contract" not in sys.path,
        "no build-source import fallback",
    )
    if not any(isinstance(x, BASE.NoProducers) for x in sys.meta_path):
        sys.meta_path.insert(0, BASE.NoProducers())
    for name, version in runtime["package_versions"].items():
        b.need(importlib.metadata.version(name) == version, "package version: " + name)
    from deployment import slots, verify_bytes
    from first_use_checks import check_real_result
    from uarch_contract.hashing import canonical_json, content_hash
    from uarch_contract.mapped import MappedEngineJob

    # isort: split
    from rkuarch.engines.native import host, runner

    verify_bytes("/candidate", b.read("/campaign/candidate-layout.json")["files"], sealed=True)
    plan = b.read("/campaign/campaign-plan.json")
    b.need(plan["subject"] == c["native_subject"], "original native subject")
    work = slots(plan)
    b.origins(sys.modules, PROJECT)
    return (
        runtime,
        plan,
        work,
        host,
        runner,
        canonical_json,
        content_hash,
        MappedEngineJob,
        check_real_result,
    )


def guards(base=None):
    c, data, publication = b.check_payload(PROJECT, HELPERS, RECORD, sealed=not PRIVATE)
    b.old_bindings("/", c)
    return b.read(HELPERS / "parallel-policy.json"), b.digest(b.encoded(c["helpers"]))


def release(policy=None, manifest_hash=None):
    b.need(not PRIVATE, "private composition cannot authorize execution")
    c, data, publication = b.check_payload(PROJECT, HELPERS, RECORD, sealed=not PRIVATE)
    b.old_bindings("/", c)
    b.need(os.statvfs(AUTHORITY).f_flag & os.ST_RDONLY, "immutable runtime authority mount")
    b.inventory(
        AUTHORITY, {p.name: b.digest(p.read_bytes()) for p in AUTHORITY.iterdir()}, sealed=True
    )
    result = b.check_authority(AUTHORITY, data, publication)
    b.need(BINDING is None or result == BINDING, "runtime authority changed during operation")
    return result


def snapshots():
    from parallel_core import snapshot_paths

    return snapshot_paths(
        [
            "/candidate",
            "/python",
            "/site",
            "/campaign",
            "/manifests",
            "/project",
            "/combined",
            "/combined-record",
            "/combined-authority",
            "/etc/rkuarch/k2-host-selector.json",
        ]
    )


def configure():
    global BASE
    c, _, _ = b.check_payload(PROJECT, HELPERS, RECORD, sealed=not PRIVATE)
    b.old_bindings("/", c)
    manifest = b.read("/manifests/campaign-files.json")
    b.inventory("/campaign", {n: v["sha256"] for n, v in manifest.items()}, sealed=True)
    for name in ("entrypoint.py", "deployment.py"):
        b.need(
            b.digest((Path("/campaign") / name).read_bytes()) == manifest[name]["sha256"],
            "original helper before import",
        )
    sys.path.insert(0, "/campaign")
    import entrypoint
    import parallel_entrypoint as scheduler
    from parallel_core import Store

    BASE = entrypoint
    # Explicit reviewed adapter: no executable/result/admission/token replacement.
    BASE.common = common
    original_dump = BASE.dump

    def dump(path, value):
        if path.name == "replays.json":
            value = {**value, "runtime_binding": release()}
        original_dump(path, value)

    class BoundStore(Store):
        def json(self, name, value):
            if name in ("campaign.json", "resources.json", "worker-summary.json"):
                value = {**value, "runtime_binding": BINDING}
            return super().json(name, value)

    BASE.dump = dump
    scheduler.Store = BoundStore
    scheduler.verify_helpers = guards
    scheduler.verify_release = release
    scheduler.input_snapshot = snapshots
    return scheduler


def main(action):
    global BINDING, PRIVATE
    PRIVATE = action == "private-preflight"
    if PRIVATE:
        action = "preflight"
    b.need(action in ("preflight", "campaign", "replay"), "exact action; no quick campaign profile")
    started = time.monotonic()
    scheduler = configure()
    try:
        # Authority/provenance binding precedes any resolution/admission/native call.
        if action != "preflight":
            BINDING = release()
        else:
            b.need(
                not Path("/etc/rkuarch/k2-host-selector.json").exists() and not AUTHORITY.exists(),
                "authority-free preflight only",
            )

            def blocked(*args, **kwargs):
                raise RuntimeError("native/process execution prohibited in preflight")

            subprocess.Popen = blocked
            sys.addaudithook(
                lambda event, args: (
                    blocked()
                    if event
                    in ("subprocess.Popen", "os.exec", "os.posix_spawn", "os.system", "os.fork")
                    else None
                )
            )
        context = common()
        policy, manifest = guards()
        if action == "preflight":
            c, data, publication = b.check_payload(PROJECT, HELPERS, RECORD, sealed=not PRIVATE)
            BASE.dump(
                OUT / "preflight.json",
                {
                    "status": "private-composition-passed"
                    if PRIVATE
                    else "combined-runtime-import-preflight-passed",
                    "binding": b.identity(data),
                    "publication": publication,
                    "root": str(b.NEW),
                    "immutable_mounts_checked": True,
                    "origins": b.origins(sys.modules, PROJECT),
                    "private_test": PRIVATE,
                    "native_calls": 0,
                    "authority_resolved": False,
                },
            )
        elif action == "campaign":
            scheduler.campaign(BASE, context, policy, manifest, started, time.monotonic() - started)
        else:
            record = b.read(OUT / "campaign.json")
            b.need(record["runtime_binding"] == BINDING, "same-runtime saved campaign required")
            before = snapshots()
            BASE.replay(context)
            guards()
            release()
            scheduler.verify_snapshots(before, snapshots())
        BASE.dump(
            OUT / (action + "-operational.json"),
            {
                "runtime_binding": BINDING or b.identity((RECORD / "candidate.json").read_bytes()),
                "stage": action,
                "total_seconds": time.monotonic() - started,
                "parent_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "startup_processing_fields": (
                    "worker-summary.json for campaign; no mapped processing in preflight/replay"
                ),
            },
        )
    except BaseException as error:
        BASE.dump(
            OUT / (action + "-failure.json"),
            {"error": repr(error), "complete": False, "runtime_binding": BINDING},
        )
        raise


if __name__ == "__main__":
    b.need(len(sys.argv) == 2, "one explicit action")
    main(sys.argv[1])
