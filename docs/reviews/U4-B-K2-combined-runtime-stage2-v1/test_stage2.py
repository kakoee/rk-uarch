"""Stage 2 regressions. All approvals/complete sets here are synthetic, never authority."""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

TARGET = Path(os.environ["STAGE2_PACKAGE"])
sys.path.insert(0, str(TARGET))
import bindings as b  # noqa: E402
import launch  # noqa: E402
import prepare  # noqa: E402

DATA = (TARGET / "candidate.json").read_bytes()
C = json.loads(DATA)
PUB = {"helper_commit": C["B_subject"], "candidate_hash": b.digest(DATA)}
BASE = Path(os.environ["STAGE2_BASELINE"]).resolve()
for module in (b, launch, prepare):
    assert module.__file__ is not None
    assert Path(module.__file__).resolve().parent == TARGET.resolve()


def git(repo, *args, data=None):
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": "/nonexistent",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_AUTHOR_NAME": "synthetic fixture",
        "GIT_AUTHOR_EMAIL": "fixture@invalid",
        "GIT_COMMITTER_NAME": "synthetic fixture",
        "GIT_COMMITTER_EMAIL": "fixture@invalid",
    }
    return subprocess.check_output(
        ["/usr/bin/git", "--no-replace-objects", *args],
        cwd=repo,
        env=env,
        input=data,
        stderr=subprocess.DEVNULL,
    )


@pytest.fixture
def repos(tmp_path):
    local, remote, decoy = [tmp_path / n for n in ("local", "remote.git", "decoy")]
    local.mkdir()
    decoy.mkdir()
    git(local, "init", "-b", "main")
    git(decoy, "init", "-b", "main")
    (local / "data.txt").write_bytes(b"actual published fixture content\n")
    git(local, "add", "data.txt")
    git(local, "commit", "-m", "synthetic initial")
    published = git(local, "rev-parse", "HEAD").decode().strip()
    git(tmp_path, "init", "--bare", str(remote))
    git(local, "remote", "add", "origin", str(remote))
    git(local, "push", "origin", "main")
    git(local, "update-ref", "refs/remotes/origin/main", published)
    (decoy / "data.txt").write_bytes(b"foreign content\n")
    git(decoy, "add", ".")
    git(decoy, "commit", "-m", "synthetic decoy")
    return local, remote, decoy, published


@contextmanager
def publication_context(remote):
    if hasattr(prepare, "publication"):
        with prepare.publication.RemoteView.fixture(remote) as view:
            # Only test publication reads; production renderers disallow simulated views.
            yield lambda repo, commit, path: view.read(commit, path)
    else:
        yield prepare.published


def test_F1_unpushed_local_tracking_ref_is_not_publication(repos):
    local, remote, _, published = repos
    (local / "data.txt").write_bytes(b"UNPUSHED SYNTHETIC DATA\n")
    git(local, "add", ".")
    git(local, "commit", "-m", "not published")
    local_commit = git(local, "rev-parse", "HEAD").decode().strip()
    git(local, "update-ref", "refs/remotes/origin/main", local_commit)
    with publication_context(remote) as read:
        assert read(local, published, "data.txt") == b"actual published fixture content\n"
        with pytest.raises((ValueError, subprocess.CalledProcessError)):
            read(local, local_commit, "data.txt")


def test_F1_replace_and_environment_redirects(repos, monkeypatch):
    local, remote, decoy, published = repos
    (local / "data.txt").write_bytes(b"replaced bytes\n")
    git(local, "add", ".")
    git(local, "commit", "-m", "replacement")
    substitute = git(local, "rev-parse", "HEAD").decode().strip()
    git(local, "replace", published, substitute)
    config = local.parent / "hostile-config"
    config.write_text('[url "file:///not-the-remote/"]\n insteadOf = https://github.com/\n')
    for key, value in {
        "GIT_DIR": str(decoy / ".git"),
        "GIT_WORK_TREE": str(decoy),
        "GIT_COMMON_DIR": str(decoy / ".git"),
        "GIT_OBJECT_DIRECTORY": str(decoy / ".git/objects"),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(decoy / ".git/objects"),
        "GIT_INDEX_FILE": str(decoy / "index"),
        "GIT_REPLACE_REF_BASE": "refs/replace/",
        "GIT_CONFIG": str(config),
        "GIT_CONFIG_GLOBAL": str(config),
        "GIT_CONFIG_SYSTEM": str(config),
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "url.file:///absent/.insteadOf",
        "GIT_CONFIG_VALUE_0": "https://github.com/",
        "GIT_SSH_COMMAND": "false",
        "HOME": str(decoy),
        "XDG_CONFIG_HOME": str(decoy),
        "GIT_CONFIG_PARAMETERS": "'core.bare=true'",
    }.items():
        monkeypatch.setenv(key, value)
    with publication_context(remote) as read:
        assert read(local, published, "data.txt") == b"actual published fixture content\n"


