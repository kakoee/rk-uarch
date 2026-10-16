"""Host-only proposal guards; no authority, interpreter payload or native launch."""

import copy
import json
from pathlib import Path

import pytest
from deployment import IMAGE, digest, docker_argv, slots, verify_bytes

HERE = Path(__file__).resolve().parent


def test_complete_finite_plan():
    plan = json.loads((HERE / "campaign-plan.json").read_text())
    work = slots(plan)
    assert len(work) == len({(m, r, c["case_id"]) for m, r, c in work}) == 798
    assert sum(c["outcome"] == "TimeOverflow" for _, _, c in work) == 18


@pytest.mark.parametrize("fault", ["empty", "missing", "extra", "duplicate", "order", "source"])
def test_bad_selections_refuse(fault):
    plan = copy.deepcopy(json.loads((HERE / "campaign-plan.json").read_text()))
    rows = plan["case_membership"]
    if fault == "empty":
        rows.clear()
    elif fault == "missing":
        rows.pop()
    elif fault == "extra":
        rows.append(copy.deepcopy(rows[-1]))
    elif fault == "duplicate":
        rows[1] = copy.deepcopy(rows[0])
    elif fault == "order":
        rows.reverse()
    else:
        plan["source"] = "0" * 40
    with pytest.raises(ValueError):
        slots(plan)


@pytest.mark.parametrize("action", ["preflight", "campaign", "replay"])
def test_exact_unprivileged_image_command(action):
    argv = docker_argv(action, "/tmp/approved-campaign-output", action != "preflight")
    for k, v in [
        ("--pull", "never"),
        ("--network", "none"),
        ("--user", "1000:1000"),
        ("--cap-drop", "ALL"),
        ("--security-opt", "no-new-privileges"),
    ]:
        assert argv[argv.index(k) + 1] == v
    assert IMAGE in argv and "--read-only" in argv
    assert not any("LD_LIBRARY_PATH" in a or "privileged" in a for a in argv)
    assert argv[-6:] == [
        "/python/bin/python3.12",
        "-I",
        "-S",
        "-B",
        "/campaign/entrypoint.py",
        action,
    ]
    assert any("k2-host-selector" in a for a in argv) == (action != "preflight")
    mounts = [argv[i + 1] for i, a in enumerate(argv) if a == "--mount"]
    assert all("readonly" in a for a in mounts if "dst=/receipts" not in a)
    assert not any("docker.sock" in a for a in mounts)


def test_changed_missing_and_symlink_inputs_refuse(tmp_path):
    p = tmp_path / "one"
    p.write_bytes(b"frozen")
    files = {"one": {"byte_hash": digest(b"frozen"), "mode": "0444"}}
    verify_bytes(tmp_path, files)
    p.write_bytes(b"changed")
    with pytest.raises(ValueError, match="digest"):
        verify_bytes(tmp_path, files)
    p.unlink()
    with pytest.raises(FileNotFoundError):
        verify_bytes(tmp_path, files)
    (tmp_path / "other").write_bytes(b"frozen")
    p.symlink_to("other")
    with pytest.raises(ValueError, match="regular"):
        verify_bytes(tmp_path, files)


def test_actual_candidate_file_bytes_and_membership():
    layout = json.loads((HERE / "candidate-layout.json").read_text())
    assert layout["authority_installed"] is False and len(layout["files"]) == 372
    assert all(not p.startswith("authority/") for p in layout["files"])
    for binding in layout["files"].values():
        assert digest(Path(binding["source"]).read_bytes()) == binding["byte_hash"]
    plan = json.loads((HERE / "campaign-plan.json").read_text())
    for row in plan["case_membership"]:
        binding = layout["files"][row["file"]["path"]]
        assert binding["byte_hash"] == row["file"]["byte_hash"]
        job = json.loads(Path(binding["source"]).read_bytes())
        assert job["job_hash"] == row["job_hash"]
        assert job["admission"]["case_id"] == row["case_id"]


def test_foreign_case_even_with_133_rows_refuses():
    plan = json.loads((HERE / "campaign-plan.json").read_text())
    plan["case_membership"][0]["case_id"] = "foreign"
    with pytest.raises(ValueError, match="frozen"):
        slots(plan)


def test_default_launcher_is_nonexecuting(tmp_path, monkeypatch, capsys):
    import launch

    def forbidden(*args, **kwargs):
        raise AssertionError("no child launch allowed")

    monkeypatch.setattr(launch.subprocess, "Popen", forbidden)
    launch.launch("preflight", tmp_path / "new-output", False)
    assert json.loads(capsys.readouterr().out)[-1] == "preflight"
    assert not (tmp_path / "new-output").exists()


def test_copy_guard_refuses_runtime_escape_and_drift(tmp_path):
    from materialize import runtime_copy

    source = tmp_path / "source"
    source.mkdir()
    (source / "one").write_bytes(b"frozen tool bytes")
    inv = {"one": {"sha256": digest(b"frozen tool bytes")}}
    runtime_copy(source, tmp_path / "copy", inv)
    assert (source / "one").read_bytes() == (tmp_path / "copy/one").read_bytes()
    (source / "one").write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        runtime_copy(source, tmp_path / "bad", inv)
    (source / "alias").symlink_to("../outside")
    with pytest.raises(ValueError, match="escape"):
        runtime_copy(source, tmp_path / "bad-alias", {"alias": {"symlink": "../outside"}})


def test_published_blob_check_and_wrong_hash():
    from deployment import publication_blob

    repo = Path("/home/jjaff/AI-infra-simulation/rk-uarch-u4-b")
    name = "docs/reviews/U4-B-K2-candidate-04-audit-v1/review.json"
    expected = (repo / name).read_bytes()
    commit = "94b072ef5b78aab9a3c1ff97639ddfb4f65b9e26"
    assert publication_blob(repo, commit, name, digest(expected)) == expected
    with pytest.raises(ValueError, match="blob"):
        publication_blob(repo, commit, name, "sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="full commit"):
        publication_blob(repo, "main", name, digest(expected))


def test_incomplete_saved_campaign_refuses_before_any_replay(tmp_path):
    from deployment import verify_saved_campaign

    plan = json.loads((HERE / "campaign-plan.json").read_bytes())
    for record in [
        {},
        {"complete": True, "mapped_calls": 798, "subject": plan["subject"], "calls": []},
    ]:
        with pytest.raises(ValueError):
            verify_saved_campaign(tmp_path, plan, record)


def test_frozen_future_harness_manifest():
    inventory = json.loads((HERE / "campaign-files.expected.json").read_bytes())
    assert set(inventory) == {
        "entrypoint.py",
        "deployment.py",
        "runtime.json",
        "campaign-plan.json",
        "candidate-layout.json",
    }
    for name, binding in inventory.items():
        data = (HERE / name).read_bytes()
        assert binding == {"sha256": digest(data), "bytes": len(data)}
