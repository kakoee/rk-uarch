"""Bounded host-only scheduler guards. Toy tasks are not native-success fixtures."""

import copy
import json
import multiprocessing
import os
import threading
import time
from pathlib import Path

import parallel_core as core
import pytest
from parallel_core import Store, digest, run_workers, safe_fork, verify_six_way
from resource_limits import select_resources


def limits(**overrides):
    values = dict(
        affinity=set(range(16)),
        quotas=[],
        memory_available=16 * 1024,
        memory_limits=[],
        reserve=1024,
        per_worker=1024,
        tasks=133,
    )
    return select_resources(**(values | overrides))


def test_cpu_quota_and_memory_are_both_limits():
    assert limits()["workers"] == 15
    assert limits(quotas=[(250, 100), (110, 100)])["workers"] == 1
    assert limits(affinity={1, 3, 6})["workers"] == 3
    assert limits(memory_limits=[(8000, 5000)])["workers"] == 1
    assert limits(tasks=2)["workers"] == 2
    with pytest.raises(ValueError, match="effective CPU"):
        limits(quotas=[(50, 100)])
    with pytest.raises(ValueError, match="memory"):
        limits(memory_available=1500)


def toy_group(case):
    # Deliberately no EngineResult, native call or host capability. Each group
    # exercises six distinct slot writes with a content-addressed shared byte blob.
    store = Store(TOY_ROOT, 1024 * 1024)
    slots = []
    for mode in ("debug", "release"):
        for repetition in range(3):
            slot = f"{mode}-{repetition}-{case}"
            store.json(
                "toy/" + slot + ".json", {"slot": slot, "blob": store.blob(b"toy transport")}
            )
            slots.append(slot)
            time.sleep(0.001 if case == "first" else 0.002)
    return {"case": case, "slots": slots, "pid": os.getpid()}


TOY_ROOT = None


def test_case_group_scheduling_atomic_shared_blob_and_order(tmp_path):
    global TOY_ROOT
    TOY_ROOT = tmp_path
    tasks = ["first", "second", "third"]
    results = run_workers(tasks, toy_group, workers=3, task_timeout=2, total_timeout=5)
    assert [r["case"] for r in results] == tasks
    assert len({r["pid"] for r in results}) >= 2
    assert len(list((tmp_path / "toy").glob("*.json"))) == 18
    assert len(list((tmp_path / "blobs").iterdir())) == 1
    assert all(len(r["slots"]) == 6 for r in results)
    Store(tmp_path, 1024 * 1024).check_budget()
    assert not multiprocessing.active_children()


def test_atomic_collision_duplicate_and_budget(tmp_path):
    store = Store(tmp_path, 5000)
    name = store.blob(b"genuine bytes")
    assert store.blob(b"genuine bytes") == name
    with pytest.raises(ValueError, match="collision"):
        store.publish(name, b"other bytes", shared=True)
    store.json("calls/one.json", {"slot": 1})
    with pytest.raises(ValueError, match="duplicate"):
        store.json("calls/one.json", {"slot": 1})
    with pytest.raises(ValueError, match="budget"):
        store.publish("too-big", b"x" * 5000)
    assert not (tmp_path / "too-big").exists()


def test_receipt_symlink_and_partial_publication_refuse(tmp_path):
    store = Store(tmp_path, 10000)
    (tmp_path / "bad").symlink_to(tmp_path / "outside")
    with pytest.raises(ValueError, match="parent"):
        store.publish("bad/one", b"data")
    (tmp_path / "bad").unlink()
    (tmp_path / ".pending-dead-worker").write_bytes(b"partial")
    with pytest.raises(ValueError, match="unfinished"):
        store.check_budget()


def broken(task):
    raise ValueError("later repetition failure")


def abrupt(task):
    os._exit(17)


def hangs(task):
    time.sleep(10)


@pytest.mark.parametrize(
    "function,reason",
    [
        (broken, "worker failure"),
        (abrupt, "worker exited"),
        (hangs, "worker task/startup deadline"),
    ],
)
def test_failure_death_and_hang_refuse_and_reap(function, reason):
    with pytest.raises((ValueError, EOFError), match=reason if function != abrupt else None):
        run_workers(["one"], function, workers=1, task_timeout=0.15, total_timeout=1)
    assert not multiprocessing.active_children()