def test_F2_incomplete_launch_refuses_before_process(tmp_path):
    binding = {"synthetic": "NOT A RUNTIME BINDING OR CAMPAIGN"}
    (tmp_path / "campaign.json").write_bytes(
        b.encoded({"runtime_binding": binding, "synthetic": "NOT A CAMPAIGN"})
    )
    (tmp_path / "campaign-launch.json").write_bytes(
        b.encoded({"complete": False, "exit_code": -9, "stop_reason": "outer deadline"})
    )
    (tmp_path / "campaign-failure.json").write_bytes(b.encoded({"complete": False}))
    with pytest.raises(ValueError):
        launch.run(
            ["/bin/sh", "-c", "exit 0", "synthetic-process-fixture"], "replay", tmp_path, binding
        )
    assert not (tmp_path / "replay-launch.json").exists()


def test_F3_private_flags_cannot_create_placed_evidence():
    old = BASE / "docs/reviews/U4-B-K2-combined-runtime-v1"
    saved = json.loads((old / "evidence/private-preflight.json").read_bytes())
    saved.update(status="combined-runtime-import-preflight-passed", private_test=False)
    # Use the same exact candidate binding as the saved diagnostic; no identity setup error.
    with pytest.raises(ValueError, match="observ|seal|placement|root"):
        b.check_preflight(saved, (old / "candidate.json").read_bytes(), saved["publication"])


def core_module():
    p = BASE / "docs/reviews/U4-B-K2-parallel-first-use-v1/parallel_core.py"
    assert (
        hashlib.sha256(p.read_bytes()).hexdigest()
        == "bbe3746760753c388ac1fa3f3420016f008281a1014638863320e073e15348b1"
    )
    spec = importlib.util.spec_from_file_location("real_parallel_core", p)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_F4_store_transient_disappears_during_actual_poll(tmp_path, monkeypatch):
    output = tmp_path / "run"
    core = core_module()
    real_popen, real_unlink = subprocess.Popen, Path.unlink
    pending = []

    def popen(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        with monkeypatch.context() as patch:

            def postpone(path, *a, **k):
                if path.name.startswith(".pending-"):
                    pending.append(path)
                else:
                    real_unlink(path, *a, **k)

            patch.setattr(Path, "unlink", postpone)
            core.Store(output, 2 * 1024**3).json("calls/fixture.json", {"synthetic": "not native"})
        return process

    old_is_file, old_lstat = Path.is_file, Path.lstat
    disappeared: list[str] = []

    def is_file(path):
        answer = old_is_file(path)
        if answer and path in pending and not disappeared:
            real_unlink(path)
            disappeared.append(str(path))
        return answer

    def lstat(path, *a, **k):
        if hasattr(launch, "receipt_bytes") and path in pending and not disappeared:
            real_unlink(path)
            disappeared.append(str(path))
        return old_lstat(path, *a, **k)

    monkeypatch.setattr(subprocess, "Popen", popen)
    monkeypatch.setattr(Path, "is_file", is_file)
    monkeypatch.setattr(Path, "lstat", lstat)
    launch.run(
        ["/bin/sh", "-c", "sleep 0.2", "synthetic-process-fixture"],
        "campaign",
        output,
        {"synthetic": "NOT A CAMPAIGN"},
    )
    assert disappeared and (output / "calls/fixture.json").is_file()
    assert b.read(output / "campaign-launch.json")["exit_code"] == 0


def test_F5_earlier_helper_shadow_refused(tmp_path, monkeypatch):
    (tmp_path / "resource_limits.py").write_text('LABEL = "synthetic shadow, no actions"\n')
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, "resource_limits", raising=False)
    import resource_limits

    modules = {
        n: SimpleNamespace(__file__=str(tmp_path / "project/owned.py"))
        for n in ("rkuarch.engines.native.host", "uarch_contract.hardware")
    }
    modules["resource_limits"] = resource_limits
    if hasattr(b, "helper_origins"):
        expected = {
            "resource_limits": {
                "path": str(tmp_path / "bound/resource_limits.py"),
                "sha256": "sha256:" + "0" * 64,
            }
        }
        with pytest.raises(ValueError, match="helper origin"):
            b.helper_origins(modules, expected)
    else:
        with pytest.raises(ValueError, match="helper origin"):
            b.origins(modules, tmp_path / "project")


