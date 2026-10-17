"""Render exact human placement scripts only. Never sudo, install or launch."""

import argparse
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import bindings as b
import publication

HERE = Path(__file__).resolve().parent
A_PACKAGE = "docs/reviews/U4-A-K2-python-admission-v1/"
B_PACKAGE = "docs/reviews/U4-B-K2-parallel-first-use-v1/"


def published(repo, commit, path):
    # repo is never an object/config authority; read only the fresh verified remote context.
    return publication.published(commit, path)


def checked_bundle(repo, commit):
    data = published(repo, commit, b.PACKAGE + "candidate.json")
    c = json.loads(data)
    for name, expected in c["tools"].items():
        actual = published(repo, commit, b.PACKAGE + name)
        b.need(
            b.digest(actual) == expected and (HERE / name).read_bytes() == actual,
            "exact published preparation/launcher tool: " + name,
        )
    texts = {
        "normative-addendum.txt": c["amendment_hash"],
        "policy-choices.md": c["policy_hash"],
        **c["policy_patches"],
    }
    for name, expected in texts.items():
        actual = published(repo, commit, b.PACKAGE + name)
        b.need(
            b.digest(actual) == expected and (HERE / name).read_bytes() == actual,
            "exact proposed policy text: " + name,
        )
    return c, data


def apply(root, patch, *, check):
    subprocess.run(
        ["/usr/bin/git", "--no-replace-objects", "apply", *(["--check"] if check else []), "-"],
        input=patch,
        cwd=root,
        check=True,
        env=publication.environment(Path("/nonexistent")),
    )


def payload(repo, commit, c, data):
    result = {}
    proposal = json.loads(
        published(repo, c["B_subject"], B_PACKAGE + "combined-reuse-proposal.json")
    )
    with tempfile.TemporaryDirectory(prefix="u4-combined-compose-") as tmp:
        root = Path(tmp)
        for name in c["project"]:
            path = root / b.relative(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(published(repo, c["native_source"], name))
        for name, patch in [
            ("src/rkuarch/engines/native/runner.py", "runner.patch"),
            ("contract/uarch_contract/hardware.py", "hardware-rule.patch"),
            ("src/rkuarch/engines/native/host.py", "host-session.patch"),
        ]:
            raw = published(repo, c["A_subject"], A_PACKAGE + patch)
            b.need(
                b.digest(raw) == "sha256:" + proposal["A_bindings"][name]["patch_sha256"],
                "exact A patch",
            )
            apply(root, raw, check=True)
            apply(root, raw, check=False)
        b.inventory(root, c["project"], sealed=False)
        for name in c["project"]:
            result["project/" + name] = (root / name).read_bytes()
    with tempfile.TemporaryDirectory(prefix="u4-combined-helper-") as tmp:
        root = Path(tmp)
        for name, expected in c["helpers"].items():
            if name in ("runtime_entry.py", "bindings.py", "receipt_checks.py"):
                raw = published(repo, commit, b.PACKAGE + name)
            else:
                raw = published(repo, c["B_subject"], B_PACKAGE + name)
            if name == "parallel_entrypoint.py":
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                patch = published(
                    repo, c["B_subject"], B_PACKAGE + "combined-reuse-integration.patch"
                )
                b.need(b.digest(patch) == proposal["B_patch"], "exact combined patch")
                apply(root, patch, check=True)
                apply(root, patch, check=False)
                raw = target.read_bytes()
            b.need(b.digest(raw) == expected, "exact helper: " + name)
            result["helpers/" + name] = raw
    result["record/candidate.json"] = data
    result["record/publication.json"] = b.encoded(
        {"helper_commit": commit, "candidate_hash": b.digest(data)}
    )
    return result


def script(files, initial):
    # Literal embedded bytes. Never source a user-writable script as part of root placement.
    lines = ["#!/bin/sh", "set -euC", 'test "$(id -u)" = 0']
    for parent in reversed((b.NEW.parent, *b.NEW.parent.parents)):
        lines += [
            f"test -d {parent}",
            f"test ! -L {parent}",
            f'test "$(stat -c %u {parent})" = 0',
            f'test "$(find {parent} -maxdepth 0 -perm /022 -print)" = ""',
        ]
    if initial:
        lines += [f"test ! -e {b.NEW}", f"test ! -L {b.NEW}", f"mkdir -m 0555 -- {b.NEW}"]
        directories = {b.NEW / "authority"}
        for name in files:
            directories.update(
                p for p in (b.NEW / name).parents if p != b.NEW and p.is_relative_to(b.NEW)
            )
        for p in sorted(directories, key=lambda x: (len(x.parts), str(x))):
            lines.append(f"mkdir -m 0555 -- {p}")
    else:
        lines += [
            f"test -d {b.NEW}",
            f"test ! -L {b.NEW}",
            f'test "$(stat -c %u {b.NEW})" = 0',
            f'test "$(find {b.NEW} -maxdepth 0 -perm /222 -print)" = ""',
            f"test -d {b.NEW}/authority",
            f"test ! -L {b.NEW}/authority",
            f'test "$(stat -c %u {b.NEW}/authority)" = 0',
            f'test "$(find {b.NEW}/authority -maxdepth 0 -perm /222 -print)" = ""',
            f'test "$(find {b.NEW}/authority -mindepth 1 -print -quit)" = ""',
        ]
    for name, raw in sorted(files.items()):
        p = b.NEW / b.relative(name)
        lines += [
            f"test ! -e {p}",
            f"test ! -L {p}",
            f"printf %s '{base64.b64encode(raw).decode()}' | /usr/bin/base64 -d > {p}",
            f"chown root:root -- {p}",
            f"chmod 0444 -- {p}",
            f"printf '%s\\n' '{b.digest(raw)[7:]}  {p}' | /usr/bin/sha256sum -c -",
        ]
    return ("\n".join(lines) + "\n").encode()


def authority_files(repo, commit, data, decision_commit, placement_commit, preflight):
    publication = {"helper_commit": commit, "candidate_hash": b.digest(data)}
    decision = published(repo, decision_commit, b.DECISION)
    placement = published(repo, placement_commit, b.PLACEMENT)
    pf = preflight.read_bytes()
    binding = b.identity(data)
    release = b.encoded(
        {
            "status": "human-authorized-combined-runtime",
            "root": str(b.NEW),
            "binding": binding,
            "publication": publication,
            "decision_commit": decision_commit,
            "placement_commit": placement_commit,
            "decision_hash": b.digest(decision),
            "placement_hash": b.digest(placement),
            "preflight_hash": b.digest(pf),
        }
    )
    files = {
        "decision.json": decision,
        "placement.json": placement,
        "preflight.json": pf,
        "release.json": release,
    }
    files["selector.json"] = b.encoded(
        {
            "binding": binding,
            "publication": publication,
            "decision_commit": decision_commit,
            "placement_commit": placement_commit,
            "files": {n: b.digest(v) for n, v in files.items()},
        }
    )
    with tempfile.TemporaryDirectory(prefix="u4-authority-check-") as tmp:
        for n, raw in files.items():
            (Path(tmp) / n).write_bytes(raw)
        b.check_authority(tmp, data, publication)
    return {"authority/" + n: raw for n, raw in files.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("payload", "placement", "binding"))
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--publication", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--decision-commit")
    p.add_argument("--placement-commit")
    p.add_argument("--preflight", type=Path)
    a = p.parse_args()
    with publication.observe() as view:
        try:
            execute(a, view)
        finally:
            # Keep the actual remote observation even when a later guard refuses.
            print(
                json.dumps({"publication_check": view.receipt()}, sort_keys=True), file=sys.stderr
            )


