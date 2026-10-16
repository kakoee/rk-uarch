"""Replacement case scheduler. Original approved runtime and validators stay immutable."""

import json
import os
import resource
import sys
import time
from pathlib import Path

from parallel_core import (
    Store,
    digest,
    require,
    run_workers,
    snapshot_paths,
    verify_six_way,
    verify_snapshots,
)
from resource_limits import discover

OUTPUT = Path("/receipts")
STATE = None


def input_snapshot():
    return snapshot_paths(
        [
            "/candidate",
            "/python",
            "/site",
            "/campaign",
            "/manifests",
            "/parallel",
            "/parallel-authority",
            "/etc/rkuarch/k2-host-selector.json",
        ]
    )


def original():
    sys.path.insert(0, "/campaign")
    import entrypoint

    return entrypoint


def verify_helpers(base):
    manifest_bytes = Path("/parallel-authority/helper-manifest.json").read_bytes()
    for path in ["/parallel", "/parallel-authority"]:
        require(os.statvfs(path).f_flag & os.ST_RDONLY, "read-only parallel deployment")
    base.frozen_tree("/parallel", json.loads(manifest_bytes))
    policy = json.loads(Path("/parallel/parallel-policy.json").read_bytes())
    require(
        digest(Path("/manifests/runtime-release.json").read_bytes())
        == policy["original_runtime_release_hash"],
        "original release changed",
    )
    require(
        digest(Path("/manifests/campaign-files.json").read_bytes())
        == policy["original_helper_manifest_hash"],
        "original helper bytes changed",
    )
    require(
        digest(Path("/campaign/campaign-plan.json").read_bytes()) == policy["plan_hash"],
        "unchanged full 798-slot plan required",
    )
    return policy, digest(manifest_bytes)


def verify_release(policy, manifest_hash):
    preflight_bytes = Path("/parallel-authority/parallel-preflight.json").read_bytes()
    preflight = json.loads(preflight_bytes)
    release = json.loads(Path("/parallel-authority/runtime-release.json").read_bytes())
    require(
        preflight["status"] == "parallel-import-preflight-passed"
        and preflight["helper_manifest_hash"] == manifest_hash
        and preflight["native_calls"] == 0,
        "matching real parallel preflight required",
    )
    require(
        release["format"] == "uarch-k2-parallel-runtime/1"
        and release["status"] == "placed-after-coordinator-reconciliation"
        and release["helper_manifest_hash"] == manifest_hash
        and release["original_runtime_release_hash"] == policy["original_runtime_release_hash"]
        and release["plan_hash"] == policy["plan_hash"]
        and release["policy_hash"] == digest(Path("/parallel/parallel-policy.json").read_bytes())
        and release["preflight_byte_hash"] == digest(preflight_bytes),
        "parallel release join",
    )
    require(
        len(release["helper_publication_commit"]) == 40
        and len(release["placement_publication_commit"]) == 40
        and release["placement_record_byte_hash"].startswith("sha256:"),
        "real placement publication required",
    )
    # Commit/blob provenance is checked independently before human placement; these
    # root-owned declarations do not authenticate themselves or create engine authority.
    return release