def decision():
    old = {
        "format": "uarch-k2-combined-human-decision/1",
        "accepted_by": "Javid (@jjaffari)",
        "reply": "yes",
        "scope": "isolated-protected-runtime-placement-preflight-and-798-call-restart",
        "amendment_hash": C["amendment_hash"],
        "binding": b.identity(DATA),
        "publication": PUB,
    }
    if hasattr(b, "DECISION_FIELDS"):
        old.pop("reply")
        old.update(
            format="uarch-k2-combined-human-decision/2",
            reply_verbatim="Yes, approved.",
            accepted=True,
            disposition="accepted-unconditional",
            conditions=[],
            decision_id=C["decision_id"],
            policy_hash=C["policy_hash"],
        )
    return old


def test_F6_unknown_decision_condition_refused():
    d = decision()
    d["undeclared_condition"] = "SYNTHETIC ONLY; not permission"
    with pytest.raises(ValueError, match="schema|field"):
        b.check_decision(d, DATA, PUB)


def test_F1_no_context_no_offline_fallback():
    with pytest.raises(ValueError, match="actual remote observation"):
        prepare.published(Path("/unused"), C["B_subject"], "data.txt")


def test_F1_wrong_remote_refused():
    with pytest.raises(ValueError, match="exact expected"):
        prepare.publication.RemoteView("https://example.invalid/other.git")


def test_F1_unavailable_remote_refuses(tmp_path):
    with pytest.raises(ValueError, match="no offline fallback"):
        with prepare.publication.RemoteView.fixture(tmp_path / "absent"):
            pytest.fail("unavailable remote accepted")


@pytest.fixture
def complete_campaign(tmp_path, monkeypatch):
    """798 labelled receipt-shape slots; stdout is NOT an EngineResult. No authority."""
    monkeypatch.syspath_prepend(str(b.OLD / "campaign"))
    import deployment

    assert Path(deployment.__file__) == b.OLD / "campaign/deployment.py"
    import receipt_checks as rc

    plan = b.read(b.OLD / "campaign/campaign-plan.json")
    binding = {
        "synthetic": "NOT HUMAN AUTHORITY OR NATIVE RESULTS",
        "native_subject": plan["subject"],
    }
    (tmp_path / "calls").mkdir()
    (tmp_path / "transport").mkdir()
    (tmp_path / "blobs").mkdir()

    def blob(raw):
        name = b.digest(raw)[7:]
        p = tmp_path / "blobs" / name
        if not p.exists():
            p.write_bytes(raw)
        return "blobs/" + name

    rows = []
    for mode, repetition, case in deployment.slots(plan):
        request = (b.OLD / "candidate" / case["file"]["path"]).read_bytes()
        stdout, stderr = b"NOT A NATIVE RESULT: labelled receipt fixture\n", b""
        row = {
            "mode": mode,
            "repetition": repetition,
            "case_id": case["case_id"],
            "request": blob(request),
            "stdout": blob(stdout),
            "stderr": blob(stderr),
            "request_hash": b.digest(request),
            "stdout_hash": b.digest(stdout),
            "stderr_hash": b.digest(stderr),
            "status": 0 if case["outcome"] == "success" else 2,
            "executable_hash": plan["subject"]["executable_byte_hashes"][plan["modes"].index(mode)],
            "receipt": {"synthetic": "not an execution"},
        }
        name = f"{mode}-{repetition}-{case['case_id']}.json"
        (tmp_path / "calls" / name).write_bytes(b.encoded(row))
        (tmp_path / "transport" / name).write_bytes(
            b.encoded({k: row[k] for k in ("request", "stdout", "stderr", "status")})
        )
        rows.append(row)
    campaign = {
        "synthetic": "NOT A CAMPAIGN; metadata-only test",
        "complete": True,
        "mapped_calls": 798,
        "subject": plan["subject"],
        "calls": rows,
        "runtime_binding": binding,
    }
    (tmp_path / "campaign.json").write_bytes(b.encoded(campaign))
    (tmp_path / "resources.json").write_bytes(b.encoded({"workers": 1, "runtime_binding": binding}))
    summary = {
        "workers": 1,
        "runtime_binding": binding,
        "cases": [
            {
                "case_id": c["case_id"],
                "slots": [
                    f"{m}-{r}-{c['case_id']}" for m in plan["modes"] for r in plan["repetitions"]
                ],
            }
            for c in plan["case_membership"]
        ],
    }
    (tmp_path / "worker-summary.json").write_bytes(b.encoded(summary))
    for name in rc.COMPONENTS[-2:]:
        (tmp_path / name).write_bytes(
            b.encoded({p: {"synthetic": "not observed"} for p in rc.SNAPSHOT_ROOTS})
        )
    operation = {
        "stage": "campaign",
        "complete": True,
        "runtime_binding": binding,
        "component_hashes": rc.component_hashes(tmp_path),
    }
    (tmp_path / "campaign-operational.json").write_bytes(b.encoded(operation))
    (tmp_path / "campaign-launch.json").write_bytes(
        b.encoded(
            {
                "stage": "campaign",
                "complete": True,
                "exit_code": 0,
                "stop_reason": None,
                "runtime_binding": binding,
                "operational_hash": b.digest((tmp_path / "campaign-operational.json").read_bytes()),
            }
        )
    )
    return tmp_path, binding, plan


