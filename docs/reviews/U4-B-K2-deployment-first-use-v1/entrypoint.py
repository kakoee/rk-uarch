"""Future guarded container harness. NEVER execute during proposal preparation.

No wrapper is used as the native executable. The production resolver supplies its
verified ELF descriptor; the production runner owns admission, IO and result checks.
"""

import copy
import hashlib
import importlib.abc
import importlib.metadata
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/candidate")
PACKAGE = Path("/campaign")
OUTPUT = Path("/receipts")


def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


class NoProducers(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname == "rk" or fullname.startswith(
            (
                "rk.",
                "rkuarch.mapping",
                "rkuarch.workload.prepare",
                "rkuarch.workload.producer",
                "rkuarch.engines.analytic",
                "rkuarch.table",
                "scripts.vendor_rk",
                "scripts.u2_inputs",
                "tkinter",
                "_tkinter",
            )
        ):
            raise RuntimeError("forbidden producer/oracle/optional GUI import: " + fullname)


def frozen_tree(root, inventory):
    root = Path(root)
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() or p.is_symlink()}
    need(actual == set(inventory), "runtime file membership drift")
    for name, binding in inventory.items():
        p = root / name
        need(".." not in Path(name).parts and not Path(name).is_absolute(), "runtime path")
        s = p.lstat()
        need(s.st_uid == 0, "runtime ownership")
        if "symlink" in binding:
            need(p.is_symlink() and str(p.readlink()) == binding["symlink"], "symlink identity")
            need(p.resolve().is_relative_to(root), "runtime symlink escape")
        else:
            need(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "runtime regular inode")
            need(not s.st_mode & 0o222, "runtime inode write bit")
            need(sha(p.read_bytes()) == binding["sha256"], "runtime byte drift")


def common():
    need(os.getuid() == os.geteuid() == 1000, "UID1000 required")
    need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, "-I -S -B required")
    need(sys.version_info[:3] == (3, 12, 14), "exact Python required")
    need(Path(sys.executable) == Path("/python/bin/python3.12"), "mounted interpreter required")
    need(Path(sys.base_prefix) == Path("/python"), "relocated Python prefix")
    need(
        "LD_LIBRARY_PATH" not in os.environ and "PYTHONPATH" not in os.environ, "clean environment"
    )
    for root in ["/", "/python", "/site", "/candidate", "/campaign", "/manifests"]:
        need(os.statvfs(root).f_flag & os.ST_RDONLY, "read-only mount required: " + root)
    frozen_tree(PACKAGE, read_json(Path("/manifests/campaign-files.json")))
    runtime = read_json(PACKAGE / "runtime.json")
    for name, root in [("python-files.json", "/python"), ("site-files.json", "/site")]:
        data = (Path("/manifests") / name).read_bytes()
        need(sha(data) == runtime["inventories"][name], "runtime manifest identity")
        frozen_tree(root, json.loads(data))
    for path, expected in runtime["image_libraries"].items():
        need(sha(Path(path).read_bytes()) == expected, "image library/search-state mismatch")
    sys.path[:0] = [
        "/site",
        "/candidate/src",
        "/candidate/contract",
        "/campaign",
        "/candidate/docs/reviews/U4-B-K2-construction-audit-v1",
    ]
    sys.meta_path.insert(0, NoProducers())
    for name, expected in runtime["package_versions"].items():
        need(importlib.metadata.version(name) == expected, "package version drift: " + name)
    from deployment import slots, verify_bytes
    from first_use_checks import check_real_result
    from uarch_contract.hashing import canonical_json, content_hash
    from uarch_contract.mapped import MappedEngineJob

    from rkuarch.engines.native import host, runner

    layout = read_json(PACKAGE / "candidate-layout.json")
    verify_bytes(ROOT, layout["files"], sealed=True)
    plan = read_json(PACKAGE / "campaign-plan.json")
    work = slots(plan)
    for name, module in tuple(sys.modules.items()):
        f = getattr(module, "__file__", None)
        if f and name.startswith(("rkuarch", "uarch_contract")):
            need(Path(f).is_relative_to(ROOT), "non-private project origin")
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


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def dump(path, value):
    put(path, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode())


def blob(data):
    path = OUTPUT / "blobs" / sha(data).split(":")[1]
    if path.exists():
        need(path.read_bytes() == data, "saved blob changed")
    else:
        put(path, data)
    return str(path.relative_to(OUTPUT))