def perform_case(case_id):
    base, context, hosts, cases, answers, store = STATE
    _, plan, _, _, runner, _, _, job_model, checker = context
    case = cases[case_id]
    saved = base.ROOT / case["file"]["path"]
    require(digest(saved.read_bytes()) == case["file"]["byte_hash"], "saved case changed")
    completed = []
    for mode in plan["modes"]:
        for repetition in plan["repetitions"]:
            slot = f"{mode}-{repetition}-{case_id}"
            captured = []
            original_exchange = runner._exchange

            def observe(
                fd,
                request,
                limits,
                original_exchange=original_exchange,
                captured=captured,
                slot=slot,
            ):
                response = original_exchange(fd, request, limits)
                captured.append((request, *response))
                out, err, status = response
                store.json(
                    "transport/" + slot + ".json",
                    {
                        "request": store.blob(request),
                        "stdout": store.blob(out),
                        "stderr": store.blob(err),
                        "status": status,
                    },
                )
                return response

            runner._exchange = observe
            try:
                try:
                    result, receipt = runner.run_fixed_delay(saved, host=hosts[mode])
                except runner.NativeRefusal as error:
                    require(
                        case["outcome"] == "TimeOverflow"
                        and error.envelope["code"] == "TimeOverflow",
                        "wrong semantic refusal",
                    )
                    receipt = {"semantic_refusal": error.envelope}
                else:
                    require(case["outcome"] == "success", "expected refusal succeeded")
                    # Preserve the current baseline: fresh request parse and all
                    # independent checks, no validation-cache or caller shortcut.
                    checker(
                        result, job_model.model_validate_json(saved.read_bytes()), answers[case_id]
                    )
                require(len(captured) == 1, "one fresh real native call per slot")
                request, out, err, status = captured[0]
                require(request == saved.read_bytes(), "canonical request drift")
                row = {
                    "mode": mode,
                    "repetition": repetition,
                    "case_id": case_id,
                    "request": store.blob(request),
                    "stdout": store.blob(out),
                    "stderr": store.blob(err),
                    "request_hash": digest(request),
                    "stdout_hash": digest(out),
                    "stderr_hash": digest(err),
                    "status": status,
                    "receipt": receipt,
                    "executable_hash": hosts[mode].executable.byte_hash,
                }
                store.json("calls/" + slot + ".json", row)
                completed.append(slot)
            finally:
                runner._exchange = original_exchange
    return {
        "case_id": case_id,
        "slots": completed,
        "worker_pid": os.getpid(),
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def assemble(base, plan, store, worker_results):
    from deployment import slots, verify_saved_campaign

    expected = slots(plan)
    cases = [c["case_id"] for c in plan["case_membership"]]
    require([r["case_id"] for r in worker_results] == cases, "exact ordered case completion")
    names = [f"{m}-{r}-{c['case_id']}" for m, r, c in expected]
    returned = [name for result in worker_results for name in result["slots"]]
    require(
        len(returned) == len(set(returned)) == len(names) and set(returned) == set(names),
        "missing/extra/duplicate worker slots",
    )
    for directory in ["calls", "transport"]:
        actual = [p.name for p in (store.root / directory).iterdir()]
        require(
            set(actual) == {name + ".json" for name in names} and len(actual) == len(names),
            "exact receipt directory membership",
        )
    rows = [json.loads((store.root / "calls" / (name + ".json")).read_bytes()) for name in names]
    record = {"subject": plan["subject"], "calls": rows, "mapped_calls": 798, "complete": True}
    verify_six_way(rows, cases)
    verify_saved_campaign(store.root, plan, record)
    for name, row in zip(names, rows, strict=True):
        transport = json.loads((store.root / "transport" / (name + ".json")).read_bytes())
        require(
            transport == {k: row[k] for k in ["request", "stdout", "stderr", "status"]},
            "transport/checked receipt mismatch",
        )
    store.check_budget()
    return record


def campaign(base, context, policy, manifest_hash, entry_started, setup_seconds):
    global STATE
    _, plan, _, host, _, _, _, _, _ = context
    verify_release(policy, manifest_hash)
    snapshot_started = time.monotonic()
    before_inputs = input_snapshot()
    snapshot_seconds = time.monotonic() - snapshot_started
    # This is the public resolver, including its token constructor and every input
    # check. Exactly once per mode in the thread-free parent, before any worker fork.
    before = time.monotonic()
    hosts = base.authority(plan, host)
    resolver_seconds = time.monotonic() - before
    cases = {c["case_id"]: c for c in plan["case_membership"]}
    answers = base.read_json(
        base.ROOT / "docs/reviews/U4-A-K2-construction-v1/corpus/expectations.json"
    )
    resources = discover(policy, len(cases))
    store = Store(OUTPUT, plan["receipt_budget_bytes"])
    require(
        not any((OUTPUT / name).exists() for name in ["calls", "transport", "campaign.json"]),
        "fresh replacement campaign output required",
    )
    store.json(
        "resources.json",
        {
            **resources,
            "resolver_seconds": resolver_seconds,
            "scheduling": "one worker owns all six fresh calls of each case",
        },
    )
    store.json("input-snapshot-before.json", before_inputs)
    STATE = base, context, hosts, cases, answers, store
    processing_started = time.monotonic()
    results = run_workers(
        list(cases),
        perform_case,
        workers=resources["workers"],
        task_timeout=policy["case_timeout_seconds"],
        total_timeout=plan["campaign_timeout_seconds"],
        executable_paths=tuple(str(base.ROOT / h.executable.path) for h in hosts.values()),
        progress=lambda case, result: store.json("progress/" + case + ".json", result),
    )
    processing_seconds = time.monotonic() - processing_started
    final_checks_started = time.monotonic()
    record = assemble(base, plan, store, results)
    base.common()  # All original sealed inputs rechecked after workers exit.
    verify_helpers(base)
    verify_release(policy, manifest_hash)
    after_inputs = input_snapshot()
    store.json("input-snapshot-after.json", after_inputs)
    verify_snapshots(before_inputs, after_inputs)
    store.json(
        "worker-summary.json",
        {
            "workers": resources["workers"],
            "cases": results,
            "timing_seconds": {
                "runtime_preflight": setup_seconds,
                "initial_input_snapshot": snapshot_seconds,
                "genuine_authority_resolution": resolver_seconds,
                "case_processing": processing_seconds,
                "final_checks": time.monotonic() - final_checks_started,
                "entrypoint_total_before_final_receipt": time.monotonic() - entry_started,
            },
        },
    )
    store.json("campaign.json", record)  # Last, only after complete validation and postchecks.
    STATE = None


def main():
    require(
        len(sys.argv) == 2 and sys.argv[1] in ("preflight", "campaign", "replay"), "explicit action"
    )
    entry_started = time.monotonic()
    base = original()
    try:
        policy, manifest_hash = verify_helpers(base)
        context = base.common()
        if sys.argv[1] == "preflight":
            require(
                not Path("/etc/rkuarch/k2-host-selector.json").exists(), "no selector in preflight"
            )
            base.dump(
                OUTPUT / "parallel-preflight.json",
                {
                    "status": "parallel-import-preflight-passed",
                    "helper_manifest_hash": manifest_hash,
                    "original_runtime_release_hash": policy["original_runtime_release_hash"],
                    "native_calls": 0,
                    "authority_resolved": False,
                },
            )
        elif sys.argv[1] == "campaign":
            campaign(
                base,
                context,
                policy,
                manifest_hash,
                entry_started,
                time.monotonic() - entry_started,
            )
        else:
            verify_release(policy, manifest_hash)
            before_inputs = input_snapshot()
            base.replay(context)  # Unchanged real saved-output corruption/restoration obligations.
            verify_helpers(base)
            after_inputs = input_snapshot()
            verify_snapshots(before_inputs, after_inputs)
            base.dump(
                OUTPUT / "parallel-replay-inputs.json",
                {
                    "before": digest(json.dumps(before_inputs, sort_keys=True).encode()),
                    "after": digest(json.dumps(after_inputs, sort_keys=True).encode()),
                    "preserved": True,
                },
            )
    except BaseException as error:
        base.dump(OUTPUT / "parallel-failure.json", {"error": repr(error), "complete": False})
        raise


if __name__ == "__main__":
    main()