def test_F2_complete_consistent_receipt_fixture(complete_campaign):
    import receipt_checks as rc

    root, binding, plan = complete_campaign
    assert rc.replay_admission(root, binding, plan)["campaign_hash"] == b.digest(
        (root / "campaign.json").read_bytes()
    )
    launch.run(["/bin/sh", "-c", "exit 0", "synthetic-process-fixture"], "replay", root, binding)
    assert b.read(root / "replay-launch.json")["runtime_binding"]["synthetic"]
    assert not (root / "replays.json").exists()


@pytest.mark.parametrize(
    "fault",
    [
        "missing-launch",
        "missing-operation",
        "nonzero",
        "incomplete",
        "stop-reason",
        "failure",
        "stale-binding",
        "contradictory-operation",
        "missing-snapshot",
        "changed-snapshot",
        "missing-transport",
        "wrong-outcome",
        "missing-worker",
    ],
)
def test_F2_full_set_faults_refuse(complete_campaign, fault):
    import receipt_checks as rc

    root, binding, plan = complete_campaign
    if fault.startswith("missing-"):
        names = {
            "missing-launch": "campaign-launch.json",
            "missing-operation": "campaign-operational.json",
            "missing-snapshot": "input-snapshot-after.json",
        }
        if fault in names:
            (root / names[fault]).unlink()
        elif fault == "missing-transport":
            next((root / "transport").iterdir()).unlink()
        else:
            x = b.read(root / "worker-summary.json")
            x["cases"].pop()
            (root / "worker-summary.json").write_bytes(b.encoded(x))
    elif fault == "failure":
        (root / "campaign-failure.json").write_bytes(b"{}")
    elif fault == "changed-snapshot":
        (root / "input-snapshot-after.json").write_bytes(b"{}")
    elif fault == "contradictory-operation":
        x = b.read(root / "campaign-operational.json")
        x["complete"] = False
        (root / "campaign-operational.json").write_bytes(b.encoded(x))
    elif fault == "wrong-outcome":
        x = b.read(root / "campaign.json")
        x["calls"][0]["status"] = 3
        (root / "campaign.json").write_bytes(b.encoded(x))
    else:
        x = b.read(root / "campaign-launch.json")
        if fault == "nonzero":
            x["exit_code"] = -9
        elif fault == "incomplete":
            x["complete"] = False
        elif fault == "stop-reason":
            x["stop_reason"] = "killed after campaign.json"
        else:
            x["runtime_binding"] = {"synthetic": "stale binding"}
        (root / "campaign-launch.json").write_bytes(b.encoded(x))
    expected_reason = None
    if fault in ("changed-snapshot", "wrong-outcome", "missing-worker"):
        # Rebind outer hashes so this proves the underlying invariant, not a stale hash.
        operation = b.read(root / "campaign-operational.json")
        operation["component_hashes"] = rc.component_hashes(root)
        (root / "campaign-operational.json").write_bytes(b.encoded(operation))
        launch_record = b.read(root / "campaign-launch.json")
        launch_record["operational_hash"] = b.digest(
            (root / "campaign-operational.json").read_bytes()
        )
        (root / "campaign-launch.json").write_bytes(b.encoded(launch_record))
        expected_reason = {
            "changed-snapshot": "required equal input snapshots",
            "wrong-outcome": "saved outcome drift",
            "missing-worker": "complete worker cases",
        }[fault]
    with pytest.raises(ValueError, match=expected_reason):
        rc.replay_admission(root, binding, plan)


