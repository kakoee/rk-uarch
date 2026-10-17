"""Replay admission checks only; receipt consistency is not semantic/native qualification."""

from pathlib import Path
from typing import Any

import bindings as b

COMPONENTS = (
    "campaign.json",
    "resources.json",
    "worker-summary.json",
    "input-snapshot-before.json",
    "input-snapshot-after.json",
)
SNAPSHOT_ROOTS = (
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
)


def component_hashes(root: Path) -> dict[str, str]:
    return {name: b.digest((root / name).read_bytes()) for name in COMPONENTS}


def replay_admission(root: Path, binding: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    """Host and container both call this before replay resolution/transport."""
    root = Path(root)
    b.need(root.is_dir() and not root.is_symlink(), "real campaign output required")
    b.need(not any(root.glob("*failure*.json")), "campaign failure receipt forbids replay")
    required = (*COMPONENTS, "campaign-launch.json", "campaign-operational.json")
    b.need(
        all((root / n).is_file() and not (root / n).is_symlink() for n in required),
        "complete campaign receipt set required",
    )
    campaign, launch, operation, resources, summary = [
        b.read(root / n)
        for n in (
            "campaign.json",
            "campaign-launch.json",
            "campaign-operational.json",
            "resources.json",
            "worker-summary.json",
        )
    ]
    for record in (campaign, launch, operation, resources, summary):
        b.need(record.get("runtime_binding") == binding, "same runtime/input binding required")
    b.need(
        launch.get("complete") is True
        and launch.get("exit_code") == 0
        and launch.get("stop_reason") is None
        and launch.get("stage") == "campaign",
        "complete exit-0 campaign launch required",
    )
    b.need(
        operation.get("stage") == "campaign" and operation.get("complete") is True,
        "complete campaign operational receipt required",
    )
    b.need(
        operation.get("component_hashes") == component_hashes(root),
        "operational component identity",
    )
    b.need(
        launch.get("operational_hash")
        == b.digest((root / "campaign-operational.json").read_bytes()),
        "launch/operational identity",
    )
    before, after = [b.read(root / n) for n in COMPONENTS[-2:]]
    b.need(
        bool(before) and before == after and all(p in before for p in SNAPSHOT_ROOTS),
        "required equal input snapshots",
    )
    b.need(
        campaign.get("complete") is True
        and campaign.get("mapped_calls") == 798
        and campaign.get("subject") == plan["subject"] == binding["native_subject"],
        "complete exact native subject/campaign",
    )
    # The original hard-pinned slot/outcome/request and byte-LF/blob checks remain.
    from deployment import slots, verify_saved_campaign

    expected = slots(plan)
    verify_saved_campaign(root, plan, campaign)
    rows = campaign["calls"]
    b.need(
        len(rows) == 798
        and sum(r["status"] == 0 for r in rows) == 780
        and sum(r["status"] == 2 for r in rows) == 18,
        "exact success/refusal outcomes",
    )
    names = [f"{m}-{r}-{c['case_id']}" for m, r, c in expected]
    for directory in ("calls", "transport"):
        b.need(
            {p.name for p in (root / directory).iterdir()} == {n + ".json" for n in names},
            "exact saved receipt membership",
        )
    for name, row in zip(names, rows, strict=True):
        b.need(
            b.read(root / "transport" / (name + ".json"))
            == {k: row[k] for k in ("request", "stdout", "stderr", "status")},
            "checked/transport consistency",
        )
    cases = summary.get("cases", [])
    wanted = [c["case_id"] for c in plan["case_membership"]]
    b.need([c["case_id"] for c in cases] == wanted, "complete worker cases")
    returned = [n for c in cases for n in c["slots"]]
    b.need(
        len(returned) == len(set(returned)) == 798 and set(returned) == set(names),
        "complete worker slots",
    )
    b.need(
        summary.get("workers") == resources.get("workers")
        and type(resources.get("workers")) is int
        and resources["workers"] > 0,
        "nonempty matching worker selection",
    )
    b.need(not (root / "replays.json").exists(), "fresh replay required; no implicit retry")
    return {
        "campaign_hash": b.digest((root / "campaign.json").read_bytes()),
        "launch_hash": b.digest((root / "campaign-launch.json").read_bytes()),
        "operational_hash": b.digest((root / "campaign-operational.json").read_bytes()),
    }