def execute(a, view):
    c, data = checked_bundle(a.repo, a.publication)
    b.old_bindings(b.OLD, c)
    b.need(
        b.digest((b.OLD / "authority/k2-host-selector.json").read_bytes())
        == c["native_selector_hash"],
        "original root-owned native selector",
    )
    out = a.output.absolute()
    b.need(
        out.is_relative_to("/tmp") and out.resolve() == out and not out.exists(),
        "new private preparation path",
    )
    if a.stage in ("payload", "placement"):
        b.need(not b.NEW.exists() and not b.NEW.is_symlink(), "new deployment target only")
        files = payload(a.repo, a.publication, c, data)
        if a.stage == "placement":
            b.need(a.decision_commit is not None, "actual published human decision required")
            decision = json.loads(published(a.repo, a.decision_commit, b.DECISION))
            b.check_decision(
                decision, data, {"helper_commit": a.publication, "candidate_hash": b.digest(data)}
            )
    else:
        b.need(
            a.preflight is not None and a.decision_commit and a.placement_commit,
            "actual approval/placement/preflight required",
        )
        b.check_payload(b.NEW / "project", b.NEW / "helpers", b.NEW / "record")
        b.need(not any((b.NEW / "authority").iterdir()), "empty authority target")
        files = authority_files(
            a.repo, a.publication, data, a.decision_commit, a.placement_commit, a.preflight
        )
    out.mkdir()
    for name, raw in files.items():
        path = out / "payload" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    if a.stage != "payload":
        (out / "human-place.sh").write_bytes(script(files, a.stage == "placement"))
    else:
        (out / "human-place.preview.sh").write_bytes(
            (b"#!/bin/sh\n# NOT AUTHORIZED: published human approval required.\nexit 1\n")
            + script(files, True)
        )
    (out / "postimages.json").write_bytes(b.encoded({n: b.digest(raw) for n, raw in files.items()}))
    (out / "publication-check.json").write_bytes(b.encoded(view.receipt()))
    print("Prepared only; no root placement, authority installation or execution performed.")


if __name__ == "__main__":
    main()