def synthetic_preflight() -> dict[str, Any]:
    observed: dict[str, Any] = {
        "payload": {},
        "mounts": {},
        "authority_selector_present": False,
        "runtime_authority_present": False,
    }
    for mount, suffix, members in [
        ("/project", "project", C["project"]),
        ("/combined", "helpers", C["helpers"]),
        (
            "/combined-record",
            "record",
            {"candidate.json": b.digest(DATA), "publication.json": b.digest(b.encoded(PUB))},
        ),
    ]:
        observed["payload"][mount] = {
            "seal_check_enforced": True,
            "all_root_owned": True,
            "all_inodes_readonly": True,
            "root_uid": 0,
            "root_mode": 0o555,
            "inventory_hash": b.digest(b.encoded(members)),
            "files_checked": sorted(members),
        }
        observed["mounts"][mount] = {"source_root": str(b.NEW / suffix), "mount_options": ["ro"]}
    return {
        "synthetic_fixture": "NOT AN OBSERVED PREFLIGHT OR HOST",
        "status": "combined-runtime-import-preflight-passed",
        "binding": b.identity(DATA),
        "publication": PUB,
        "observations": observed,
        "native_calls": 0,
        "authority_resolved": False,
        "private_test": False,
        "all_module_origins": {"synthetic": {}},
        "helper_origins": C["helper_imports"],
    }


def test_F3_observation_shape_and_private_distinctions():
    pf = synthetic_preflight()
    b.check_preflight(pf, DATA, PUB)  # shape-only; no publication/placement or authority made
    for key, value in [
        ("seal_check_enforced", False),
        ("root_uid", 1000),
        ("all_root_owned", False),
        ("all_inodes_readonly", False),
    ]:
        bad = json.loads(json.dumps(pf))
        bad["observations"]["payload"]["/project"][key] = value
        with pytest.raises(ValueError, match="observed production seal"):
            b.check_preflight(bad, DATA, PUB)
    pf["observations"]["mounts"]["/project"]["source_root"] = "/tmp/private/project"
    with pytest.raises(ValueError, match="observed deployment"):
        b.check_preflight(pf, DATA, PUB)


def test_F3_measure_real_private_files_and_mount_parser(tmp_path):
    p = tmp_path / "source.py"
    p.write_bytes(b"# fixture")
    result = b.observed_payload(tmp_path, {"source.py": b.digest(p.read_bytes())}, sealed=False)
    assert result["root_uid"] == os.getuid() and result["seal_check_enforced"] is False
    mounts = b.mount_observations(
        "23 1 8:1 /tmp/private/project /project ro,nosuid - ext4 /dev/sda rw\n"
    )
    assert mounts["/project"]["source_root"] == "/tmp/private/project"


def test_F4_persistent_budget_symlink_and_other_errors(tmp_path, monkeypatch):
    (tmp_path / "persistent").write_bytes(b"x" * 9000)
    assert launch.receipt_bytes(tmp_path) == 9000
    (tmp_path / "link").symlink_to("persistent")
    with pytest.raises(ValueError, match="receipt symlink"):
        launch.receipt_bytes(tmp_path)
    (tmp_path / "link").unlink()
    old = Path.lstat

    def denied(path, *a, **k):
        if path.name == "persistent":
            raise PermissionError("synthetic inaccessible persistent file")
        return old(path, *a, **k)

    monkeypatch.setattr(Path, "lstat", denied)
    with pytest.raises(PermissionError):
        launch.receipt_bytes(tmp_path)


def test_F5_bound_helper_and_module_kinds(tmp_path):
    path = tmp_path / "helper.py"
    path.write_bytes(b"# bound helper fixture")
    module = SimpleNamespace(__file__=str(path), __spec__=SimpleNamespace(origin=str(path)))
    expected = {"helper": {"path": str(path), "sha256": b.digest(path.read_bytes())}}
    assert b.helper_origins({"helper": module}, expected) == expected
    kinds = b.module_origins(
        {
            "helper": module,
            "builtin": SimpleNamespace(__spec__=SimpleNamespace(origin="built-in")),
            "frozen": SimpleNamespace(__spec__=SimpleNamespace(origin="frozen")),
            "no_file": SimpleNamespace(),
        }
    )
    assert [kinds[n]["kind"] for n in ("builtin", "frozen", "no_file")] == [
        "built-in",
        "frozen",
        "no-file",
    ]
    with pytest.raises(ValueError, match="helper origin"):
        b.helper_origins({"helper": SimpleNamespace()}, expected)