def test_late_failure_preserves_earlier_slot_receipt(tmp_path):
    def later(task):
        store = Store(tmp_path, 10000)
        store.json("calls/first.json", {"toy": "first checked slot"})
        raise ValueError("final repetition failure")

    with pytest.raises(ValueError, match="worker failure"):
        run_workers(["case"], later, workers=1, task_timeout=1, total_timeout=2)
    assert json.loads((tmp_path / "calls/first.json").read_bytes())["toy"] == "first checked slot"
    assert not (tmp_path / "campaign.json").exists()


def malicious(connection, function, inherited):
    for fd in inherited:
        os.close(fd)
    core._send(connection, {"kind": "ready"})
    core._receive(connection)
    core._send(connection, {"kind": "done", "task": "foreign", "result": {}})
    time.sleep(1)


def test_foreign_worker_completion_refuses(monkeypatch):
    monkeypatch.setattr(core, "_worker", malicious)
    with pytest.raises(ValueError, match="duplicate/foreign"):
        run_workers(["one"], broken, workers=1, task_timeout=1, total_timeout=2)
    assert not multiprocessing.active_children()


def test_safe_fork_rejects_active_thread_and_open_executable(tmp_path):
    event = threading.Event()
    thread = threading.Thread(target=event.wait)
    thread.start()
    try:
        with pytest.raises(ValueError, match="threads"):
            safe_fork()
    finally:
        event.set()
        thread.join()
    file = tmp_path / "test-executable-inode"
    file.write_bytes(b"not an executable")
    with file.open("rb"):
        with pytest.raises(ValueError, match="descriptor"):
            safe_fork((str(file),))


def test_empty_duplicate_selection_refuses_before_fork():
    for tasks in [[], ["one", "one"]]:
        with pytest.raises(ValueError, match="membership"):
            run_workers(tasks, broken, workers=1, task_timeout=1, total_timeout=2)


def saved_rows():
    # Only genuine prior output hashes. Relabeling metadata here tests comparison
    # bookkeeping only; it is explicitly not evidence of six native invocations.
    row = json.loads(Path("/tmp/u4-k2-approved-campaign/calls/debug-0-K01.json").read_bytes())
    for field in ("request", "stdout", "stderr"):
        assert (
            digest((Path("/tmp/u4-k2-approved-campaign") / row[field]).read_bytes())
            == row[field + "_hash"]
        )
    return [
        copy.deepcopy(row) | {"mode": mode, "repetition": repetition}
        for mode in ("debug", "release")
        for repetition in range(3)
    ]


def test_actual_saved_hash_comparison_positive_and_late_drift():
    rows = saved_rows()
    verify_six_way(rows, ["K01"])
    rows[-1]["stdout_hash"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="drift"):
        verify_six_way(rows, ["K01"])


@pytest.mark.parametrize("fault", ["missing", "extra", "duplicate", "wrong-mode"])
def test_saved_multiplicity_controls(fault):
    rows = saved_rows()
    if fault == "missing":
        rows.pop()
    elif fault == "extra":
        rows.append(rows[0])
    elif fault == "duplicate":
        rows[-1] = rows[0]
    else:
        rows[-1]["mode"] = "foreign"
    with pytest.raises(ValueError, match="membership"):
        verify_six_way(rows, ["K01"])


def test_new_command_reuses_original_and_never_writes_stopped_evidence(
    tmp_path, monkeypatch, capsys
):
    import launch

    for action in ["preflight", "campaign", "replay"]:
        argv = launch.command(action, tmp_path / "new-output")
        assert argv[argv.index("--network") + 1] == "none"
        assert argv[argv.index("--user") + 1] == "1000:1000"
        assert argv[argv.index("--pull") + 1] == "never"
        assert "/parallel/parallel_entrypoint.py" in argv[-1]
        assert any("candidate-04-first-use-v1/candidate" in x for x in argv)
        assert any("candidate-04-parallel-v1/helpers" in x for x in argv)
        assert any("k2-host-selector" in x for x in argv) == (action != "preflight")
    with pytest.raises(ValueError, match="stopped evidence"):
        launch.command("campaign", "/tmp/u4-k2-approved-campaign")

    def forbidden(*args, **kwargs):
        raise AssertionError("default must not launch")

    monkeypatch.setattr(launch.subprocess, "Popen", forbidden)
    launch.launch("campaign", tmp_path / "default-only", False)
    assert json.loads(capsys.readouterr().out)[-2] == "-c"
    assert not (tmp_path / "default-only").exists()