def authority(plan, host):
    preflight = read_json(Path("/manifests/preflight.json"))
    need(preflight["status"] == "runtime-import-preflight-passed", "actual preflight required")
    need(
        preflight["runtime_hash"] == sha((PACKAGE / "runtime.json").read_bytes()), "stale preflight"
    )
    need(
        preflight["campaign_files_hash"]
        == sha(Path("/manifests/campaign-files.json").read_bytes()),
        "preflight/helper binding drift",
    )
    release = read_json(Path("/manifests/runtime-release.json"))
    need(release["status"] == "human-authorized-first-use", "human runtime release absent")
    need(release["subject"] == plan["subject"], "runtime release subject")
    need(
        release["preflight_byte_hash"] == sha(Path("/manifests/preflight.json").read_bytes()),
        "actual preflight receipt binding",
    )
    need(release["runtime_hash"] == sha((PACKAGE / "runtime.json").read_bytes()), "runtime release")
    need(
        release["campaign_files_hash"] == sha(Path("/manifests/campaign-files.json").read_bytes()),
        "exact released helper bytes",
    )
    need(release["plan_hash"] == sha((PACKAGE / "campaign-plan.json").read_bytes()), "plan release")
    hosts = {m: host.resolve_host(mode=m) for m in plan["modes"]}
    for m, bound in hosts.items():
        need(bound.root == ROOT, "exact container repository root")
        need(bound.selector.acceptance_commit == release["acceptance_commit"], "publication join")
        need(bound.selector.record_byte_hash == release["record_byte_hash"], "record release join")
        expected = plan["subject"]["executable_byte_hashes"][plan["modes"].index(m)]
        need(bound.executable.byte_hash == expected, "exact actual executable")
    return hosts


def preflight(context):
    need(not Path("/etc/rkuarch/k2-host-selector.json").exists(), "preflight must lack authority")
    origins = {n: m.__file__ for n, m in sys.modules.copy().items() if getattr(m, "__file__", None)}
    dump(
        OUTPUT / "preflight.json",
        {
            "status": "runtime-import-preflight-passed",
            "runtime_hash": sha((PACKAGE / "runtime.json").read_bytes()),
            "campaign_files_hash": sha(Path("/manifests/campaign-files.json").read_bytes()),
            "origins": origins,
            "mapped_jobs_executed": 0,
            "resolver_authority_installed": False,
        },
    )


def campaign(context):
    _, plan, work, host, runner, canonical, _, job_model, checker = context
    hosts = authority(plan, host)
    need(not (OUTPUT / "campaign.json").exists(), "fresh campaign required")
    answers = read_json(ROOT / "docs/reviews/U4-A-K2-construction-v1/corpus/expectations.json")
    baseline, rows = {}, []
    start = time.monotonic()
    original = runner._exchange
    captured = []
    current_slot = None

    def observe(fd, request, limits):
        response = original(fd, request, limits)
        captured.append((request, *response))
        out, err, status = response
        dump(
            OUTPUT / "transport" / (current_slot + ".json"),
            {
                "request": blob(request),
                "stdout": blob(out),
                "stderr": blob(err),
                "status": status,
            },
        )
        return response

    runner._exchange = observe
    try:
        for mode, repetition, case in work:
            current_slot = f"{mode}-{repetition}-{case['case_id']}"
            need(time.monotonic() - start < plan["campaign_timeout_seconds"], "campaign time cap")
            need(
                sum(p.stat().st_size for p in OUTPUT.rglob("*") if p.is_file())
                < plan["receipt_budget_bytes"],
                "campaign receipt cap",
            )
            saved = ROOT / case["file"]["path"]
            need(sha(saved.read_bytes()) == case["file"]["byte_hash"], "saved request drift")
            captured.clear()
            try:
                result, receipt = runner.run_fixed_delay(saved, host=hosts[mode])
            except runner.NativeRefusal as error:
                need(
                    case["outcome"] == "TimeOverflow" and error.envelope["code"] == "TimeOverflow",
                    "wrong semantic refusal",
                )
                receipt = {"semantic_refusal": error.envelope}
            else:
                need(case["outcome"] == "success", "expected refusal succeeded")
                checker(
                    result,
                    job_model.model_validate_json(saved.read_bytes()),
                    answers[case["case_id"]],
                )
            need(len(captured) == 1, "exactly one actual subprocess per slot")
            request, stdout, stderr, status = captured[0]
            need(request == saved.read_bytes(), "canonical saved request changed")
            observed = (sha(stdout), sha(stderr), status)
            if case["case_id"] in baseline:
                need(observed == baseline[case["case_id"]], "mode/repetition replay drift")
            else:
                baseline[case["case_id"]] = observed
            row = {
                "mode": mode,
                "repetition": repetition,
                "case_id": case["case_id"],
                "request": blob(request),
                "stdout": blob(stdout),
                "stderr": blob(stderr),
                "request_hash": sha(request),
                "stdout_hash": sha(stdout),
                "stderr_hash": sha(stderr),
                "status": status,
                "receipt": receipt,
                "executable_hash": hosts[mode].executable.byte_hash,
            }
            dump(OUTPUT / "calls" / f"{mode}-{repetition}-{case['case_id']}.json", row)
            rows.append(row)
            need(
                sum(p.stat().st_size for p in OUTPUT.rglob("*") if p.is_file())
                < plan["receipt_budget_bytes"],
                "campaign receipt cap; incomplete",
            )
    finally:
        runner._exchange = original
    common()  # Recheck all input/runtime bytes after the complete campaign.
    need(
        len(rows) == 798 and sum(r["status"] == 2 for r in rows) == 18, "complete campaign required"
    )
    dump(
        OUTPUT / "campaign.json",
        {"subject": plan["subject"], "calls": rows, "mapped_calls": 798, "complete": True},
    )


