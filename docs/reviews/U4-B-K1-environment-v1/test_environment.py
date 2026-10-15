"""Host-controller regression tests, not synthetic native qualification evidence."""

import importlib.util
import json
import runpy
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
spec = importlib.util.spec_from_file_location("controller_tests", PACKAGE / "controls.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
c = m.c


def test_refuse_base_as_final_image():
    base = "sha256:" + "a" * 64
    final = "sha256:" + "b" * 64
    info = [
        {"Id": final, "Os": "linux", "Architecture": "amd64", "RootFS": {"Layers": ["sha256:c"]}}
    ]
    c.image_identity(info, final, base)
    with pytest.raises(ValueError, match="base config"):
        c.image_identity(info, final, final)
    info[0]["Architecture"] = "arm64"
    with pytest.raises(ValueError, match="platform"):
        c.image_identity(info, final, base)


def test_full_lock_and_linux_closure_are_distinct():
    guard = runpy.run_path(str(ROOT / c.B / "ci_host_guard.py"))
    closure = guard["validate_package"](ROOT)
    selected = guard["target_closure"](closure)
    assert len(closure) == 27 and len(selected) == 26
    assert {(p["name"], p["version"]) for p in closure} - {
        (p["name"], p["version"]) for p in selected
    } == {("r-efi", "6.0.0")}
    with pytest.raises(ValueError):
        guard["target_closure"](selected)


def test_cache_archives_and_notices_require_exact_bytes():
    closure = [
        {
            "name": "synthetic",
            "version": "1",
            "checksum": "a" * 64,
            "notice_files": [{"path": "LICENSE", "sha256": "b" * 64}],
        }
    ]
    archives = "a" * 64 + "  /cache/synthetic-1.crate\n"
    notices = "b" * 64 + "  /src/synthetic-1/LICENSE\n"
    c.verify_cache(closure, archives, notices)
    for a, n in [
        ("", notices),
        (archives.replace("a" * 64, "c" * 64), notices),
        (archives, ""),
        (archives, notices + notices),
    ]:
        with pytest.raises(ValueError):
            c.verify_cache(closure, a, n)


def test_replays_require_six_complete_equal_binary_payloads():
    outputs = {
        f"{mode}-{n}": b'{"duration_ps":5}' for mode in ("debug", "release") for n in range(3)
    }
    c.compare_replays(outputs)
    outputs["release-2"] += b" "
    with pytest.raises(ValueError, match="mismatch"):
        c.compare_replays(outputs)
    outputs.pop("release-2")
    with pytest.raises(ValueError, match="six"):
        c.compare_replays(outputs)


def test_mutation_restores_exact_bytes_and_mtime_on_failure(tmp_path):
    path = tmp_path / "native/src/lib.rs"
    path.parent.mkdir(parents=True)
    path.write_text("original")
    before = c.snapshot(tmp_path)
    with pytest.raises(RuntimeError):
        with m.mutation(tmp_path, "native/src/lib.rs", "original", "fault", c.digest(path)):
            assert path.read_text() == "fault"
            raise RuntimeError("intentional controller fault")
    assert before == c.snapshot(tmp_path)
    with pytest.raises(ValueError, match="identity"):
        with m.mutation(tmp_path, "native/src/lib.rs", "original", "fault", "0" * 64):
            pytest.fail("wrong source accepted")
    with pytest.raises(ValueError, match="native Rust"):
        with m.mutation(tmp_path, "../outside.rs", remove=True):
            pytest.fail("path escape accepted")


def test_runner_records_failure_and_rejects_stale_receipts(tmp_path):
    status = c.run(tmp_path, "fail", ["bash", "-c", "echo diagnostic >&2; exit 7"], fail=False)
    assert status == 7
    assert json.loads((tmp_path / "fail.json").read_text())["exit"] == 7
    assert (tmp_path / "fail.stderr").read_text() == "diagnostic\n"
    with pytest.raises(ValueError, match="overwrite"):
        c.run(tmp_path, "fail", ["true"])
