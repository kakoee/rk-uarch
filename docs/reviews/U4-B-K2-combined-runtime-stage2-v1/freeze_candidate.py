"""Reconstruct proposal metadata in a NEW PRIVATE file; never edit historical evidence."""

import argparse
import json
import subprocess
from pathlib import Path

import bindings as b
import publication

BASELINE = "cbb0313e13abc0ca99311df323a0c64f4f7886c1"
BASELINE_PATH = "docs/reviews/U4-B-K2-combined-runtime-v1/candidate.json"
BASELINE_HASH = "sha256:932fe281632bac001f0fdb091089cfd5e09d0b141d74569f6d6b5281f06f9ee1"


def build(repo: Path, package: Path) -> bytes:
    raw = subprocess.check_output(
        ["/usr/bin/git", "--no-replace-objects", "show", BASELINE + ":" + BASELINE_PATH],
        cwd=repo,
        env=publication.environment(Path("/nonexistent")),
    )
    b.need(b.digest(raw) == BASELINE_HASH, "exact historical candidate bytes")
    c = json.loads(raw)
    c.update(
        format="uarch-k2-combined-candidate/2",
        decision_id="candidate-04-combined-runtime-v2-first-use",
        policy_hash=b.digest((package / "policy-choices.md").read_bytes()),
        amendment_hash=b.digest((package / "normative-addendum.txt").read_bytes()),
    )
    c["helpers"]["receipt_checks.py"] = b.digest((package / "receipt_checks.py").read_bytes())
    for name in ("bindings.py", "runtime_entry.py"):
        c["helpers"][name] = b.digest((package / name).read_bytes())
    c["tools"] = {
        n: b.digest((package / n).read_bytes())
        for n in (
            "bindings.py",
            "runtime_entry.py",
            "receipt_checks.py",
            "prepare.py",
            "launch.py",
            "publication.py",
            "freeze_candidate.py",
        )
    }
    c["helper_imports"] = {
        n[:-3]: {"path": "/combined/" + n, "sha256": h}
        for n, h in c["helpers"].items()
        if n.endswith(".py")
    }
    for n, prefix in [
        ("entrypoint.py", "campaign"),
        ("deployment.py", "campaign"),
        ("first_use_checks.py", "candidate/docs/reviews/U4-B-K2-construction-audit-v1"),
    ]:
        path = b.OLD / prefix / n
        if prefix == "campaign":
            expected = b.read(b.OLD / "manifests/campaign-files.json")[n]["sha256"]
        else:
            relative = str(path.relative_to(b.OLD / "candidate"))
            expected = b.read(b.OLD / "campaign/candidate-layout.json")["files"][relative][
                "byte_hash"
            ]
        b.need(b.digest(path.read_bytes()) == expected, "unchanged auxiliary helper")
        c["helper_imports"][n[:-3]] = {"path": "/" + prefix + "/" + n, "sha256": expected}
    c["policy_patches"] = {
        n: b.digest((package / n).read_bytes())
        for n in (
            "U0002-cross-reference.unapplied.patch",
            "U0011-runtime-coexistence.unapplied.patch",
        )
    }
    c["additional_runtime_helpers"] = ["runtime_entry.py", "bindings.py", "receipt_checks.py"]
    return b.encoded(c)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    b.need(
        a.output.is_absolute()
        and a.output.is_relative_to("/tmp")
        and a.output.resolve() == a.output,
        "new private output only",
    )
    with a.output.open("xb") as stream:
        stream.write(build(a.repo, Path(__file__).resolve().parent))


if __name__ == "__main__":
    main()