def test_human_script_is_confined_literal_and_syntax_only(tmp_path):
    import subprocess

    from prepare_placement import NEW_ROOT, script

    data = script({NEW_ROOT / "helpers/one.py": b'print("never executed")\n'}, True)
    file = tmp_path / "script.sh"
    file.write_bytes(data)
    assert subprocess.run(["/bin/bash", "-n", str(file)], check=False).returncode == 0
    assert b"sudo" not in data and b"chmod 0444" in data
    assert b"test ! -e" in data and b"set -euC" in data
    assert not NEW_ROOT.exists()
    with pytest.raises(ValueError, match="fixed"):
        script({NEW_ROOT / "../foreign": b"bad"}, True)
    with pytest.raises(ValueError, match="fixed"):
        script({Path("/etc/rkuarch/forbidden"): b"bad"}, True)


def test_full_input_snapshot_detects_same_size_tamper(tmp_path):
    from parallel_core import snapshot_paths, verify_snapshots

    file = tmp_path / "bound"
    file.write_bytes(b"one")
    before = snapshot_paths([tmp_path])
    verify_snapshots(before, snapshot_paths([tmp_path]))
    file.write_bytes(b"two")
    with pytest.raises(ValueError, match="sealed deployment"):
        verify_snapshots(before, snapshot_paths([tmp_path]))
    file.write_bytes(b"one")
    verify_snapshots(before, snapshot_paths([tmp_path]))


def test_developer_profiles_never_reduce_full_campaign():
    from developer_checks import SMOKE, selection

    ids = SMOKE + [f"fixture-{i}" for i in range(125)]
    plan = {"case_membership": [{"case_id": name} for name in ids]}
    fast = selection(plan, "fast")
    assert len(fast) == 8 and all(m == "debug" and r == 0 for m, r, c in fast)
    assert [c["case_id"] for m, r, c in fast] == SMOKE
    broad = selection(plan, "regression")
    assert len(broad) == 266
    assert len({(m, r, c["case_id"]) for m, r, c in broad}) == 266
    with pytest.raises(ValueError, match="profile"):
        selection(plan, "complete")
    with pytest.raises(ValueError, match="corpus"):
        selection({"case_membership": []}, "fast")


def test_developer_launcher_is_authority_free_and_default_nonexecuting(
    tmp_path, monkeypatch, capsys
):
    import developer_launch

    saved = Path("/tmp/u4-k2-approved-campaign")
    argv = developer_launch.command("fast", saved, tmp_path / "out", tmp_path / "helpers")
    assert not any("k2-host-selector" in item for item in argv)
    assert argv[argv.index("--network") + 1] == "none"
    assert argv[argv.index("--user") + 1] == "1000:1000"
    assert "developer_checks.py" in argv[-1]

    def forbidden(*args, **kwargs):
        raise AssertionError("default cannot launch")

    monkeypatch.setattr(developer_launch.subprocess, "Popen", forbidden)
    developer_launch.launch("fast", saved, tmp_path / "out", False)
    assert json.loads(capsys.readouterr().out)[-2] == "-c"
    assert not (tmp_path / "out").exists()


def test_combined_session_cleanup_on_failure_uses_same_real_api_shape(tmp_path):
    # Toy callback sentinels only; no AcceptedHostBinding, token or native result.
    import contextlib
    import importlib.util
    import subprocess
    from types import SimpleNamespace

    here = Path(__file__).resolve().parent
    (tmp_path / "parallel_entrypoint.py").write_bytes(
        (here / "parallel_entrypoint.py").read_bytes()
    )
    subprocess.run(
        ["git", "apply", "--check", str(here / "combined-reuse-integration.patch")],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "apply", str(here / "combined-reuse-integration.patch")], cwd=tmp_path, check=True
    )
    spec = importlib.util.spec_from_file_location(
        "private_combined_helper", tmp_path / "parallel_entrypoint.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    events = []

    @contextlib.contextmanager
    def session():
        events.append("enter")
        try:
            yield lambda *, mode: "toy-" + mode
        finally:
            assert module.STATE is None
            events.append("exit-after-clear")

    def authority(plan, facade):
        return {mode: facade.resolve_host(mode=mode) for mode in plan["modes"]}

    with pytest.raises(RuntimeError, match="worker failed"):
        with module.resolve_campaign_hosts(
            SimpleNamespace(authority=authority),
            {"modes": ["debug", "release"]},
            SimpleNamespace(resolution_session=session),
        ) as values:
            assert values == {"debug": "toy-debug", "release": "toy-release"}
            module.STATE = object()
            raise RuntimeError("worker failed")
    assert events == ["enter", "exit-after-clear"] and module.STATE is None