def replay(context):
    _, plan, _, host, runner, canonical, content_hash, job_model, checker = context
    hosts = authority(plan, host)
    from deployment import verify_saved_campaign

    campaign_record = read_json(OUTPUT / "campaign.json")
    need(
        campaign_record["complete"] and campaign_record["subject"] == plan["subject"],
        "complete real campaign required",
    )

    verify_saved_campaign(OUTPUT, plan, campaign_record)

    # Never create a native-success fixture: only actual saved qualifying outputs enter here.
    def forbidden(*args, **kwargs):
        raise RuntimeError("replay process/producer execution prohibited")

    subprocess.Popen = forbidden
    original_cwd = Path.cwd()
    rows = []
    for case in plan["saved_replays"]:
        row = next(
            r
            for r in campaign_record["calls"]
            if r["case_id"] == case and r["mode"] == "debug" and r["repetition"] == 0
        )
        relocation = Path("/tmp") / ("replay-" + case)
        relocation.mkdir()
        streams = {}
        for field in ["request", "stdout", "stderr"]:
            source = OUTPUT / row[field]
            need(sha(source.read_bytes()) == row[field + "_hash"], "saved replay drift")
            shutil.copyfile(source, relocation / field)
            streams[field] = (relocation / field).read_bytes()
        os.chdir(relocation)

        def parse(out, err=b"", status=0, request=streams["request"]):
            return runner.parse_response(
                out, err, status, request_bytes=request, host=hosts["debug"]
            )

        result = parse(streams["stdout"])
        answers = read_json(ROOT / "docs/reviews/U4-A-K2-construction-v1/corpus/expectations.json")
        checker(result, job_model.model_validate_json(streams["request"]), answers[case])
        failures = []
        for label, out, err, status in [
            ("missing", b"", b"", 0),
            ("duplicated", streams["stdout"] * 2, b"", 0),
            ("extra-LF", streams["stdout"] + b"\n", b"", 0),
            ("nonzero", streams["stdout"], b"", 1),
            ("foreign-status", streams["stdout"], b"", 3),
        ]:
            try:
                parse(out, err, status)
            except (runner.ProtocolViolation, runner.OperationalFailure):
                failures.append(label)
            else:
                raise RuntimeError("replay fault accepted: " + label)
        raw = json.loads(streams["stdout"])
        for label in [
            "foreign-job",
            "stale-engine",
            "incomplete",
            "busy-drift",
            "event-order",
            "queue-domain",
            "phase",
            "causal-link",
            "clock-law",
        ]:
            bad = copy.deepcopy(raw)
            if label == "foreign-job":
                bad["job_hash"] = "sha256:" + "0" * 64
            elif label == "stale-engine":
                bad["engine"]["implementation_hash"] = "sha256:" + "0" * 64
            elif label == "incomplete":
                bad["completed_jobs"] = []
            elif label == "busy-drift":
                bad["busy_time_ps"][0]["busy_time_ps"] += 1
            elif label == "event-order":
                bad["observations"]["events"]["records"].reverse()
            elif label == "phase":
                bad["observations"]["events"]["records"][0]["phase"] = 3
            elif label == "causal-link":
                if case != "S08-zero-bridge":
                    continue
                target = next(
                    x
                    for x in bad["observations"]["jobs"]["records"]
                    if x["blocking_predecessor_ids"]
                )
                target["blocking_predecessor_ids"] = []
            elif label == "clock-law":
                if case != "K06-02":
                    continue
                bad["observations"]["clocks"]["records"][0]["completion_ps"] += 1
            else:
                bad["observations"]["queue_membership"]["records"][0]["clock_domain"] = "core"
            bad["result_hash"] = content_hash(bad, exclude=("result_hash",))
            try:
                parse(canonical(bad).encode())
            except runner.ProtocolViolation:
                failures.append(label)
            else:
                raise RuntimeError("rehashed real-result mutation accepted: " + label)
        need(
            canonical(parse(streams["stdout"])).encode() == streams["stdout"],
            "restored replay changed",
        )
        for field in streams:
            need((relocation / field).read_bytes() == streams[field], "replay original mutated")
        rows.append({"case": case, "controls_refused": failures, "restored_pass": True})
    os.chdir(original_cwd)
    common()  # Recheck immutable inputs after replay/fault/restoration.
    dump(OUTPUT / "replays.json", {"saved_real_replays": rows, "new_native_calls": 0})


def main():
    need(
        len(sys.argv) == 2 and sys.argv[1] in ("preflight", "campaign", "replay"), "explicit stage"
    )
    try:
        context = common()
        {"preflight": preflight, "campaign": campaign, "replay": replay}[sys.argv[1]](context)
    except BaseException as error:
        dump(
            OUTPUT / "failure.json", {"stage": sys.argv[1], "error": repr(error), "complete": False}
        )
        raise


if __name__ == "__main__":
    main()
