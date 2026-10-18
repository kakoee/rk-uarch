"""Synthetic Linux interface controls; no native results or authority."""

import runpy
from pathlib import Path

import pytest

from validation.component.runtime_resources import inspect_cgroups

ROOT = Path(__file__).resolve().parents[2]
SELECT = runpy.run_path(
    str(ROOT / "docs/reviews/U4-B-K2-parallel-first-use-v1/resource_limits.py")
)["select_resources"]


def fixture(tmp_path, name="/parent/worker"):
    mount = tmp_path / "cgroup"
    group = mount / name.lstrip("/")
    group.mkdir(parents=True)
    (mount / "cgroup.controllers").write_text("cpu memory pids cpuset\n")
    for p in (mount / "parent", group):
        if p == mount:
            continue
        p.mkdir(exist_ok=True)
        (p / "cgroup.type").write_text("domain\n")
        (p / "cpu.max").write_text("max 100000\n")
        (p / "memory.max").write_text("max\n")
        (p / "memory.current").write_text("100\n")
    info = f"120 111 0:23 / {mount} rw - cgroup2 cgroup2 rw\n"
    return mount, group, f"0::{name}\n", info


def budget(value):
    return SELECT(
        set(range(8)),
        value["quotas"],
        10_000,
        value["memory"],
        reserve=500,
        per_worker=1000,
        tasks=8,
    )


def test_real_root_absence_does_not_mean_missing_child_limits(tmp_path):
    mount, group, membership, info = fixture(tmp_path)
    value = inspect_cgroups(membership, info)
    assert budget(value)["workers"] == 8
    assert (
        value["observed_cgroups"][-1]["interface"]
        == "hierarchy-root-no-bandwidth-or-memory-interface"
    )
    (group / "cpu.max").unlink()
    with pytest.raises(ValueError, match="incomplete non-root"):
        inspect_cgroups(membership, info)


def test_every_ancestor_cpu_and_memory_limit_is_applied(tmp_path):
    mount, group, membership, info = fixture(tmp_path)
    (mount / "parent/cpu.max").write_text("250000 100000\n")
    (group / "memory.max").write_text("7000\n")
    value = inspect_cgroups(membership, info)
    assert budget(value)["workers"] == 2
    assert budget(value)["effective_cpu_capacity"] == "5/2"
    (mount / "parent/memory.max").write_text("2500\n")
    assert budget(inspect_cgroups(membership, info))["workers"] == 1
    (mount / "parent/cpu.max").write_text("50000 100000\n")
    with pytest.raises(ValueError, match="less than one"):
        budget(inspect_cgroups(membership, info))


def test_mount_root_with_limits_is_never_skipped(tmp_path):
    mount, _, membership, info = fixture(tmp_path)
    (mount / "cgroup.type").write_text("domain\n")
    (mount / "cpu.max").write_text("100000 100000\n")
    (mount / "memory.max").write_text("2000\n")
    (mount / "memory.current").write_text("100\n")
    assert budget(inspect_cgroups(membership, info))["workers"] == 1
    (mount / "memory.max").write_text("1200\n")
    with pytest.raises(ValueError, match="insufficient measured memory"):
        budget(inspect_cgroups(membership, info))


@pytest.mark.parametrize(
    "attack",
    [
        "partial-root",
        "namespace-missing-controls",
        "missing-ancestor",
        "hidden-mount",
        "parent-escape",
        "ambiguous-mount",
        "no-memory-controller",
        "malformed-cpu",
        "negative-memory",
    ],
)
def test_unknown_or_invalid_limits_refuse(tmp_path, attack):
    mount, group, membership, info = fixture(tmp_path)
    if attack == "partial-root":
        (mount / "cpu.max").write_text("max 100000\n")
    elif attack == "namespace-missing-controls":
        (mount / "cgroup.type").write_text("domain\n")
    elif attack == "missing-ancestor":
        (mount / "parent/memory.max").unlink()
    elif attack == "hidden-mount":
        info = info.replace("0:23 / ", "0:23 /hidden ")
    elif attack == "parent-escape":
        membership = "0::/../worker\n"
    elif attack == "ambiguous-mount":
        info += info
    elif attack == "no-memory-controller":
        (mount / "cgroup.controllers").write_text("cpu\n")
    elif attack == "malformed-cpu":
        (group / "cpu.max").write_text("max 0\n")
    elif attack == "negative-memory":
        (group / "memory.current").write_text("-1\n")
    with pytest.raises(ValueError):
        inspect_cgroups(membership, info)


def test_membership_is_literal_but_mountinfo_escapes_are_decoded(tmp_path):
    mount, group, membership, info = fixture(tmp_path, name=r"/parent/worker\040name")
    assert inspect_cgroups(membership, info)["observed_cgroups"][0]["path"] == str(group)
