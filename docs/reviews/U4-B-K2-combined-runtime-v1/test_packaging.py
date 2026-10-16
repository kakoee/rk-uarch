"""Packaging-only discriminators; no engine authority or native result fixtures."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import bindings as b
import launch
import pytest

HERE = Path(__file__).resolve().parent
CANDIDATE = (HERE / "candidate.json").read_bytes()
C = json.loads(CANDIDATE)


def fixture_payload(root):
    project, helpers, record = [root / n for n in ("project", "helpers", "record")]
    for p in (project, helpers, record):
        p.mkdir()
    (project / "sample.py").write_bytes(b"# synthetic packaging fixture\n")
    (helpers / "parallel_entrypoint.py").write_bytes(b"# never executed\n")
    c = copy.deepcopy(C)
    c["project"] = {"sample.py": b.digest((project / "sample.py").read_bytes())}
    c["helpers"] = {
        "parallel_entrypoint.py": b.digest((helpers / "parallel_entrypoint.py").read_bytes())
    }
    data = b.encoded(c)
    (record / "candidate.json").write_bytes(data)
    publication = {"helper_commit": C["B_subject"], "candidate_hash": b.digest(data)}
    (record / "publication.json").write_bytes(b.encoded(publication))
    return project, helpers, record, data, publication


def test_positive_payload_is_only_integrity(tmp_path):
    project, helpers, record, data, publication = fixture_payload(tmp_path)
    assert b.check_payload(project, helpers, record, sealed=False)[1] == data
    with pytest.raises(FileNotFoundError):
        b.check_authority(tmp_path / "absent-authority", data, publication)
    with pytest.raises(ValueError, match="sealed"):
        b.check_payload(project, helpers, record, sealed=True)


@pytest.mark.parametrize(
    "fault",
    ["missing", "extra", "changed-source", "changed-helper", "symlink", "stale-publication"],
)
def test_payload_refuses_before_authority(tmp_path, fault):
    project, helpers, record, _, _ = fixture_payload(tmp_path)
    if fault == "missing":
        (project / "sample.py").unlink()
    elif fault == "extra":
        (project / "extra.py").write_bytes(b"")
    elif fault == "changed-source":
        (project / "sample.py").write_bytes(b"# drift")
    elif fault == "changed-helper":
        (helpers / "parallel_entrypoint.py").write_bytes(b"# drift")
    elif fault == "symlink":
        (project / "sample.py").unlink()
        (project / "sample.py").symlink_to(helpers / "parallel_entrypoint.py")
    else:
        pub = b.read(record / "publication.json")
        pub["candidate_hash"] = "sha256:" + "0" * 64
        (record / "publication.json").write_bytes(b.encoded(pub))
    with pytest.raises(ValueError):
        b.check_payload(project, helpers, record, sealed=False)


def test_project_origin_positive_and_foreign(tmp_path):
    modules = {
        n: SimpleNamespace(__file__=str(tmp_path / "owned.py"))
        for n in ("rkuarch.engines.native.host", "uarch_contract.hardware")
    }
    assert len(b.origins(modules, tmp_path)) == 2
    modules["uarch_contract.hardware"].__file__ = "/candidate/contract/uarch_contract/hardware.py"
    with pytest.raises(ValueError, match="wrong project import origin"):
        b.origins(modules, tmp_path)


@pytest.mark.parametrize("name", sorted(C["old_files"]))
def test_wrong_original_binding(tmp_path, name):
    subset = {"old_files": {name: C["old_files"][name]}}
    path = tmp_path / name
    path.parent.mkdir(parents=True)
    path.write_bytes((b.OLD / name).read_bytes())
    b.old_bindings(tmp_path, subset)
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="original native/runtime binding"):
        b.old_bindings(tmp_path, subset)


def synthetic_authority(root, data, publication):
    """Deliberately NON-authorizing records, for early-refusal layer discrimination."""
    root.mkdir()
    records = {
        n: {
            "binding": b.identity(data),
            "publication": publication,
            "format": "synthetic-not-human-authority",
        }
        for n in ("decision.json", "placement.json", "preflight.json", "release.json")
    }
    files = {}
    for name, value in records.items():
        raw = b.encoded(value)
        (root / name).write_bytes(raw)
        files[name] = b.digest(raw)
    selector = {"binding": b.identity(data), "publication": publication, "files": files}
    (root / "selector.json").write_bytes(b.encoded(selector))


@pytest.mark.parametrize(
    "fault",
    [
        "rehashed-closure",
        "rehashed-helper",
        "swapped-native",
        "stale-publication",
        "missing",
        "extra",
        "tampered-approval",
    ],
)
def test_unapproved_refusal_precedes_decision_or_execution(tmp_path, fault):
    project, helpers, record, data, publication = fixture_payload(tmp_path)
    authority = tmp_path / "authority"
    synthetic_authority(authority, data, publication)
    changed = json.loads(data)
    if fault == "rehashed-closure":
        changed["project"]["sample.py"] = b.digest(b"new self-consistent source")
    elif fault == "rehashed-helper":
        changed["helpers"]["parallel_entrypoint.py"] = b.digest(b"new helper")
    elif fault == "swapped-native":
        changed["native_source"] = "0" * 40
    elif fault == "stale-publication":
        publication = {**publication, "helper_commit": "0" * 40}
    elif fault == "missing":
        (authority / "release.json").unlink()
    elif fault == "extra":
        (authority / "extra.json").write_bytes(b"{}")
    else:
        (authority / "decision.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="complete exact|external selector|unapproved/swapped"):
        b.check_authority(authority, b.encoded(changed), publication)


def test_no_synthetic_approval(tmp_path):
    _, _, _, data, publication = fixture_payload(tmp_path)
    authority = tmp_path / "authority"
    synthetic_authority(authority, data, publication)
    with pytest.raises(ValueError, match="actual human decision"):
        b.check_authority(authority, data, publication)


def test_private_preflight_is_not_placement():
    pf = {"status": "private-composition-passed"}
    with pytest.raises(ValueError, match="actual placed preflight"):
        b.check_preflight(pf, CANDIDATE, {})


@pytest.mark.parametrize("action", ["preflight", "campaign", "replay"])
def test_rendered_command_boundary(action):
    argv = launch.command(action, Path("/tmp/u4-future-combined-campaign"), C)
    text = "\n".join(argv)
    for required in [
        "/project,readonly",
        "/combined,readonly",
        "/candidate,readonly",
        "--pull",
        "never",
        "--network",
        "none",
        "1000:1000",
        "--cap-drop",
        "ALL",
        "no-new-privileges",
        "/python/bin/python3.12",
        "-I",
        "-S",
        "-B",
    ]:
        assert required in text
    assert ("/etc/rkuarch/k2-host-selector.json" in text) == (action != "preflight")
    assert ("/combined-authority" in text) == (action != "preflight")
    assert "LD_LIBRARY_PATH" not in text
    assert "runtime_entry.py" in text


def test_stopped_output_and_quick_actions_refuse():
    with pytest.raises(ValueError, match="preserve stopped"):
        launch.command("campaign", "/tmp/u4-k2-approved-campaign/new", C)
    with pytest.raises(ValueError, match="explicit action"):
        launch.command("quick", "/tmp/u4-new", C)