@pytest.mark.parametrize(
    "reply",
    ["yes", "Yes, approved.", "I approve the exact bounded proposal.", "  Approved as proposed.\n"],
)
def test_F6_verbatim_affirmative_shape(reply):
    d = decision()
    d["reply_verbatim"] = reply
    before = b.encoded(d)
    b.check_decision(d, DATA, PUB)  # synthetic shape only, never published or installed
    assert b.encoded(d) == before


@pytest.mark.parametrize(
    "fault",
    [
        "condition",
        "rejection",
        "missing",
        "extra",
        "candidate",
        "decision-id",
        "empty-reply",
        "non-bool",
        "wrong-policy",
    ],
)
def test_F6_decision_refusals(fault):
    d = decision()
    if fault == "condition":
        d.update(
            reply_verbatim="Yes, provided additional review passes.",
            accepted=True,
            disposition="conditional",
            conditions=["additional review unresolved"],
        )
    elif fault == "rejection":
        d.update(reply_verbatim="No.", accepted=False, disposition="rejected")
    elif fault == "missing":
        d.pop("reply_verbatim")
    elif fault == "extra":
        d["condition"] = "extra unresolved field"
    elif fault == "candidate":
        d["binding"] = {"synthetic": "different candidate"}
    elif fault == "decision-id":
        d["decision_id"] = "wrong-decision"
    elif fault == "empty-reply":
        d["reply_verbatim"] = " \n"
    elif fault == "non-bool":
        d["accepted"] = 1
    else:
        d["policy_hash"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError):
        b.check_decision(d, DATA, PUB)


def test_F2_container_gate_precedes_resolution(tmp_path, monkeypatch):
    import runtime_entry as r

    binding = {"synthetic": "not authority"}
    (tmp_path / "campaign.json").write_bytes(b.encoded({"runtime_binding": binding}))
    (tmp_path / "campaign-failure.json").write_bytes(b"{}")

    def forbidden(*args):
        raise AssertionError("replay authority/transport boundary was reached")

    fake = SimpleNamespace(dump=lambda *args: None, replay=forbidden)
    monkeypatch.setattr(r, "BASE", fake)
    monkeypatch.setattr(r, "BINDING", None)
    monkeypatch.setattr(r, "OUT", tmp_path)
    monkeypatch.setattr(
        r, "configure", lambda: SimpleNamespace(verify_snapshots=lambda *args: None)
    )
    monkeypatch.setattr(r, "common", lambda: (None, {}, None))
    monkeypatch.setattr(r, "guards", lambda: ({}, "fixture"))
    monkeypatch.setattr(r, "release", lambda: binding)
    monkeypatch.setattr(r, "snapshots", lambda: {})
    with pytest.raises(ValueError, match="campaign failure"):
        r.main("replay")


def test_F1_replacement_cannot_substitute_published_bytes(repos):
    local, remote, _, published = repos
    with publication_context(remote) as read:
        assert read(local, published, "data.txt") == b"actual published fixture content\n"
    (local / "data.txt").write_bytes(b"replacement-object bytes\n")
    git(local, "add", ".")
    git(local, "commit", "-m", "synthetic replacement")
    replacement = git(local, "rev-parse", "HEAD").decode().strip()
    git(local, "replace", published, replacement)
    with publication_context(remote) as read:
        assert read(local, published, "data.txt") == b"actual published fixture content\n"


def test_F1_patch_application_ignores_git_redirection(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "sample.txt").write_bytes(b"before\n")
    decoy = tmp_path / "foreign"
    decoy.mkdir()
    git(decoy, "init", "-b", "main")
    (decoy / "sample.txt").write_bytes(b"foreign\n")
    monkeypatch.setenv("GIT_DIR", str(decoy / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(decoy))
    patch = b"--- a/sample.txt\n+++ b/sample.txt\n@@ -1 +1 @@\n-before\n+after\n"
    prepare.apply(source, patch, check=True)
    prepare.apply(source, patch, check=False)
    assert (source / "sample.txt").read_bytes() == b"after\n"
    assert (decoy / "sample.txt").read_bytes() == b"foreign\n"
